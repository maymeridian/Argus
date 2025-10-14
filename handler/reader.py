"""
Contains the methods to get and read image files.
"""

import os
import subprocess
import glob


def get_image_files(directory):
    """Get all image files in the directory."""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    image_files = []

    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(directory, ext)))

    return image_files


def read_images(image_files):
    """Run olmOCR on all images."""
    print(f"Found {len(image_files)} image(s) to process\n")
    print("Running OCR on all images (this may take a while)...\n")

    # Get GPU memory utilization from environment variable (default to 0.80)
    gpu_mem = os.environ.get('GPU_MEMORY_UTILIZATION', '0.80')

    subprocess.run([
        'python', '-m', 'olmocr.pipeline',
        '/tmp/olmocr_output',
        '--gpu-memory-utilization', gpu_mem,
        '--max_model_len', '5048',
        '--pdfs'] + image_files
    )