"""
text_processor.py

Author: maymeridian
Description: The logic engine for text analysis. Implements multiple extraction strategies,
             cleaning pipelines, regex pattern matching, and smart formatting rules for COA data.
"""

import re
from typing import Optional, Tuple, Set
import config

# ==========================================
# CONSTANTS & PATTERNS
# ==========================================

# Words that should generally remain lowercase in titles (unless at the start)
LOWERCASE_WORDS: Set[str] = {
    'A', 'An', 'The', 'And', 'But', 'Or', 'Nor', 'For', 'Yet', 'So', 
    'At', 'By', 'In', 'Of', 'On', 'To', 'Up', 'With', 'From'
}

# ==========================================
# DETECTION LOGIC
# ==========================================

def is_coa(text: str) -> bool:
    """
    Determines if the provided text represents a Certificate of Authenticity.
    
    Logic:
        Uses a weighted keyword system defined in config.py.
        - Requires at least 1 STRONG indicator (e.g., "Certificate of Authenticity").
        - OR requires at least 3 WEAK indicators (e.g., "Propabilia", "Movie & TV").
    
    Args:
        text (str): The full OCR text of the document.
        
    Returns:
        bool: True if it is a COA, False otherwise.
    """
    if not text:
        return False
        
    text_upper = text.upper()
    
    strong_hits = sum(1 for kw in config.STRONG_INDICATORS if kw in text_upper)
    weak_hits = sum(1 for kw in config.WEAK_INDICATORS if kw in text_upper)
    
    return strong_hits >= 1 or weak_hits >= 3

# ==========================================
# CLEANING & FORMATTING HELPERS
# ==========================================

def _fix_sku_tail(sku: str) -> str:
    """
    Standardizes the SKU suffix.
    
    Rule: A SKU must end in a block of at least 4 digits/characters.
    Issue: OCR often misreads the number '0' as the letter 'O' in this block.
    Fix: If the tail contains 'O' mixed with digits, convert 'O' -> '0'.
    
    Example: 
        WHISTLEBLOWEROO01 -> WHISTLEBLOWER0001
    """
    # --- CRASH FIX: Handle None ---
    if not sku: return ""

    # Regex: Match suffix of 4+ characters containing only Digits or 'O'
    match = re.search(r'([0-9O]{4,})$', sku)
    
    if match:
        suffix = match.group(1)
        # Only apply fix if an 'O' is actually present
        if 'O' in suffix:
            fixed_suffix = suffix.replace('O', '0')
            # Splice fixed suffix back onto the original string
            return sku[:-len(suffix)] + fixed_suffix
            
    return sku

def _fix_typo_zeros(text: str) -> str:
    """
    Corrects common OCR confusions between '0' (zero) and 'O' (letter) in descriptions.
    """
    # --- CRASH FIX: Handle None ---
    if not text: return ""

    # 1. Sandwich Fix: Digit + O + Digit -> 0 (e.g., 2O24 -> 2024)
    text = re.sub(r'(?<=\d)O(?=\d)', '0', text, flags=re.IGNORECASE)

    # 2. Contextual Fixes: Dot separators (e.g., 2.O -> 2.0, A.0 -> A.O)
    text = re.sub(r'(?<=\d)\.O', '.0', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<=[a-zA-Z])\.0', '.O', text)

    # 3. Word-based Logic
    def repl(m):
        word = m.group(0)
        if word.isdigit(): return word
        if any(c.isdigit() and c != '0' for c in word): return word
        return word.replace('0', 'O')
    
    return re.sub(r'\b\w*0\w*\b', repl, text)

def _move_season_code(text: str) -> Tuple[str, str]:
    """
    Extracts season/episode codes (e.g., S01E05) to move them to the end of the filename.
    
    Returns:
        Tuple[str, str]: (Description without code, The extracted code)
    """
    # --- CRASH FIX: Handle None ---
    if not text: return "", ""

    pattern = r'\(?\bS\d{1,2}E\d{1,2}\b\)?'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return text, ""
    
    tag = match.group(0)
    # Clean up formatting: (S01E01) -> S01E01
    clean_tag = tag.replace('(', '').replace(')', '').upper()
    
    # Remove tag from original text
    return text.replace(tag, ''), clean_tag

def _clean_description(raw_desc: str) -> str:
    """
    Main formatting pipeline for item descriptions.
    Applies regex fixes, casing rules, and formatting standards.
    """
    # --- CRASH FIX: Handle None ---
    if not raw_desc: return "Unknown Item"

    # 1. Zero/O Typo Fixes
    desc = _fix_typo_zeros(raw_desc)
    
    # 2. Fix Squished Apostrophes (Clarke'sbackpack -> Clarke's backpack)
    desc = re.sub(r"('s)(?=[a-zA-Z])", r"\1 ", desc, flags=re.IGNORECASE)

    # 3. CamelCase Splitter (RussellLightbourne -> Russell Lightbourne)
    desc = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', desc)

    # 4. Unglue Parentheses
    desc = re.sub(r'(?<=[a-zA-Z0-9])\(', ' (', desc)
    
    # 5. Apply Title Case
    desc = desc.title()
    desc = desc.replace("'S", "'s")  # Fix possessive case ('S -> 's)

    # 6. Restore Roman Numerals (e.g., Iii -> III)
    roman_pattern = r'\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xii?i?)\b'
    desc = re.sub(roman_pattern, lambda m: m.group(0).upper(), desc)

    # 7. Apply Lowercase Rules (Conjunctions, Prepositions)
    for word in LOWERCASE_WORDS:
        pattern = r'\b' + word + r'\b(?!\.)'
        desc = re.sub(pattern, word.lower(), desc, flags=re.IGNORECASE)

    # 8. Force Uppercase for Specific Acronyms (Configurable)
    for word in config.FORCE_UPPERCASE:
        pattern = r'\b' + word + r'\b'
        desc = re.sub(pattern, word.upper(), desc, flags=re.IGNORECASE)

    # 9. Restore Acronym Formatting (A.L.I.E.)
    def upper_acronym(m):
        return m.group(0).upper()
    desc = re.sub(r'\b([a-zA-Z]\.)+[a-zA-Z0-9]?\b', upper_acronym, desc)

    # 10. Final Character Cleanup
    desc = re.sub(r'[^\w\s\'\-\.]', ' ', desc)

    desc = desc.strip()
    # Ensure the very first letter is always Uppercase
    if desc:
        desc = desc[0].upper() + desc[1:]

    # Collapse multiple spaces into single hyphens for filename safety
    return re.sub(r'\s+', '-', desc)

def clean_filename(text: str) -> str:
    """Removes illegal characters for Windows filenames."""
    # --- CRASH FIX: Handle None ---
    if not text: return ""
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

# ==========================================
# EXTRACTION LOGIC
# ==========================================

def extract_details(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the Item SKU and Description from the OCR text.
    
    Implements two strategies:
    1. Standard Regex: Looks for "CODE Description was used in".
    2. Context Anchors: Looks for specific introductory phrases used in some layouts.
    
    Returns:
        (Item Code, Cleaned Description) or (None, None)
    """
    # --- CRASH FIX: The Main Fix ---
    if not text:
        return None, None
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    raw_code = None
    raw_desc = None

    # --- STRATEGY 1: Standard Regex (Primary) ---
    pattern = r'([A-Za-z&]+\d{4,7})\s*(.+?)\s+was used in'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        raw_code = match.group(1)
        raw_desc = match.group(2)

    # --- STRATEGY 2: Context Anchors (Fallback) ---
    if not raw_code:
        intro_anchors = ["production of the above", "certifies that the following item"]
        
        for i, line in enumerate(lines):
            matched_anchor = next((a for a in intro_anchors if a in line.lower()), None)
            
            if not matched_anchor:
                continue
                
            if i + 1 >= len(lines):
                continue

            target_line = lines[i+1]
            match_ctx = re.match(r"^([A-Z0-9-]{3,})\s+(.*)$", target_line)
            
            if not match_ctx:
                continue

            raw_code = match_ctx.group(1)
            raw_desc = match_ctx.group(2)

            # Special Handling: Multi-line description check
            if "production of the above" in matched_anchor and i + 2 < len(lines):
                next_line = lines[i+2]
                if "NOT VALID" not in next_line and "www" not in next_line and "Daily Log" in next_line:
                    raw_desc += f" {next_line}"
            
            break

    # --- FINAL PROCESSING ---
    if raw_code and raw_desc:
        
        # === NEW: De-Merge Logic (Harold Fix) ===
        # If OCR missed the space (e.g. GOOSEBUMPSO695HAROLD), separate them.
        # Look for: Digits followed immediately by 3+ letters at end of string.
        merge_check = re.search(r'(\d+)([A-Za-z]{3,})$', raw_code)
        if merge_check:
            # Found a merge! (e.g. 695 + HAROLD)
            digits = merge_check.group(1)
            word = merge_check.group(2)
            
            # 1. Chop the word off the SKU
            raw_code = raw_code[:-len(word)]
            # 2. Add the word to the START of the description
            raw_desc = f"{word} {raw_desc}"
        # ========================================

        # 1. Clean and Fix SKU
        item_code = clean_filename(raw_code.upper())
        item_code = _fix_sku_tail(item_code)

        # 2. Process Description
        desc_no_season, season_suffix = _move_season_code(raw_desc)
        clean_desc = _clean_description(desc_no_season)
        
        # 3. Re-attach Season Code
        if season_suffix:
            clean_desc = f"{clean_desc}-{season_suffix}"
            
        return item_code, clean_desc

    return None, None