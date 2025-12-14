"""
file_manager.py

Author: maymeridian
Description: Utility module for file system operations. Handles path resolution,
             directory management, safe file copying, and debug logging.
"""

import sys
import shutil
from pathlib import Path
from typing import List

def get_application_path() -> Path:
    """
    Determines the base application path.
    
    Returns:
        Path: Parent directory of the executable (if frozen) or the script (if running from source).
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent

    return Path(__file__).parent

def clean_directory(folder: Path) -> None:
    """
    Removes all contents (files and subdirectories) within a specified folder.
    """
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

def save_text_log(path: Path, text: str) -> None:
    """
    Writes text content to a markdown file, creating parent directories if needed.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        content = f"# File: {path.stem}\n\n"
        content += text if text else "(No text detected)"
        
        path.write_text(content, encoding='utf-8')
    except Exception as e:
        print(f"⚠️ Failed to save log: {e}")

def copy_file(src: Path, dest: Path) -> bool:
    """
    Copies a file from source to destination, preserving metadata.
    
    Returns:
        bool: True if copy succeeded, False otherwise.
    """
    try:
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        print(f"❌ Failed to copy {src.name}: {e}")
        return False

def delete_files(file_list: List[Path]) -> int:
    """
    Deletes a list of files from the filesystem.
    
    Returns:
        int: Count of successfully deleted files.
    """
    count = 0
    for path in file_list:
        try:
            if path.exists():
                path.unlink()
                count += 1
        except Exception as e:
            print(f"⚠️ Could not delete {path.name}: {e}")
    return count