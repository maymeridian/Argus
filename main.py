"""
Main entry point that handles both Docker OCR processing and Streamlit app.
- When run inside Docker container: Performs OCR pipeline
- When run with Streamlit: Launches web application
"""

import os
import sys

# Check if running inside Docker container
if os.path.exists('/data') and 'streamlit' not in sys.argv[0].lower():
    # Running inside Docker - execute OCR pipeline
    from reader import get_image_files, read_images
    from matcher import match_photos
    from renamer import rename_files

    if __name__ == "__main__":
        directory = '/data'

        # Find all image files
        image_files = get_image_files(directory)

        if not image_files:
            print(f"No image files found in {directory}")
            exit(1)

        # Run OCR on all images
        read_images(image_files)

        # Match prop photos with their COAs
        photo_pairs = match_photos(image_files)

        # Rename files based on COA titles
        rename_files(photo_pairs)
else:
    # Running locally with Streamlit - launch web app
    from application.app import main

    if __name__ == "__main__":
        main()
