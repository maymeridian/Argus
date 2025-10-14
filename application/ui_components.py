"""
Reusable UI components for the Argus application.
"""

import streamlit as st
from application.config import (
    DEFAULT_GPU_MEMORY, GPU_MEMORY_MIN, GPU_MEMORY_MAX, GPU_MEMORY_STEP,
    load_settings, save_settings
)

def render_title():
    """Render the application title and description."""
    st.markdown("<h1 style='text-align: left; font-size: 3.5rem;'>Argus 👁️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: leftr; font-weight: bold;'>The All-Seeing Photo Renamer</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: left;'>Upload your prop photos and COA images to automatically rename them based on the COA titles.</p>", unsafe_allow_html=True)

def render_file_uploader(uploader_key):
    """Render the file uploader widget."""
    uploaded_files = st.file_uploader(
        "Upload Images",
        type=['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_{uploader_key}"
    )

    return uploaded_files

def render_process_button(uploaded_files, processing):
    """Render the process and rename button."""
    return st.button(
        "▶ Process and Rename",
        disabled=not uploaded_files or processing,
        use_container_width=True
    )

def render_settings():
    """Render the settings expander with GPU memory slider and COA exclusion option."""
    # Load saved settings
    saved_settings = load_settings()

    with st.expander("⚙️ Settings"):
        gpu_memory = st.slider(
            "GPU Memory Utilization (%)",
            min_value=GPU_MEMORY_MIN,
            max_value=GPU_MEMORY_MAX,
            value=saved_settings['gpu_memory'],
            step=GPU_MEMORY_STEP,
            key="gpu_memory_utilization",
            help="Percentage of GPU memory to use for OCR processing. Lower values use less memory but may be slower."
        )

        exclude_coa = st.checkbox(
            "Exclude COA images from download",
            value=saved_settings['exclude_coa'],
            key="exclude_coa_from_zip",
            help="When enabled, only prop photos will be included in the ZIP download (COA images will be excluded)."
        )

        # Save settings whenever they change
        if gpu_memory != saved_settings['gpu_memory'] or exclude_coa != saved_settings['exclude_coa']:
            save_settings(gpu_memory, exclude_coa)

    return gpu_memory, exclude_coa

def render_instructions():
    """Render the how-to-use instructions."""
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        1. **Upload your images**: Drag and drop all prop photos and their COA images
        2. **Configure settings**: Open the Settings section above to adjust processing options
        3. **Process**: Click the "▶ Process and Rename" button
        4. **Download**: View the renamed files and download them

        **Note**: Make sure the COA image comes after its corresponding prop photos in the file order.
        """)

def create_processing_placeholders():
    """Create placeholders for processing UI elements."""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    output_expander_placeholder = st.container()

    return progress_placeholder, status_placeholder, output_expander_placeholder
