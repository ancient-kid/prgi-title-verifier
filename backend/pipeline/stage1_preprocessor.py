"""
Stage 1: Pre-processing & Anchor Word Extraction

Tasks:
1. Normalize case and clean non-alphanumeric punctuation.
2. Strip generic periodicities and pure structural modifiers (e.g. "The", "Daily", "Weekly", "Monthly", "Yearly", "News").
3. Isolate the distinctive 'Anchor Word(s)'.
4. Detect purely generic titles (e.g. "The Daily News") and trigger immediate 0% probability rejection.
"""

import re
import unicodedata
from typing import Any, Dict, List, Set, Tuple

# Pure generic periodicities and non-distinctive modifier words
PURE_GENERIC_WORDS: Set[str] = {
    # English Periodicities & Generics
    "the", "a", "an", "daily", "weekly", "fortnightly", "monthly", "bimonthly", 
    "quarterly", "half-yearly", "yearly", "annual", "morning", "evening", 
    "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "today", "now", "news", "express", "chronicle", "herald", "bulletin", 
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
    "news", "express", "herald", "chronicle", "bulletin", "journal", 
    "gazette", "post", "mail", "voice", "samachar", "sandesh", "patrika", 
    "prabhat", "sandhya", "vani", "varta", "vartha", "today", "live", "24x7", 
    "media", "press", "digest", "review"
}


def clean_text(text: str) -> str:
    """Normalize text: strip accents, lowercase, remove special characters except spaces."""
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
    """
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
            "is_purely_generic": True,
            "rejection_reason": "Title is empty or contains no valid alphanumeric characters."
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
        "is_purely_generic": False,
        "rejection_reason": None
    }
