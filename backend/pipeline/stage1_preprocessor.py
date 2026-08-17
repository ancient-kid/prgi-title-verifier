"""
Stage 1: Pre-processing, Structural Validation & Anchor Word Extraction

Tasks:
1. Validate PRGI structural constraints:
   - Reject titles with non-text characters, mathematical symbols (+, *, etc.), emojis, pictographs, hallmarks, logos.
   - Reject purely numeric titles (just numbers).
2. Normalize case and clean text.
3. Strip generic periodicities and structural modifiers (e.g. "The", "Daily", "Weekly", "News", "Samachar").
4. Isolate the distinctive 'Anchor Word(s)'.
5. Detect purely generic titles (e.g. "The Daily News", "Weekly Express India") and trigger immediate 0% probability rejection.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.pipeline.gibberish_detector import validate_title_meaningfulness

# Pure generic periodicities and non-distinctive modifier words
PURE_GENERIC_WORDS: Set[str] = {
    # English Periodicities & Generics
    "the", "a", "an", "daily", "weekly", "fortnightly", "monthly", "bimonthly", 
    "quarterly", "half-yearly", "yearly", "annual", "morning", "evening", 
    "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "today", "now", "news", "express", "times", "chronicle", "herald", "bulletin", 
    "journal", "gazette", "post", "mail", "voice", "tribune", "mirror", "report", 
    "reporter", "press", "media", "digest", "review", "dispatch", "update", 
    "leader", "courier", "star", "standard", "observer", "frontline", "current",
    "new", "super", "mega", "ultra", "prime", "real", "true", "live", "direct",
    "india", "bharat", "hindustan", "national", "regional", "state", "city",

    # Hindi / Sanskrit / Devanagari Periodicities & Structural Terms
    "dainik", "saptahik", "pakshik", "masik", "traimasik", "ardhavarshik", "varshik",
    "samachar", "khabar", "sandesh", "patrika", "prabhat", "sandhya", "pratidin",
    "aaj", "kal", "varta", "vartha", "suchna", "darshika", "shree", "shri", "naya", "nav",
    
    # Regional Indian Generics
    "bartaman", "sambad", "murasu", "malai", "sudarmalar", "mani", 
    "taaza", "roznama", "akhbar"
}

# Alias for backward compatibility
GENERIC_MODIFIERS = PURE_GENERIC_WORDS

# Prefix-specific words to strip
GENERIC_PREFIXES: Set[str] = {
    "the", "a", "an", "daily", "weekly", "fortnightly", "monthly", "dainik", 
    "saptahik", "masik", "shree", "shri", "nav", "naya", "aaj", "new", 
    "super", "apna", "mera", "hamara"
}

# Suffix-specific words to strip
GENERIC_SUFFIXES: Set[str] = {
    "times", "news", "express", "herald", "chronicle", "bulletin", "journal", 
    "gazette", "post", "mail", "voice", "samachar", "sandesh", "patrika", 
    "prabhat", "sandhya", "vani", "varta", "vartha", "today", "live", "24x7", 
    "media", "press", "digest", "review", "daily", "weekly", "monthly", "yearly",
    "annual", "tribune", "mirror", "star", "standard", "observer", "report",
    "reporter", "courier", "leader", "dispatch", "update", "akhbar", "roznama"
}

# Explicitly prohibited characters: mathematical symbols, signs, currency, special punctuation
EXPLICIT_PROHIBITED_CHARS: Set[str] = set(
    '+=*@#$%^&_~|\\/!?()[]{}<>;:"`©®™°•§¶†‡₹€£¥±÷×√∞'
)


def validate_title_structure(raw_title: str) -> Dict[str, Any]:
    """
    Validates structural PRGI constraints on the submitted title string:
    1. Prohibits non-text characters, mathematical symbols (+, *, etc.), pictographs, hallmarks, logos, emojis.
    2. Prohibits numeric-only titles (consisting solely of numbers/digits).
    3. Prohibits empty or whitespace-only inputs.
    """
    if not raw_title or not raw_title.strip():
        return {
            "valid": False,
            "error_type": "EMPTY_TITLE",
            "rule": "Empty Title Violation",
            "guideline_ref": "PRGI General Guidelines",
            "reason": "Title is empty or contains no valid alphanumeric characters.",
            "prohibited_symbols": []
        }
        
    prohibited_symbols = []
    
    for ch in raw_title:
        cat = unicodedata.category(ch)
        # So: Symbol other (emojis, hallmarks, pictographs)
        # Sm: Symbol math (+, =, etc.)
        # Sc: Symbol currency ($, ₹, etc.)
        # Sk: Symbol modifier
        if ch in EXPLICIT_PROHIBITED_CHARS or cat in ('So', 'Sm', 'Sc', 'Sk'):
            if ch not in prohibited_symbols:
                prohibited_symbols.append(ch)
                
    if prohibited_symbols:
        symbols_str = ", ".join(f"'{s}'" for s in prohibited_symbols)
        return {
            "valid": False,
            "error_type": "PROHIBITED_SYMBOLS",
            "rule": "Prohibited Non-Text Characters & Symbols Violation",
            "guideline_ref": "PRGI Non-Text Characters Prohibition",
            "reason": (
                f"Prohibited Non-Text Characters Violation: Titles containing non-text characters, or any form of "
                f"signs, symbols including mathematical symbols (like '+', '*', etc.), pictographs, photographs, "
                f"hallmarks, logos, monograms, phonograms, emojis, etc. are strictly prohibited under PRGI Guidelines. "
                f"(Detected prohibited characters: {symbols_str})"
            ),
            "prohibited_symbols": prohibited_symbols
        }
        
    # Check if purely numeric (no alphabetical / linguistic letter across any language script)
    has_letters = any(unicodedata.category(ch).startswith('L') for ch in raw_title)
    if not has_letters:
        return {
            "valid": False,
            "error_type": "PURE_NUMERIC",
            "rule": "Numeric-Only Title Prohibition",
            "guideline_ref": "PRGI Numeric Title Prohibition",
            "reason": (
                f"Numeric-Only Title Violation: The submitted title '{raw_title}' consists solely of numbers "
                f"or digits without substantive alphabetical/text characters. Titles containing exclusively numbers "
                f"are not permitted under PRGI Title Allocation Guidelines."
            ),
            "prohibited_symbols": []
        }

    # Check meaningfulness & gibberish (Shannon Entropy, N-Gram, Phonetic cluster rules)
    meaning_check = validate_title_meaningfulness(raw_title)
    if not meaning_check["valid"]:
        return {
            "valid": False,
            "error_type": meaning_check["error_type"],
            "rule": meaning_check["rule"],
            "guideline_ref": meaning_check["guideline_ref"],
            "reason": meaning_check["reason"],
            "prohibited_symbols": []
        }

    return {
        "valid": True,
        "error_type": None,
        "rule": None,
        "guideline_ref": None,
        "reason": None,
        "prohibited_symbols": []
    }


def clean_text(text: str) -> str:
    """Normalize text: strip accents, lowercase, remove special characters except spaces and hyphens."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"[\s\-]+", " ", text).strip()
    return text


def extract_anchor_words(raw_title: str) -> Dict[str, Any]:
    """
    Process raw title into clean tokens, stripped prefixes/suffixes, and distinct anchor word(s).
    Validates structural constraints (symbols, math chars, emojis, numeric-only titles).
    """
    # 1. Structural validity check (Symbols, Emojis, Pure Numbers)
    struct_check = validate_title_structure(raw_title)
    if not struct_check["valid"]:
        cleaned = clean_text(raw_title)
        tokens = cleaned.split() if cleaned else []
        return {
            "raw_title": raw_title,
            "cleaned_title": cleaned,
            "tokens": tokens,
            "stripped_prefixes": [],
            "stripped_suffixes": [],
            "anchor_words": "",
            "anchor_tokens": [],
            "is_valid_structure": False,
            "error_type": struct_check["error_type"],
            "rule": struct_check["rule"],
            "guideline_ref": struct_check["guideline_ref"],
            "rejection_reason": struct_check["reason"],
            "is_purely_generic": False
        }
        
    cleaned = clean_text(raw_title)
    tokens = cleaned.split() if cleaned else []
    
    if not tokens:
        return {
            "raw_title": raw_title,
            "cleaned_title": "",
            "tokens": [],
            "stripped_prefixes": [],
            "stripped_suffixes": [],
            "anchor_words": "",
            "anchor_tokens": [],
            "is_valid_structure": False,
            "error_type": "EMPTY_TITLE",
            "rule": "Empty Title Violation",
            "guideline_ref": "PRGI General Guidelines",
            "rejection_reason": "Title is empty or contains no valid alphanumeric characters.",
            "is_purely_generic": True
        }
        
    # Check if all tokens are generic
    non_generic_tokens = [t for t in tokens if t not in PURE_GENERIC_WORDS]
    
    if not non_generic_tokens:
        return {
            "raw_title": raw_title,
            "cleaned_title": cleaned,
            "tokens": tokens,
            "stripped_prefixes": [],
            "stripped_suffixes": [],
            "anchor_words": "",
            "anchor_tokens": [],
            "is_valid_structure": True,
            "error_type": "PURE_GENERIC",
            "rule": "Pure Generic Title Violation",
            "guideline_ref": "Guideline 8 (Generic Terms)",
            "is_purely_generic": True,
            "rejection_reason": (
                f"Pure Generic Title Violation (Stage 1): The submitted title '{raw_title}' "
                f"consists entirely of generic modifiers and periodicities ({', '.join(tokens)}). "
                f"Under PRGI Guideline 8, titles must contain a distinctive non-generic anchor word."
            )
        }
        
    # Strip leading prefixes
    start_idx = 0
    stripped_prefixes = []
    while start_idx < len(tokens) and tokens[start_idx] in GENERIC_PREFIXES:
        stripped_prefixes.append(tokens[start_idx])
        start_idx += 1
        
    # Strip trailing suffixes
    end_idx = len(tokens) - 1
    stripped_suffixes = []
    while end_idx >= start_idx and tokens[end_idx] in GENERIC_SUFFIXES:
        stripped_suffixes.insert(0, tokens[end_idx])
        end_idx -= 1
        
    anchor_tokens = tokens[start_idx:end_idx + 1] if start_idx <= end_idx else non_generic_tokens
    anchor_words = " ".join(anchor_tokens)
    
    return {
        "raw_title": raw_title,
        "cleaned_title": cleaned,
        "tokens": tokens,
        "stripped_prefixes": stripped_prefixes,
        "stripped_suffixes": stripped_suffixes,
        "anchor_words": anchor_words,
        "anchor_tokens": anchor_tokens,
        "is_valid_structure": True,
        "error_type": None,
        "rule": None,
        "guideline_ref": None,
        "is_purely_generic": False,
        "rejection_reason": None
    }
