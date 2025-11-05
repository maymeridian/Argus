"""
Docker and OCR processing logic for the Argus application.
"""

import os
import subprocess
import streamlit as st
from pathlib import Path

def check_docker_image():
    """Check if Docker image exists."""
    check_image = subprocess.run(
        ["docker", "images", "-q", "argus-olmocr"],
        capture_output=True,
        text=True
    )
    return bool(check_image.stdout.strip())

def build_docker_image():
    """Build the Docker image."""
    build_result = subprocess.run(
        ["docker", "compose", "build"],
        capture_output=True,
        text=True
    )
    return build_result

def run_docker_processing(gpu_mem_percent, output_placeholder):
    """Run the Docker container for OCR processing."""
    # Convert GPU memory percentage to decimal
    gpu_mem_decimal = gpu_mem_percent / 100.0

    # Run Docker with streaming output
    process = subprocess.Popen(
        ["docker", "compose", "run", "--rm", "--remove-orphans",
         "-e", f"GPU_MEMORY_UTILIZATION={gpu_mem_decimal}", "olmocr"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1
    )

    return process

def stream_docker_output(process, log_file, output_placeholder):
    """Stream Docker output to UI and log file."""
    output_text = ""
    with open(log_file, "w", encoding='utf-8', errors='replace') as log:
        log.write(f"Argus Processing Log\n")
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
    return_code = process.returncode

    # Log final status
    with open(log_file, "a", encoding='utf-8', errors='replace') as log:
        log.write(f"\n\nProcess completed with return code: {return_code}\n")

    return return_code

def save_uploaded_files(uploaded_files, images_dir, progress_bar, status_text):
    """Save uploaded files to the images directory."""
    with st.spinner("Saving uploaded files..."):
        status_text.text("💾 Saving uploaded files...")
        for idx, uploaded_file in enumerate(uploaded_files):
            file_path = images_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            progress_bar.progress((idx + 1) / len(uploaded_files) * 0.3)
