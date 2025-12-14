"""
main.py

Author: maymeridian
Description: The core orchestration script. Coordinates the workflow between OCR scanning,
             consensus data normalization, and the final renaming/sorting process.
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
        coa = group[-1]
        if coa['type'] == 'COA' and coa.get('desc'):
            descriptions.append(coa['desc'])
            
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
        coa = group[-1]
        if coa['type'] == 'COA' and coa.get('desc') in corrections:
            coa['desc'] = corrections[coa['desc']]

# ==========================================
# FILE OPERATIONS (Updated)
# ==========================================

def _get_show_folder(sku: str) -> str:
    """
    Extracts the 'Show Name' prefix from the SKU for sub-folder sorting.
    Logic: Splits the SKU before the final block of 4+ digits.
    Ex: THE1000332 -> THE100
        EXPANSE7586 -> EXPANSE
    """
    if not sku:
        return "Unknown_Show"
    
    # Regex: Capture everything BEFORE the last sequence of 4+ digits
    match = re.match(r"^(.*?)(?=\d{4,}$)", sku)
    if match and match.group(1):
        return match.group(1).upper()
        
    # Fallback: If regex fails (e.g. short SKU), just return the whole SKU
    return sku

def _get_unique_path(base_path: Path) -> Path:
    """
    Generates a unique filename if the target already exists.
    Ex: File.jpg -> File (1).jpg -> File (2).jpg
    """
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

def process_group(group: List[Dict], output_dir: Path, log_func: Callable[[str], None]) -> List[Path]:
    """
    Renames and moves a group of files into sub-folders.
    Includes duplicate detection.
    """
    coa_data = group[-1]
    
    item_code = coa_data.get('sku')
    item_desc = coa_data.get('desc')

    # 1. Determine Folder & Base Name
    if not item_code:
        log_func(f"⚠️ Could not find Item Code in COA: {coa_data['path'].name}")
        base_name = f"Unknown_{coa_data['path'].stem}"
        sub_folder = "Unknown_Show"
    else:
        base_name = f"{item_code}-{item_desc}" if item_desc else item_code
        sub_folder = _get_show_folder(item_code)

    # 2. Create Show-Specific Sub-folder
    target_dir = output_dir / sub_folder
    # We rely on fm.copy_file or manual mkdir. fm.copy_file handles parents, 
    # but let's be explicit here to ensure the folder structure is clear.
    target_dir.mkdir(parents=True, exist_ok=True)

    log_func(f"📦 Group: {base_name} -> /{sub_folder}")

    successful_moves = []
    
    for i, item in enumerate(group):
        original_path = item['path']
        is_coa = (item['type'] == 'COA')

        if is_coa and config.DISCARD_COA:
            successful_moves.append(original_path)
            continue

        suffix = "COA" if is_coa else str(i + 1)
        
        # Build Initial New Filename
        new_filename = f"{base_name}-{suffix}{original_path.suffix}"
        if config.APPEND_ORIGINAL_NAME:
            new_filename = f"{base_name}-{suffix}_{original_path.stem}{original_path.suffix}"

        # 3. Duplicate Detection (Get Unique Path)
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
    """
    The main execution entry point called by the GUI.
    """
    
    log_func("--- Starting Argus 2.0 ---")
    log_func(f"Selected {len(file_list)} images.")
    
    logs_dir = fm.get_application_path() / "extracted_text"
    if config.SAVE_DEBUG_LOGS:
        logs_dir.mkdir(exist_ok=True)
        fm.clean_directory(logs_dir)
    
    if stop_event.is_set(): return
    log_func("Initializing AI Engine...")
    engine = RapidOCR()
    
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
    for item in analyzed_results:
        if item['type'] == 'COA':
            current_group.append(item)
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(item)
    if current_group:
        groups.append(current_group)

    # --- CONSENSUS PHASE ---
    if stop_event.is_set(): return
    normalize_descriptions(groups, log_func)

    # --- EXECUTION PHASE ---
    log_func(f"\nProcessing {len(groups)} identified groups...")
    progress_func(0.9)
    
    files_processed_count = 0
    
    for group in groups:
        if stop_event.is_set():
            log_func("\n🛑 CANCELLED.")
            return

        if not group: continue
        
        if group[-1]['type'] != 'COA':
            log_func("⚠️ Skipping orphan group (No COA found)")
            continue
        
        processed = process_group(group, output_path, log_func)
        files_processed_count += len(processed)

    progress_func(1.0)
    log_func("================================")
    log_func(f"✅ DONE! Processed {files_processed_count} files.")
    log_func(f"📁 Output: {output_path}")
    log_func("================================")