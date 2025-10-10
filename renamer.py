import os
import re
from matcher import load_ocr_results

def extract_item_code(coa_text):
    """Extract item code from COA text (e.g., 'EXPANSE7586')."""
    # Look for pattern like 'EXPANSE####'
    match = re.search(r'EXPANSE\d+', coa_text)
    if match:
        return match.group(0)
    return None

def extract_item_description(coa_text):
    """Extract item description from COA text."""
    # Look for text between item code and 'was used in'
    match = re.search(r'EXPANSE\d+\s+(.+?)\s+was used in', coa_text, re.IGNORECASE | re.DOTALL)
    if match:
        # Clean up the description: remove extra whitespace, convert to uppercase for consistency
        description = match.group(1).strip()
        description = re.sub(r'\s+', '-', description)  # Replace spaces with hyphens
        description = re.sub(r'[^\w\-]', '', description)  # Remove special characters
        description = description.upper()  # Convert everything to uppercase for consistency
        return description
    return None

def rename_files(photo_pairs, output_dir='/tmp/olmocr_output'):
    """Rename files based on COA titles."""
    ocr_data = load_ocr_results(output_dir)

    for group in photo_pairs:
        if len(group) == 0:
            continue

        # Last file in group is the COA
        coa_file = group[-1]
        coa_text = ocr_data.get(coa_file, '')

        if not coa_text:
            print(f"Warning: No OCR data found for COA {coa_file}")
            continue

        # Extract item code and description
        item_code = extract_item_code(coa_text)
        item_desc = extract_item_description(coa_text)

        if not item_code:
            print(f"Warning: Could not extract item code from {coa_file}")
            continue

        # Build base name
        if item_desc:
            base_name = f"{item_code}-{item_desc}"
        else:
            base_name = item_code

        # Rename each file in the group
        for i, image_file in enumerate(group):
            file_ext = os.path.splitext(image_file)[1]

            if i == len(group) - 1:
                # This is the COA
                new_name = f"{base_name}-coa{file_ext}"
            else:
                # This is a prop photo
                new_name = f"{base_name}-{i + 1}{file_ext}"

            # Get directory
            directory = os.path.dirname(image_file)
            new_path = os.path.join(directory, new_name)

            os.rename(image_file, new_path)
            print(f"Renamed: {image_file} -> {new_path}")
