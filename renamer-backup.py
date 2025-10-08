import os
import re
import easyocr
from PIL import Image
import numpy as np

print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=True)
print("Ready!\n")

def list_image_files(directory):
    """Get all image files in the directory."""
    files = os.listdir(directory)
    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    image_files.sort()
    return image_files

def is_coa(image_path):
    """Check if an image is a COA by looking for common phrases."""
    result = reader.readtext(image_path, detail=0)
    text = ' '.join(result).upper()
    
    coa_indicators = [
        'DOCUMENT',
        'CERTIFIES',
        'WAS USED IN',
        'PRODUCTION OF',
        'THE EXPANSE',
        'MOVIE',
        'MEMORABILIA',
        'AUTHORIZED',
        'WWW.PROPABILIA'
    ]
    
    matches = sum(1 for indicator in coa_indicators if indicator in text)
    return matches >= 2

def clean_ocr_text(text):
    """Fix common OCR errors."""
    # Fix dollar signs that should be S
    text = text.replace('$', 'S')
    
    # Fix episode patterns like S01E06, S03E01, etc.
    # Pattern: S followed by digits/letters, then E, then digits/letters
    def fix_episode(match):
        episode = match.group(0)
        # Replace O with 0, I/L with 1, Z with 2
        episode = episode.replace('O', '0')
        episode = episode.replace('I', '1')
        episode = episode.replace('L', '1')
        episode = episode.replace('Z', '2')
        return episode
    
    text = re.sub(r'S\d*[OIL0-9]+E\d*[OIL0-9]+', fix_episode, text, flags=re.IGNORECASE)
    
    # Fix product codes that got split (like "EXPANSE354 0" -> "EXPANSE3540")
    # Pattern: Letters followed by 3+ digits with optional spaces
    def fix_code_spaces(match):
        code = match.group(0)
        # Remove spaces from the code
        return code.replace(' ', '')
    
    text = re.sub(r'[A-Z&]+\d[\d\s]{2,}', fix_code_spaces, text)
    
    return text

def fuzzy_find_code(text, code):
    """Find code in text, tolerating OCR errors like 1/l, 0/O, 5/S."""
    pattern = code
    pattern = pattern.replace('0', '[0O]')
    pattern = pattern.replace('1', '[1IL]')
    pattern = pattern.replace('5', '[5S]')
    pattern = pattern.replace('8', '[8B]')
    
    match = re.search(pattern, text, re.IGNORECASE)
    return match

def extract_title_with_crop(image_path):
    """Extract title by cropping around the product code line."""
    result = reader.readtext(image_path, detail=1)
    
    product_code = None
    code_bbox = None
    
    for (bbox, text, prob) in result:
        text_upper = text.upper()
        match = re.search(r'[A-Z&]+[O0]?\d{3,4}', text_upper)
        if match:
            code_text = match.group(0)
            product_code = re.sub(r'([A-Z&]+)O(\d)', r'\g<1>0\2', code_text)
            code_bbox = bbox
            break
    
    if not product_code:
        for (bbox, text, prob) in result:
            text_upper = text.upper()
            match = re.search(r'[A-Z&]+\d?[O0]\d+[O0]*\d*', text_upper)
            if match and len(match.group(0)) >= 8:
                code_text = match.group(0)
                product_code = code_text.replace('O', '0')
                code_bbox = bbox
                break
    
    if not product_code or not code_bbox:
        print("  WARNING: No product code found")
        return None
    
    print(f"  Found code: {product_code}")
    
    # Calculate crop region
    y_coords = [point[1] for point in code_bbox]
    y_min = min(y_coords)
    y_max = max(y_coords)
    
    img = Image.open(image_path)
    img_height = img.height
    img_width = img.width
    
    margin_above = 100
    margin_below = 200
    
    crop_y_min = max(0, y_min - margin_above)
    crop_y_max = min(img_height, y_max + margin_below)
    
    cropped = img.crop((0, crop_y_min, img_width, crop_y_max))
    cropped_array = np.array(cropped)
    
    # Run OCR on cropped image
    cropped_result = reader.readtext(cropped_array, detail=0)
    cropped_text = ' '.join(cropped_result).upper()
    
    print(f"  Cropped OCR (raw): {cropped_text}")
    
    # Clean OCR errors
    cropped_text = clean_ocr_text(cropped_text)
    
    print(f"  Cropped OCR (cleaned): {cropped_text}")
    
    # Find the code using fuzzy matching
    code_match = fuzzy_find_code(cropped_text, product_code)
    
    if not code_match:
        print(f"  WARNING: Code not found in cropped text")
        return product_code
    
    # Get everything after the code
    code_end = code_match.end()
    after_code = cropped_text[code_end:].strip()
    
    # Stop at common phrases
    stop_phrases = ['WAS USED', 'USED IN', 'PRODUCTION', 'THE EXPANSE', 'WWW', 'AUTHORIZED']
    for phrase in stop_phrases:
        pos = after_code.find(phrase)
        if pos != -1:
            after_code = after_code[:pos].strip()
            break
    
    # Clean up junk words
    junk_words = ['CERTIFIES', 'THAT', 'THE', 'FOLLOWING', 'ITEM', 'THIS', 'DOCUMENT', 'OF', 'COA', 'CERTIFICATE']
    words = after_code.split()
    clean_words = [w for w in words if w not in junk_words]
    
    description = ' '.join(clean_words[:15])
    
    if description:
        return f"{product_code} {description}"
    else:
        return product_code

if __name__ == "__main__":
    directory = input("Enter directory path (or press Enter for current directory): ").strip()
    if not directory:
        directory = "."
    
    if os.path.isdir(directory):
        image_files = list_image_files(directory)
        print(f"Found {len(image_files)} image files\n")
        
        print("Checking COAs and extracting titles...")
        for filename in image_files:
            filepath = os.path.join(directory, filename)
            if is_coa(filepath):
                title = extract_title_with_crop(filepath)
                print(f"COA: {filename}")
                print(f"  → Title: {title}\n")
            else:
                print(f"Prop: {filename}")
    else:
        print(f"Error: '{directory}' is not a valid directory")