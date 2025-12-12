"""Handles file system operations."""
import os
import shutil
from pathlib import Path

def get_application_path():
    """Returns the base path whether running as script or frozen exe."""
    import sys
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def clean_directory(folder):
    """Wipes contents of specified directory."""
    if not folder.exists():
        return
    for item in folder.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"⚠️ Failed to clean {item.name}: {e}")

def save_text_log(path, text):
    """Saves OCR text to a markdown file."""
    try:
        # Ensure parent exists (in case user deleted 'extracted_text' manually)
        path.parent.mkdir(exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# File: {path.stem}\n\n")
            f.write(text if text else "(No text detected)")
    except Exception as e:
        print(f"⚠️ Failed to save log: {e}")

def copy_file(src, dest):
    """Copies a file and returns True on success."""
    try:
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        print(f"❌ Failed to copy {src.name}: {e}")
        return False

def delete_files(file_list):
    """Deletes a list of files."""
    count = 0
    for path in file_list:
        try:
            os.remove(path)
            count += 1
        except Exception as e:
            print(f"⚠️ Could not delete {path.name}: {e}")
    return count