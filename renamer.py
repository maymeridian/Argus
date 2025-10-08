import argparse
import os
import subprocess
import glob

def process_all_images(directory):
    """Process all images in the directory."""
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(directory, ext)))

    if not image_files:
        print(f"No image files found in {directory}")
        return

    print(f"Found {len(image_files)} image(s) to process\n")

    # Run olmOCR on all images at once
    print("Running OCR on all images (this may take a while)...\n")
    subprocess.run([
        'python', '-m', 'olmocr.pipeline',
        '/tmp/olmocr_output',
        '--markdown',
        '--pdfs'] + image_files
    )

    # Display results for each image
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for image_path in image_files:
        output_file = os.path.join('/tmp/olmocr_output', os.path.splitext(os.path.basename(image_path))[0] + '.md')

        print(f"\n{os.path.basename(image_path)}:")
        print("-" * 70)
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                print(f.read())
        else:
            print("No output found")
        print("-" * 70)

def process_single_image(image_path):
    """Process a single image."""
    print(f"Processing: {image_path}")
    print("Running OCR (this may take a minute)...\n")

    # Run olmOCR via command line
    subprocess.run([
        'python', '-m', 'olmocr.pipeline',
        '/tmp/olmocr_output',
        '--markdown',
        '--pdfs', image_path
    ])

    # Read and display the output
    output_file = os.path.join('/tmp/olmocr_output', os.path.splitext(os.path.basename(image_path))[0] + '.md')

    if os.path.exists(output_file):
        print("\n" + "=" * 50)
        print("OCR Result:")
        print("=" * 50)
        with open(output_file, 'r') as f:
            print(f.read())
        print("=" * 50)
    else:
        print("No markdown output file found. Check /tmp/olmocr_output for results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run OCR on images using olmOCR')
    parser.add_argument('image_path', nargs='?', help='Path to a single image file')
    parser.add_argument('--all', action='store_true', help='Process all images in /data directory')

    args = parser.parse_args()

    if args.all:
        process_all_images('/data')
    elif args.image_path:
        process_single_image(args.image_path)
    else:
        parser.print_help()
