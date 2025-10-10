"""
File handling operations including ZIP creation and cleanup.
"""

import json
import time
import gc
import streamlit as st
from pathlib import Path
from io import BytesIO
import zipfile

def create_download_zip(images_dir, exclude_coa):
    """Create a ZIP file of renamed images, optionally excluding COA files."""
    renamed_files = sorted(list(images_dir.glob("*")))

    # Load the list of COA files from the output directory
    coa_files = []
    coa_list_file = Path("output") / "coa_files.json"
    if coa_list_file.exists():
        try:
            with open(coa_list_file, 'r') as f:
                coa_files = json.load(f)
        except Exception as e:
            st.warning(f"Could not load COA list: {e}")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in renamed_files:
            if file.is_file():
                # Skip COA files if setting is enabled
                if exclude_coa and file.name in coa_files:
                    continue
                zip_file.write(file, arcname=file.name)

    zip_buffer.seek(0)
    return zip_buffer

def cleanup_folders(images_dir):
    """Clean up images and output folders after download."""
    # Force garbage collection to release any file handles
    gc.collect()
    time.sleep(1)

    cleanup_errors = []
    deleted_count = 0

    # Clear the images folder
    if images_dir.exists():
        try:
            files_to_delete = list(images_dir.glob("*"))
            for file in files_to_delete:
                if file.is_file():
                    for attempt in range(5):
                        try:
                            file.unlink(missing_ok=True)
                            deleted_count += 1
                            break
                        except PermissionError:
                            if attempt < 4:
                                gc.collect()
                                time.sleep(0.3)
                            else:
                                cleanup_errors.append(f"{file.name}: Permission denied")
                        except Exception as e:
                            cleanup_errors.append(f"{file.name}: {e}")
                            break
        except Exception as e:
            cleanup_errors.append(f"Images folder error: {e}")

    # Clear the output folder
    output_dir = Path("output")
    if output_dir.exists():
        try:
            files_to_delete = list(output_dir.rglob("*"))
            for file in reversed(files_to_delete):  # Delete files bottom-up
                if file.is_file():
                    for attempt in range(5):
                        try:
                            file.unlink(missing_ok=True)
                            deleted_count += 1
                            break
                        except PermissionError:
                            if attempt < 4:
                                gc.collect()
                                time.sleep(0.3)
                            else:
                                cleanup_errors.append(f"{file.name}: Permission denied")
                        except Exception as e:
                            cleanup_errors.append(f"{file.name}: {e}")
                            break
        except Exception as e:
            cleanup_errors.append(f"Output folder error: {e}")

    return deleted_count, cleanup_errors
