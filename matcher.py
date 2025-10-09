import os
import json
import glob

def load_ocr_results(output_dir='/tmp/olmocr_output'):
    """Load OCR results from all JSONL files."""
    jsonl_files = glob.glob(os.path.join(output_dir, 'results', '*.jsonl'))
    if not jsonl_files:
        return {}

    ocr_data = {}
    for jsonl_file in jsonl_files:
        with open(jsonl_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                source_file = entry['metadata']['Source-File']
                ocr_data[source_file] = entry['text']
    return ocr_data

def is_coa(text):
    """Check if OCR text contains COA indicators."""
    if not text:
        return False

    text_upper = text.upper()
    coa_indicators = [
        'DOCUMENT CERTIFIES',
        'PRODUCTION OF',
        'WAS USED IN',
        'WWW.PROPABILIA',
        'AUTHORIZED',
        'MEMORABILIA'
    ]

    # Count how many indicators are found
    matches = sum(1 for indicator in coa_indicators if indicator in text_upper)

    # If 2 or more indicators found, it's likely a COA
    return matches >= 2

def match_photos(image_files, output_dir='/tmp/olmocr_output'):
    """
    Pair prop images with their COAs.
    Returns a list of tuples: [(prop1, prop2, ..., coa), (prop3, prop4, ..., coa), ...]
    """
    # Load OCR results
    ocr_data = load_ocr_results(output_dir)

    paired_groups = []
    current_group = []

    for image_file in image_files:
        # Get OCR text for this image
        ocr_text = ocr_data.get(image_file, '')

        if is_coa(ocr_text):
            # This is a COA, add it to current group and save the group
            current_group.append(image_file)
            paired_groups.append(tuple(current_group))
            current_group = []
        else:
            # This is a prop photo, add to current group
            current_group.append(image_file)

    # If there are remaining prop photos without a COA, add them as a group
    if current_group:
        paired_groups.append(tuple(current_group))

    return paired_groups
