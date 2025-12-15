"""
main.py

Author: maymeridian
Description: The core orchestration script. Coordinates the workflow between OCR scanning,
             consensus data normalization, and the final renaming/sorting process.
             Supports Multi-SKU grouping and Anchor-Folder sorting.
"""

import sys
import difflib
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

from rapidocr_onnxruntime import RapidOCR
import config
import file_manager as fm
import text_processor as tp

# ==========================================
# ANALYSIS LOGIC
# ==========================================

def analyze_image(engine: RapidOCR, img_path: Path) -> Optional[Dict[str, Any]]:
    """
    Performs OCR on a single image and extracts metadata immediately.
    """
    try:
        result, _ = engine(str(img_path))
        full_text = ""
        if result:
            full_text = "\n".join([line[1] for line in result if float(line[2]) > 0.6])
        
        is_cert = tp.is_coa(full_text)
        
        item_code, item_desc = None, None
        if is_cert:
            item_code, item_desc = tp.extract_details(full_text)

        return {
            'path': img_path,
            'text': full_text,
            'type': 'COA' if is_cert else 'PROP',
            'sku': item_code,
            'desc': item_desc
        }
    except Exception as e:
        return None

# ==========================================
# CONSENSUS LOGIC
# ==========================================

def normalize_descriptions(groups: List[List[Dict]], log_func: Callable[[str], None]) -> None:
    """
    Applies consensus logic to fix typos in descriptions based on group majority.
    """
    log_func("🧠 Analyzing group consensus...")
    
    descriptions = []
    for group in groups:
        if not group: continue
        for item in group:
            if item['type'] == 'COA' and item.get('desc'):
                descriptions.append(item['desc'])
            
    if not descriptions:
        return

    counts = Counter(descriptions)
    sorted_descs = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    corrections = {}

    for i, candidate in enumerate(sorted_descs):
        for j in range(i):
            popular = sorted_descs[j]
            ratio = difflib.SequenceMatcher(None, candidate, popular).ratio()
            
            if ratio > 0.80:
                corrections[candidate] = popular
                log_func(f"   ✨ Auto-Correcting: '{candidate}' → '{popular}'")
                break
    
    for group in groups:
        if not group: continue
        for item in group:
            if item['type'] == 'COA' and item.get('desc') in corrections:
                item['desc'] = corrections[item['desc']]

# ==========================================
# FILE OPERATIONS
# ==========================================

def _get_group_key(sku: str) -> str:
    """
    Determines the grouping key by stripping the final numeric ID.
    Logic: Splits the string before the last block of 4+ digits.
    Ex: MAGICIANS0305 -> MAGICIANS, THE8000001 -> THE800
    """
    if not sku: return "UNKNOWN"
    
    match = re.match(r"^(.*?)(?=\d{4,}$)", sku)
    if match and match.group(1):
        return match.group(1).upper()
        
    return sku[:4].upper()

def _get_unique_path(base_path: Path) -> Path:
    """Generates a unique filename if the target already exists."""
    if not base_path.exists():
        return base_path

    counter = 1
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

def _merge_skus(coas: List[Dict]) -> str:
    """Merges multiple SKUs into one string for the filename."""
    if not coas: return "UNKNOWN"
    
    base_sku = coas[0].get('sku', 'UNKNOWN')
    if len(coas) == 1:
        return base_sku

    match = re.match(r"^(.*?)(?=\d{4,}$)", base_sku)
    prefix = match.group(1) if match else ""

    merged = base_sku
    for coa in coas[1:]:
        next_sku = coa.get('sku', '')
        if not next_sku: continue
        
        if prefix and next_sku.startswith(prefix):
            suffix = next_sku[len(prefix):]
            merged += f"-{suffix}"
        else:
            merged += f"-{next_sku}"
            
    return merged

def process_group(group: List[Dict], output_dir: Path, 
                  folder_map: Dict[str, str], log_func: Callable[[str], None]) -> List[Path]:
    """
    Renames and moves a group.
    Uses 'folder_map' to anchor all items of the same Show to the first folder created.
    """
    coas = [item for item in group if item['type'] == 'COA']
    
    if not coas:
        primary_sku = "UNKNOWN"
        item_code_filename = "UNKNOWN"
        item_desc = f"Orphan_Prop_{group[0]['path'].stem}"
    else:
        primary_coa = coas[0]
        primary_sku = primary_coa.get('sku', 'UNKNOWN')
        item_code_filename = _merge_skus(coas)
        item_desc = primary_coa.get('desc', 'Unknown Item')

    # 1. Determine Folder Name (Anchor Strategy)
    group_key = _get_group_key(primary_sku)
    
    if group_key in folder_map:
        sub_folder = folder_map[group_key]
    else:
        sub_folder = primary_sku
        folder_map[group_key] = sub_folder

    # 2. Create/Target Directory
    target_dir = output_dir / sub_folder
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{item_code_filename}-{item_desc}"
    log_func(f"📦 Group: {base_name} -> /{sub_folder}")

    successful_moves = []
    
    for i, item in enumerate(group):
        original_path = item['path']
        is_coa = (item['type'] == 'COA')

        if is_coa and config.DISCARD_COA:
            successful_moves.append(original_path)
            continue

        suffix = "COA" if is_coa else str(i + 1)
        
        new_filename = f"{base_name}-{suffix}{original_path.suffix}"
        if config.APPEND_ORIGINAL_NAME:
            new_filename = f"{base_name}-{suffix}_{original_path.stem}{original_path.suffix}"

        final_path = _get_unique_path(target_dir / new_filename)

        if fm.copy_file(original_path, final_path):
            successful_moves.append(original_path)

    return successful_moves

# ==========================================
# MAIN ORCHESTRATOR
# ==========================================

def run_sorter(file_list: List[str], output_path: Path, 
               log_func: Callable[[str], None], 
               progress_func: Callable[[float], None], 
               stop_event: Any) -> None:
    
    log_func("--- Starting Argus 2.0 ---")
    log_func(f"Selected {len(file_list)} images.")
    
    logs_dir = fm.get_application_path() / "extracted_text"
    if config.SAVE_DEBUG_LOGS:
        logs_dir.mkdir(exist_ok=True)
        fm.clean_directory(logs_dir)
    
    if stop_event.is_set(): return
    log_func("Initializing AI Engine...")
    
    # --- UPDATED GPU LOGIC ---
    if config.USE_GPU:
        # User wants GPU -> Try CUDA, fallback if it fails
        try:
            engine = RapidOCR(det_use_cuda=True, cls_use_cuda=True, rec_use_cuda=True)
            log_func("🚀 GPU Acceleration Enabled (CUDA)")
        except Exception:
            log_func("⚠️ GPU request failed. Falling back to CPU.")
            engine = RapidOCR()
    else:
        # User disabled GPU -> Force CPU
        engine = RapidOCR(det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False)
        log_func("💻 CPU Mode Active (User Setting)")
    # -------------------------
    
    # --- SCANNING PHASE ---
    analyzed_results = []
    total = len(file_list)
    sorted_files = sorted([Path(f) for f in file_list], key=lambda p: p.name.lower())

    for idx, img_path in enumerate(sorted_files):
        if stop_event.is_set():
            log_func("\n🛑 OPERATION CANCELLED.")
            return

        progress = (idx / total) * 0.8
        progress_func(progress)
        
        log_func(f"Reading: {img_path.name}")
        res = analyze_image(engine, img_path)
        
        if res:
            if config.SAVE_DEBUG_LOGS:
                fm.save_text_log(logs_dir / f"{img_path.stem}.md", res['text'])
            analyzed_results.append(res)

    # --- GROUPING PHASE ---
    groups = []
    current_group = []
    
    for i, item in enumerate(analyzed_results):
        current_group.append(item)
        if item['type'] == 'COA':
            next_is_coa = False
            if i + 1 < len(analyzed_results):
                if analyzed_results[i+1]['type'] == 'COA':
                    next_is_coa = True
            
            if not next_is_coa:
                groups.append(current_group)
                current_group = []
    
    if current_group:
        groups.append(current_group)

    # --- CONSENSUS PHASE ---
    if stop_event.is_set(): return
    normalize_descriptions(groups, log_func)

    # --- EXECUTION PHASE ---
    log_func(f"\nProcessing {len(groups)} identified groups...")
    progress_func(0.9)
    
    folder_map = {}
    files_processed_count = 0
    
    for group in groups:
        if stop_event.is_set():
            log_func("\n🛑 CANCELLED.")
            return

        if not group: continue
        
        has_coa = any(item['type'] == 'COA' for item in group)
        if not has_coa:
            log_func("⚠️ Skipping orphan group (No COA found)")
            continue
        
        processed = process_group(group, output_path, folder_map, log_func)
        files_processed_count += len(processed)

    progress_func(1.0)
    log_func("================================")
    log_func(f"✅ DONE! Processed {files_processed_count} files.")
    log_func(f"📁 Output: {output_path}")
    log_func("================================")