"""Handles OCR text analysis and data extraction."""
import re
import config

# Words that should remain lowercase in titles
LOWERCASE_WORDS = {
    'A', 'An', 'The', 'And', 'But', 'Or', 'Nor', 'For', 'Yet', 'So', 
    'At', 'By', 'In', 'Of', 'On', 'To', 'Up', 'With', 'From'
}

def is_coa(text):
    """
    Determines if text represents a Certificate of Authenticity.
    Uses user-defined Strong/Weak indicators from config.
    """
    if not text: return False
    text_upper = text.upper()
    
    strong_hits = sum(1 for kw in config.STRONG_INDICATORS if kw in text_upper)
    weak_hits = sum(1 for kw in config.WEAK_INDICATORS if kw in text_upper)
    
    return strong_hits >= 1 or weak_hits >= 3

def _fix_sku_tail(sku):
    """
    Enforces the rule: SKUs must end in at least 4 digits.
    If the tail contains 'O's mixed with digits, convert them to '0'.
    Ex: WHISTLEBLOWEROO01 -> WHISTLEBLOWER0001
    """
    match = re.search(r'([0-9O]{4,})$', sku)
    if match:
        suffix = match.group(1)
        if 'O' in suffix:
            fixed_suffix = suffix.replace('O', '0')
            return sku[:-len(suffix)] + fixed_suffix
    return sku

def _fix_typo_zeros(text):
    """Smart Zero/O replacement logic for DESCRIPTIONS."""
    # 1. SANDWICH FIX: Digit + O + Digit -> 0
    text = re.sub(r'(?<=\d)O(?=\d)', '0', text, flags=re.IGNORECASE)

    # 2. CONTEXTUAL FIXES (Dot Separators)
    text = re.sub(r'(?<=\d)\.O', '.0', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<=[a-zA-Z])\.0', '.O', text)

    # 3. WORD-BASED FIXES
    def repl(m):
        word = m.group(0)
        if word.isdigit(): return word
        if any(c.isdigit() and c != '0' for c in word): return word
        return word.replace('0', 'O')
    
    return re.sub(r'\b\w*0\w*\b', repl, text)

def _move_season_code(text):
    """Moves 'SxxExx' patterns from the middle to the end."""
    pattern = r'\(?\bS\d{1,2}E\d{1,2}\b\)?'
    match = re.search(pattern, text, re.IGNORECASE)
    if not match: return text, ""
    
    tag = match.group(0)
    clean_tag = tag.replace('(', '').replace(')', '').upper()
    return text.replace(tag, ''), clean_tag

def _clean_description(raw_desc):
    """Pipeline to clean and format the item description."""
    desc = _fix_typo_zeros(raw_desc)
    
    # 1. FIX SQUISHED APOSTROPHES (Clarke'sbackpack -> Clarke's backpack)
    # Looks for 's followed immediately by a letter and adds a space
    desc = re.sub(r"('s)(?=[a-zA-Z])", r"\1 ", desc, flags=re.IGNORECASE)

    # 2. CamelCase Splitter (RussellLightbourne -> Russell Lightbourne)
    desc = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', desc)

    desc = re.sub(r'(?<=[a-zA-Z0-9])\(', ' (', desc)
    
    # Standardize Case
    desc = desc.title()
    desc = desc.replace("'S", "'s")

    # RESTORE ROMAN NUMERALS
    roman_pattern = r'\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xii?i?)\b'
    desc = re.sub(roman_pattern, lambda m: m.group(0).upper(), desc)

    # LOWERCASE LINKING WORDS
    for word in LOWERCASE_WORDS:
        pattern = r'\b' + word + r'\b(?!\.)'
        desc = re.sub(pattern, word.lower(), desc, flags=re.IGNORECASE)

    # FORCE UPPERCASE WORDS (GCPD, AKA)
    for word in config.FORCE_UPPERCASE:
        pattern = r'\b' + word + r'\b'
        desc = re.sub(pattern, word.upper(), desc, flags=re.IGNORECASE)

    # RESTORE ACRONYMS (A.L.I.E.)
    def upper_acronym(m):
        return m.group(0).upper()
    desc = re.sub(r'\b([a-zA-Z]\.)+[a-zA-Z0-9]?\b', upper_acronym, desc)

    desc = re.sub(r'[^\w\s\'\-\.]', ' ', desc)

    desc = desc.strip()
    if desc:
        desc = desc[0].upper() + desc[1:]

    return re.sub(r'\s+', '-', desc)

def clean_filename(text):
    if not text: return ""
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

def extract_details(text):
    if not text: return None, None
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    raw_code = None
    raw_desc = None

    # Strategy 1: Standard
    pattern = r'([A-Za-z&]+\d{4,7})\s*(.+?)\s+was used in'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        raw_code = match.group(1)
        raw_desc = match.group(2)

    # Strategy 2: Context
    if not raw_code:
        intro_anchors = ["production of the above", "certifies that the following item"]
        for i, line in enumerate(lines):
            matched_anchor = next((a for a in intro_anchors if a in line.lower()), None)
            if not matched_anchor: continue
            if i + 1 >= len(lines): continue

            target_line = lines[i+1]
            match_ctx = re.match(r"^([A-Z0-9-]{3,})\s+(.*)$", target_line)
            if not match_ctx: continue

            raw_code = match_ctx.group(1)
            raw_desc = match_ctx.group(2)

            if "production of the above" in matched_anchor and i + 2 < len(lines):
                next_line = lines[i+2]
                if "NOT VALID" not in next_line and "www" not in next_line and "Daily Log" in next_line:
                    raw_desc += f" {next_line}"
            break

    if raw_code and raw_desc:
        # 1. Clean Code
        item_code = clean_filename(raw_code.upper())
        item_code = _fix_sku_tail(item_code)

        # 2. Process Description
        desc_no_season, season_suffix = _move_season_code(raw_desc)
        clean_desc = _clean_description(desc_no_season)
        
        if season_suffix:
            clean_desc = f"{clean_desc}-{season_suffix}"
            
        return item_code, clean_desc

    return None, None