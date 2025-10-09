import streamlit as st
import os
import shutil
import subprocess
from pathlib import Path

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

st.title("👁️ Argus")
st.markdown("**The All-Seeing Photo Renamer**")
st.markdown("Upload your prop photos and COA images to automatically rename them based on the COA titles.")

# Main upload area
st.header("Upload Images")
uploaded_files = st.file_uploader(
    "Drag and drop your images here",
    type=['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG'],
    accept_multiple_files=True
)

# Display uploaded files
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

    with st.expander("View uploaded files"):
        cols = st.columns(4)
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                st.text(file.name)

# Initialize session state for processing
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Process button
if st.button("🚀 Process and Rename", type="primary", disabled=not uploaded_files or st.session_state.processing):
    st.session_state.processing = True

    try:
        # Create log file
        log_file = Path("argus_log.txt")

        # Save uploaded files to images folder
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)

        # Clear existing files if needed
        if st.session_state.get("clear_after", False):
            for f in images_dir.glob("*"):
                f.unlink()

        progress_bar = st.progress(0)
        status_text = st.empty()

        # Save uploaded files
        with st.spinner("Saving uploaded files..."):
            status_text.text("💾 Saving uploaded files...")
            for idx, uploaded_file in enumerate(uploaded_files):
                file_path = images_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                progress_bar.progress((idx + 1) / len(uploaded_files) * 0.3)

        # Backup original files if requested
        if st.session_state.get("keep_originals", False):
            backup_dir = Path("backup")
            backup_dir.mkdir(exist_ok=True)
            status_text.text("💾 Creating backup of original files...")
            for file in images_dir.glob("*"):
                if file.is_file():
                    shutil.copy2(file, backup_dir / file.name)

        # Build Docker image if needed
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
        else:
            # Run Docker container
            status_text.text("👁️ Argus is reading your images...")
            progress_bar.progress(0.5)

            # Create a placeholder for live output
            st.markdown("**Processing Output:**")
            output_container = st.empty()
            output_text = ""

            # Run Docker with streaming output
            process = subprocess.Popen(
                ["docker", "compose", "run", "--remove-orphans", "olmocr"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # Stream output to the UI and log file
            with open(log_file, "w", encoding='utf-8', errors='replace') as log:
                log.write(f"Argus Processing Log - {st.session_state.get('start_time', 'Unknown')}\n")
                log.write("="*80 + "\n\n")

                for line in process.stdout:
                    output_text += line
                    log.write(line)
                    log.flush()
                    output_container.code(output_text, language="shell")

            process.wait()
            result_returncode = process.returncode

            # Log final status
            with open(log_file, "a", encoding='utf-8', errors='replace') as log:
                log.write(f"\n\nProcess completed with return code: {result_returncode}\n")

            progress_bar.progress(1.0)

            if result_returncode == 0:
                status_text.empty()
                st.success("✅ Files processed and renamed successfully!")

                # Show renamed files
                st.header("Renamed Files")
                renamed_files = sorted(list(images_dir.glob("*")))

                cols = st.columns(3)
                for idx, file in enumerate(renamed_files):
                    with cols[idx % 3]:
                        st.image(str(file), caption=file.name, use_container_width=True)

                # Download button for all files
                st.download_button(
                    label="📥 Download All Renamed Files",
                    data="Check the images folder for renamed files",
                    file_name="renamed_files.txt"
                )
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

# Settings
with st.expander("⚙️ Settings"):
    clear_after = st.checkbox("Clear images folder after processing", value=False, key="clear_after")
    keep_originals = st.checkbox("Keep original filenames as backup", value=False, key="keep_originals")

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Upload your images**: Drag and drop all prop photos and their COA images
    2. **Configure settings**: Open the Settings section above to adjust processing options
    3. **Process**: Click the "Process and Rename" button
    4. **Download**: View the renamed files and download them

    **Note**: Make sure the COA image comes after its corresponding prop photos in the file order.
    """)
