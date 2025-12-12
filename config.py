"""Configuration settings for Argus 2.0."""
import json
import file_manager as fm
from pathlib import Path

# ==========================================
# DEFAULT SETTINGS
# ==========================================
APPEND_ORIGINAL_NAME = False
DISCARD_COA = False
SAVE_DEBUG_LOGS = True  # NEW: Toggle for .md text files

# Default to "Output" folder next to the app
OUTPUT_FOLDER = str(fm.get_application_path() / "Output")

COA_INDICATORS = [
    'DOCUMENT CERTIFIES', 'PRODUCTION OF', 'WAS USED IN',
    'WWW.PROPABILIA', 'AUTHORIZED', 'MEMORABILIA',
    'CERTIFICATE OF AUTHENTICITY', 'PROPABILIA'
]

# ==========================================
# PERSISTENCE LOGIC
# ==========================================
def get_settings_path():
    return fm.get_application_path() / "settings.json"

def load():
    global APPEND_ORIGINAL_NAME, DISCARD_COA, SAVE_DEBUG_LOGS, COA_INDICATORS, OUTPUT_FOLDER
    
    path = get_settings_path()
    if not path.exists():
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if "APPEND_ORIGINAL_NAME" in data: APPEND_ORIGINAL_NAME = data["APPEND_ORIGINAL_NAME"]
        if "DISCARD_COA" in data: DISCARD_COA = data["DISCARD_COA"]
        if "SAVE_DEBUG_LOGS" in data: SAVE_DEBUG_LOGS = data["SAVE_DEBUG_LOGS"]
        if "COA_INDICATORS" in data: COA_INDICATORS = data["COA_INDICATORS"]
        if "OUTPUT_FOLDER" in data: OUTPUT_FOLDER = data["OUTPUT_FOLDER"]
            
        print(f"✅ Config loaded from {path.name}")
    except Exception as e:
        print(f"⚠️ Failed to load settings: {e}")

def save():
    data = {
        "APPEND_ORIGINAL_NAME": APPEND_ORIGINAL_NAME,
        "DISCARD_COA": DISCARD_COA,
        "SAVE_DEBUG_LOGS": SAVE_DEBUG_LOGS,
        "COA_INDICATORS": COA_INDICATORS,
        "OUTPUT_FOLDER": OUTPUT_FOLDER
    }
    
    try:
        with open(get_settings_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print("✅ Config saved successfully.")
    except Exception as e:
        print(f"⚠️ Failed to save settings: {e}")