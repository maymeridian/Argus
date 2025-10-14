"""
Configuration and styling for the Argus application.
"""

import streamlit as st
import json
from pathlib import Path

def configure_page():
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="Argus - Photo Renamer",
        page_icon="👁️",
        layout="wide",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

def apply_custom_styling():
    """Apply custom CSS styling to the application."""
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display: none;}

            /* Green process button */
            .stButton > button {
                width: 100%;
                background-color: #00cc66;
                color: white;
            }
            .stButton > button:hover {
                background-color: #00b359;
                color: white;
            }
            .stButton > button:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        </style>
        """, unsafe_allow_html=True)

# Default values
DEFAULT_GPU_MEMORY = 80
GPU_MEMORY_MIN = 10
GPU_MEMORY_MAX = 100
GPU_MEMORY_STEP = 1

# Settings file path
SETTINGS_FILE = Path("argus_settings.json")

def load_settings():
    """Load settings from file, or return defaults if file doesn't exist."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'gpu_memory': DEFAULT_GPU_MEMORY,
        'exclude_coa': True
    }

def save_settings(gpu_memory, exclude_coa):
    """Save settings to file."""
    try:
        settings = {
            'gpu_memory': gpu_memory,
            'exclude_coa': exclude_coa
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass  # Silently fail if we can't save settings
