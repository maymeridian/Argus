import streamlit as st
import os
import shutil
import subprocess
from pathlib import Path
import zipfile
from io import BytesIO

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

# Hide deploy button and streamlit branding
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>👁️ Argus 👁️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold;'>The All-Seeing Photo Renamer</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload your prop photos and COA images to automatically rename them based on the COA titles.</p>", unsafe_allow_html=True)

# Initialize uploader key in session state
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# Main upload area
uploaded_files = st.file_uploader(
    "Upload Images",
    type=['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG'],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)

# Display uploaded files
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

# Initialize session state for processing
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Process button - styled to match expanders and use play icon
st.markdown("""
    <style>
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

if st.button("▶ Process and Rename", disabled=not uploaded_files or st.session_state.processing, use_container_width=True):
    if not st.session_state.processing:  # Extra safety check
        st.session_state.start_processing = True
        st.session_state.processing = True  # Immediately set to prevent double-clicks
        st.rerun()  # Force immediate rerun to disable button

# Create placeholders for processing UI elements (below button, above settings)
progress_placeholder = st.empty()
status_placeholder = st.empty()
output_expander_placeholder = st.container()

# Settings
with st.expander("⚙️ Settings"):
    gpu_memory = st.slider(
        "GPU Memory Utilization (%)",
        min_value=10,
        max_value=100,
        value=80,
        step=5,
        key="gpu_memory_utilization",
        help="Percentage of GPU memory to use for OCR processing. Lower values use less memory but may be slower."
    )

    exclude_coa = st.checkbox(
        "Exclude COA images from download",
        value=True,
        key="exclude_coa_from_zip",
        help="When enabled, only prop photos will be included in the ZIP download (COA images will be excluded)."
    )

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Upload your images**: Drag and drop all prop photos and their COA images
    2. **Configure settings**: Open the Settings section above to adjust processing options
    3. **Process**: Click the "▶ Process and Rename" button
    4. **Download**: View the renamed files and download them

    **Note**: Make sure the COA image comes after its corresponding prop photos in the file order.
    """)

# Process button logic
if st.session_state.get('start_processing', False):
    st.session_state.start_processing = False

    try:
        # Create log file
        log_file = Path("argus_log.txt")

        # Save uploaded files to images folder
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)

        # Use the placeholders created earlier
        progress_bar = progress_placeholder.progress(0)
        status_text = status_placeholder.empty()

        # Save uploaded files
        with st.spinner("Saving uploaded files..."):
            status_text.text("💾 Saving uploaded files...")
            for idx, uploaded_file in enumerate(uploaded_files):
                file_path = images_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                progress_bar.progress((idx + 1) / len(uploaded_files) * 0.3)

        # Check if Docker image exists, build if needed
        check_image = subprocess.run(
            ["docker", "images", "-q", "prop-renamer-olmocr"],
            capture_output=True,
            text=True
        )

        if not check_image.stdout.strip():
            # Image doesn't exist, build it
            with st.spinner("Building Docker image (this may take a while on first run)..."):
                status_text.text("🔨 Building Docker image...")
                build_result = subprocess.run(
                    ["docker", "compose", "build"],
                    capture_output=True,
                    text=True
                )

            if build_result.returncode != 0:
                progress_bar.progress(0)
                status_text.empty()
                st.error("❌ Error building Docker image. Check the logs below:")
                st.code(build_result.stderr)
                st.session_state.processing = False
                st.stop()

        # Run Docker container
        status_text.text("👁️ Argus is reading your images...")
        progress_bar.progress(0.5)

        # Create an expander for the processing output in the placeholder container
        with output_expander_placeholder:
            with st.expander("📋 Console", expanded=False):
                output_placeholder = st.empty()

        # Run Docker with streaming output
        # Note: --rm removes container after exit, --remove-orphans cleans up old containers
        # Get GPU memory setting and convert percentage to decimal
        gpu_mem_percent = st.session_state.get('gpu_memory_utilization', 80)
        gpu_mem_decimal = gpu_mem_percent / 100.0

        # Set up environment variables for Docker
        docker_env = os.environ.copy()
        docker_env['GPU_MEMORY_UTILIZATION'] = str(gpu_mem_decimal)

        process = subprocess.Popen(
            ["docker", "compose", "run", "--rm", "--remove-orphans",
             "-e", f"GPU_MEMORY_UTILIZATION={gpu_mem_decimal}", "olmocr"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=docker_env
        )

        # Stream output to the UI and log file
        output_text = ""
        with open(log_file, "w", encoding='utf-8', errors='replace') as log:
            log.write(f"Argus Processing Log - {st.session_state.get('start_time', 'Unknown')}\n")
            log.write("="*80 + "\n\n")

            for line in process.stdout:
                output_text += line
                log.write(line)
                log.flush()
                # Display with fixed height using HTML and CSS
                output_placeholder.markdown(
                    f"""
                    <div style="height: 400px; overflow-y: auto; background-color: #262730; padding: 1rem; border-radius: 0.5rem; font-family: monospace; font-size: 0.875rem;">
                        <pre style="margin: 0; color: #fafafa; white-space: pre-wrap;">{output_text}</pre>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        process.wait()
        result_returncode = process.returncode

        # Log final status
        with open(log_file, "a", encoding='utf-8', errors='replace') as log:
            log.write(f"\n\nProcess completed with return code: {result_returncode}\n")

        progress_bar.progress(1.0)

        if result_returncode == 0:
            status_text.empty()
            st.success("✅ Files processed and renamed successfully!")

            # Create zip file of renamed images (optionally excluding COA files)
            renamed_files = sorted(list(images_dir.glob("*")))
            exclude_coa = st.session_state.get('exclude_coa_from_zip', True)

            # Load the list of COA files from the output directory
            coa_files = []
            coa_list_file = Path("output") / "coa_files.json"
            if coa_list_file.exists():
                try:
                    import json
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

            # Download button with callback to clear files after download
            if st.download_button(
                label="📥 Download All Renamed Files (ZIP)",
                data=zip_buffer,
                file_name="renamed_images.zip",
                mime="application/zip",
                on_click=lambda: st.session_state.update({'clear_and_reset': True})
            ):
                pass  # Download initiated

            # Clear files only after download button is clicked
            if st.session_state.get('clear_and_reset', False):
                import time

                # Wait a moment for any file handles to be released
                time.sleep(0.5)

                cleanup_errors = []

                # Clear the images folder
                if images_dir.exists():
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            for file in images_dir.glob("*"):
                                if file.is_file():
                                    try:
                                        file.unlink()
                                    except Exception as e:
                                        cleanup_errors.append(f"Failed to delete {file.name}: {e}")
                            break  # Success, exit retry loop
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(0.5)  # Wait before retry
                            else:
                                cleanup_errors.append(f"Images folder cleanup failed: {e}")

                # Clear the output folder
                output_dir = Path("output")
                if output_dir.exists():
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            for file in output_dir.rglob("*"):
                                if file.is_file():
                                    try:
                                        file.unlink()
                                    except Exception as e:
                                        cleanup_errors.append(f"Failed to delete {file.name}: {e}")
                            break  # Success, exit retry loop
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(0.5)  # Wait before retry
                            else:
                                cleanup_errors.append(f"Output folder cleanup failed: {e}")

                # Reset states
                st.session_state.uploader_key += 1
                st.session_state.clear_and_reset = False

                if cleanup_errors:
                    st.warning(f"⚠️ Some files could not be deleted:\n" + "\n".join(cleanup_errors[:3]))
                else:
                    st.success("✅ Files downloaded and cleared. Ready for next batch!")

                # Wait a moment then rerun to reset the UI
                time.sleep(1)
                st.rerun()
        else:
            status_text.empty()
            st.error("❌ Error processing files. Check the output above for details.")
    except Exception as e:
        # Log any unexpected errors
        st.error(f"❌ Unexpected error: {str(e)}")
        try:
            with open(log_file, "a", encoding='utf-8', errors='replace') as log:
                log.write(f"\n\nERROR: {str(e)}\n")
                import traceback
                log.write(traceback.format_exc())
        except:
            pass
        st.info("💾 Error details saved to argus_log.txt")
    finally:
        # Always reset processing state
        st.session_state.processing = False
