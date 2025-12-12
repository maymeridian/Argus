import sys
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
import config
import file_manager as fm
import text_processor as tp

def analyze_image(engine, img_path):
    """Runs OCR on a single image."""
    try:
        result, _ = engine(str(img_path))
        full_text = "\n".join([line[1] for line in result if float(line[2]) > 0.6]) if result else ""
        is_cert = tp.is_coa(full_text)
        return {'path': Path(img_path), 'text': full_text, 'type': 'COA' if is_cert else 'PROP'}
    except Exception as e:
        return None

def process_group(group, output_dir, log_func):
    """Renames and moves a group of files."""
    coa_data = group[-1]
    item_code, item_desc = tp.extract_details(coa_data['text'])

    if not item_code:
        log_func(f"⚠️ Could not find Item Code in COA: {coa_data['path'].name}")
        base_name = f"Unknown_{coa_data['path'].stem}"
    else:
        base_name = f"{item_code}-{item_desc}" if item_desc else item_code

    log_func(f"📦 Group: {base_name}")

    successful_moves = []
    
    for i, item in enumerate(group):
        original_path = item['path']
        is_coa = (item['type'] == 'COA')

        if is_coa and config.DISCARD_COA:
            successful_moves.append(original_path)
            continue

        suffix = "COA" if is_coa else str(i + 1)
        
        new_name = f"{base_name}-{suffix}{original_path.suffix}"
        if config.APPEND_ORIGINAL_NAME:
            new_name = f"{base_name}-{suffix}_{original_path.stem}{original_path.suffix}"

        if fm.copy_file(original_path, output_dir / new_name):
            successful_moves.append(original_path)

    return successful_moves

def run_sorter(file_list, output_path, log_func, progress_func, stop_event):
    """Main logic called by GUI."""
    
    log_func("--- Starting Argus 2.0 ---")
    log_func(f"Selected {len(file_list)} images.")
    
    # 0. Setup Logs (Optional)
    logs_dir = fm.get_application_path() / "extracted_text"
    if config.SAVE_DEBUG_LOGS:
        logs_dir.mkdir(exist_ok=True)
        fm.clean_directory(logs_dir)
    
    # 1. OCR Init
    if stop_event.is_set(): return
    log_func("Initializing AI Engine...")
    engine = RapidOCR()
    
    # 2. Analyze Loop
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
            # SAVE LOG IF ENABLED
            if config.SAVE_DEBUG_LOGS:
                fm.save_text_log(logs_dir / f"{img_path.stem}.md", res['text'])
            
            analyzed_results.append(res)

    # 3. Grouping
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

    # 4. Processing
    log_func(f"\nProcessing {len(groups)} identified groups...")
    progress_func(0.9)
    
    # Optional: Clean output folder if desired, or just overwrite
    # fm.clean_directory(output_path) 
    
    files_to_delete = []
    for group in groups:
        if stop_event.is_set():
            log_func("\n🛑 CANCELLED.")
            return

        if not group: continue
        if group[-1]['type'] != 'COA':
            log_func("⚠️ Skipping orphan group (No COA found)")
            continue
        
        processed = process_group(group, output_path, log_func)
        files_to_delete.extend(processed)

    # 5. Cleanup
    progress_func(1.0)
    log_func("================================")
    log_func(f"✅ DONE! Processed {len(files_to_delete)} files.")
    log_func(f"📁 Output: {output_path}")
    log_func("================================")