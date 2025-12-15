"""
config.py

Author: maymeridian
Description: Manages global configuration settings, persistence logic for user preferences,
             and detection lists (Strong/Weak indicators, Uppercase exceptions) for Argus.
"""

import json
import file_manager as fm
from pathlib import Path

# ==========================================
# DEFAULT SETTINGS
# ==========================================
APPEND_ORIGINAL_NAME = False
DISCARD_COA = False
SAVE_DEBUG_LOGS = True 
USE_GPU = True  # <--- NEW: Default to using GPU

# Default to "Output" folder next to the app
OUTPUT_FOLDER = str(fm.get_application_path() / "Output")

# NEW: Split indicators for smarter detection
STRONG_INDICATORS = [
    'CERTIFICATE OF AUTHENTICITY', 
    'THIS DOCUMENT CERTIFIES', 
    'WAS USED IN THE PRODUCTION',
    'PRODUCTION OF THE ABOVE'
]

WEAK_INDICATORS = [
    'PROPABILIA', 
    'MEMORABILIA', 
    'AUTHORIZED SIGNATURE', 
    'MOVIE & TV',
    'OFFICIAL PROP'
]

# NEW: Acronyms that should always be fully capitalized
# (Prevents them from becoming "Gcpd" or "Aka" via Title Case)
FORCE_UPPERCASE = [
    'GCPD', 'CIA', 'FBI', 'AKA', 'USA', 'UN', 'SSD', 'DHD', 'NASA'
]

# ==========================================
# PERSISTENCE LOGIC
# ==========================================
def get_settings_path():
    return fm.get_application_path() / "settings.json"

def load():
    global APPEND_ORIGINAL_NAME, DISCARD_COA, SAVE_DEBUG_LOGS, USE_GPU, OUTPUT_FOLDER
    global STRONG_INDICATORS, WEAK_INDICATORS, FORCE_UPPERCASE
    
    path = get_settings_path()
    if not path.exists():
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if "APPEND_ORIGINAL_NAME" in data: APPEND_ORIGINAL_NAME = data["APPEND_ORIGINAL_NAME"]
        if "DISCARD_COA" in data: DISCARD_COA = data["DISCARD_COA"]
        if "SAVE_DEBUG_LOGS" in data: SAVE_DEBUG_LOGS = data["SAVE_DEBUG_LOGS"]
        if "USE_GPU" in data: USE_GPU = data["USE_GPU"]  # <--- Load GPU setting
        if "OUTPUT_FOLDER" in data: OUTPUT_FOLDER = data["OUTPUT_FOLDER"]
        
        # Load lists
        if "STRONG_INDICATORS" in data: STRONG_INDICATORS = data["STRONG_INDICATORS"]
        if "WEAK_INDICATORS" in data: WEAK_INDICATORS = data["WEAK_INDICATORS"]
        if "FORCE_UPPERCASE" in data: FORCE_UPPERCASE = data["FORCE_UPPERCASE"]
            
        print(f"✅ Config loaded from {path.name}")
    except Exception as e:
        print(f"⚠️ Failed to load settings: {e}")

def save():
    data = {
        "APPEND_ORIGINAL_NAME": APPEND_ORIGINAL_NAME,
        "DISCARD_COA": DISCARD_COA,
        "SAVE_DEBUG_LOGS": SAVE_DEBUG_LOGS,
        "USE_GPU": USE_GPU,  # <--- Save GPU setting
        "OUTPUT_FOLDER": OUTPUT_FOLDER,
        "STRONG_INDICATORS": STRONG_INDICATORS,
        "WEAK_INDICATORS": WEAK_INDICATORS,
        "FORCE_UPPERCASE": FORCE_UPPERCASE
    }
    
    try:
        with open(get_settings_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print("✅ Config saved successfully.")
    except Exception as e:
        print(f"⚠️ Failed to save settings: {e}")