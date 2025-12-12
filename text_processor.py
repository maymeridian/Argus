"""Handles OCR text analysis and data extraction."""
import re
import config

# Words that should remain lowercase in titles
# (unless they are the very first word, which title() handles)
LOWERCASE_WORDS = {
    'A', 'An', 'The', 'And', 'But', 'Or', 'Nor', 'For', 'Yet', 'So', 
    'At', 'By', 'In', 'Of', 'On', 'To', 'Up', 'With', 'From'
}

def is_coa(text):
    """Determines if text represents a Certificate of Authenticity."""
    if not text:
        return False
    text_upper = text.upper()
    matches = sum(1 for kw in config.COA_INDICATORS if kw in text_upper)
    return matches >= 2

def _fix_typo_zeros(text):
    """Replaces '0' with 'O' in words that contain no other digits."""
    def repl(m):
        word = m.group(0)
        # If word has digits 1-9, it's a real number code (like S03). Keep it.
        if any(c.isdigit() and c != '0' for c in word):
            return word
        # Otherwise (H00CH), replace 0 with O.
        return word.replace('0', 'O')
    
    return re.sub(r'\b\w*0\w*\b', repl, text)

def _move_season_code(text):
    """Moves 'SxxExx' patterns from the middle to the end."""
    pattern = r'\(?\bS\d{1,2}E\d{1,2}\b\)?'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return text, ""
    
    tag = match.group(0)
    clean_tag = tag.replace('(', '').replace(')', '').upper()
    
    # Remove the tag from the original text so we can append it later
    clean_text = text.replace(tag, '')
    return clean_text, clean_tag

def _clean_description(raw_desc):
    """Pipeline to clean and format the item description."""
    
    # 1. Fix Typo Zeros (H00CH -> HOOCH)
    desc = _fix_typo_zeros(raw_desc)

    # 2. Unglue Parentheses (Word(S01) -> Word (S01))
    desc = re.sub(r'(?<=[a-zA-Z0-9])\(', ' (', desc)

    # 3. Standardize Case (Everything becomes Title Case)
    desc = desc.title()
    desc = desc.replace("'S", "'s")  # Fix possessives (Maneo'S -> Maneo's)

    # 4. LOWERCASE LINKING WORDS (New Step)
    # We look for words in our list and lowercase them if found
    # We use \b to ensure we match whole words only (e.g. don't lowercase 'And' inside 'Band')
    for word in LOWERCASE_WORDS:
        # Regex: Find the word surrounded by boundaries, replace with lowercase version
        pattern = r'\b' + word + r'\b'
        desc = re.sub(pattern, word.lower(), desc)

    # 5. Handle Punctuation 
    # Replace non-word chars with spaces, BUT keep apostrophes and hyphens
    desc = re.sub(r'[^\w\s\'\-]', ' ', desc)

    # 6. Final Polish (Collapse spaces to hyphens)
    return re.sub(r'\s+', '-', desc.strip())

def extract_details(text):
    """Extracts Item Code and cleaned Description from OCR text."""
    if not text:
        return None, None

    # Regex: SKU + (Optional Space) + Description + "was used in"
    pattern = r'([A-Za-z&]+\d{4,7})\s*(.+?)\s+was used in'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

    if not match:
        return None, None

    item_code = match.group(1).upper()
    raw_desc = match.group(2).strip()

    # Process Description
    desc_no_season, season_suffix = _move_season_code(raw_desc)
    clean_desc = _clean_description(desc_no_season)

    # Re-attach season code at the very end
    if season_suffix:
        clean_desc = f"{clean_desc}-{season_suffix}"

    return item_code, clean_desc