"""
Main Streamlit application entry point for Argus.
"""

import time
import streamlit as st
from pathlib import Path

from application.config import configure_page, apply_custom_styling
from application.ui_components import (
    render_title,
    render_file_uploader,
    render_process_button,
    render_settings,
    render_instructions,
    create_processing_placeholders
)
from application.processing import (
    check_docker_image,
    build_docker_image,
    run_docker_processing,
    stream_docker_output,
    save_uploaded_files
)
from application.file_operations import create_download_zip, cleanup_folders


def initialize_session_state():
    """Initialize session state variables."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    if 'initial_cleanup_done' not in st.session_state:
        st.session_state.initial_cleanup_done = False


def main():
    """Main application logic."""
    # Configure page
    configure_page()
    apply_custom_styling()

    # Initialize session state
    initialize_session_state()

    # Perform initial cleanup on program launch (only once per session)
    if not st.session_state.initial_cleanup_done:
        images_dir = Path("images")
        output_dir = Path("output")

        # Only cleanup if folders exist and contain files
        if (images_dir.exists() and any(images_dir.iterdir())) or \
           (output_dir.exists() and any(output_dir.iterdir())):
            cleanup_folders(images_dir)

        st.session_state.initial_cleanup_done = True

    # Handle cleanup after download (must be at top level to catch button clicks)
    if st.session_state.get('clear_and_reset', False):
        deleted_count, cleanup_errors = cleanup_folders(Path("images"))
        st.session_state.uploader_key += 1
        st.session_state.clear_and_reset = False

        if cleanup_errors:
            st.warning(f"⚠️ Deleted {deleted_count} files. Failed to delete {len(cleanup_errors)} files:\n" + "\n".join(cleanup_errors[:5]))
        else:
            st.success(f"✅ Files downloaded and cleared ({deleted_count} files deleted). Ready for next batch!")

        time.sleep(1)
        st.rerun()

    # Render UI components
    render_title()

    uploaded_files = render_file_uploader(st.session_state.uploader_key)

    # Process button
    if render_process_button(uploaded_files, st.session_state.processing):
        if not st.session_state.processing:  # Extra safety check
            st.session_state.start_processing = True
            st.session_state.processing = True  # Immediately set to prevent double-clicks
            st.rerun()  # Force immediate rerun to disable button

    # Create placeholders for processing UI elements
    progress_placeholder, status_placeholder, output_expander_placeholder = create_processing_placeholders()

    # Settings
    gpu_memory, exclude_coa = render_settings()

    # Instructions
    render_instructions()

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
            save_uploaded_files(uploaded_files, images_dir, progress_bar, status_text)

            # Check if Docker image exists, build if needed
            if not check_docker_image():
                # Image doesn't exist, build it
                with st.spinner("Building Docker image (this may take a while on first run)..."):
                    status_text.text("🔨 Building Docker image...")
                    build_result = build_docker_image()

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

            # Run Docker processing
            process = run_docker_processing(gpu_memory, output_placeholder)
            result_returncode = stream_docker_output(process, log_file, output_placeholder)

            progress_bar.progress(1.0)

            if result_returncode == 0:
                status_text.empty()
                st.success("✅ Files processed and renamed successfully!")

                # Create zip file
                zip_buffer = create_download_zip(images_dir, exclude_coa)

                # Download button with callback to clear files after download
                st.download_button(
                    label="📥 Download All Renamed Files (ZIP)",
                    data=zip_buffer,
                    file_name="renamed_images.zip",
                    mime="application/zip",
                    on_click=lambda: st.session_state.update({'clear_and_reset': True})
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


if __name__ == "__main__":
    main()
