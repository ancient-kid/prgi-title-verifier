"""
Stage 4B: Orthographic (String Distance & Fuzzy) Similarity Engine

Computes string-level orthographic distances and fuzzy similarities:
1. Normalized Levenshtein similarity [0.0 to 1.0].
2. Jaro-Winkler similarity [0.0 to 1.0].
3. Token Sort Ratio (word-order insensitive) [0.0 to 1.0].
4. Set-based Character 3-Gram Dice coefficient [0.0 to 1.0].

Aggregation Policy: Configurable via ORTHOGRAPHIC_AGGREGATION_POLICY (default: 'max').
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from backend.config import NGRAM_SIZE, ORTHOGRAPHIC_AGGREGATION_POLICY


def clean_orthographic_text(text: str) -> str:
    """Normalize text for orthographic comparison: lowercase and clean whitespace."""
    if not text:
        return ""
    # Strip non-alphanumeric punctuation, keeping whitespace
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def compute_char_ngrams(text: str, n: int = NGRAM_SIZE) -> Set[str]:
    """
    Extract set-based character n-grams from string with boundary markers.
    Pads string with leading and trailing underscores for positional context.
    """
    if not text:
        return set()
    cleaned = clean_orthographic_text(text)
    if not cleaned:
        return set()
    padded = f"_{cleaned}_"
    if len(padded) < n:
        return {padded}
    return {padded[i:i + n] for i in range(len(padded) - n + 1)}


def ngram_similarity(text1: str, text2: str, n: int = NGRAM_SIZE) -> float:
    """
    Compute set-based Dice similarity coefficient on character n-grams.
    
    Formula:
        Dice(A, B) = 2 * |A ∩ B| / (|A| + |B|)
    """
    ng1 = compute_char_ngrams(text1, n=n)
    ng2 = compute_char_ngrams(text2, n=n)
    if not ng1 or not ng2:
        return 0.0
    intersection = len(ng1 & ng2)
    return (2.0 * intersection) / (len(ng1) + len(ng2))


def compute_orthographic_similarity(title1: str, title2: str) -> Dict[str, float]:
    """
    Compute comprehensive orthographic similarity metrics between two title strings.
    
    Returns:
        Dict containing:
            - jaro_winkler: float
            - levenshtein_ratio: float
            - token_sort_ratio: float
            - ngram_sim: float
            - aggregate_orthographic_score: float
    """
    t1 = clean_orthographic_text(title1)
    t2 = clean_orthographic_text(title2)
    
    # Handle empty strings
    if not t1 or not t2:
        return {
            "jaro_winkler": 0.0,
            "levenshtein_ratio": 0.0,
            "token_sort_ratio": 0.0,
            "ngram_sim": 0.0,
            "aggregate_orthographic_score": 0.0
        }
        
    # Exact match shortcut
    if t1 == t2:
        return {
            "jaro_winkler": 1.0,
            "levenshtein_ratio": 1.0,
            "token_sort_ratio": 1.0,
            "ngram_sim": 1.0,
            "aggregate_orthographic_score": 1.0
        }
        
    tokens1 = set(t1.split())
    tokens2 = set(t2.split())
    jaccard = len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)
    
    try:
        from rapidfuzz.distance import JaroWinkler, Levenshtein
        from rapidfuzz import fuzz
        
        # 1. Normalized Levenshtein similarity [0.0, 1.0]
        lev = Levenshtein.normalized_similarity(t1, t2)
        
        # 2. Token Sort Ratio [0.0, 1.0]
        raw_token_sort = fuzz.token_sort_ratio(t1, t2) / 100.0
        # If token overlap is strong, retain full token sort; otherwise scale mildly
        token_sim = raw_token_sort if jaccard >= 0.5 else raw_token_sort * (0.2 + 0.8 * jaccard)
        
        # 3. Jaro-Winkler similarity [0.0, 1.0]
        is_single_word = (" " not in t1 and " " not in t2)
        if lev >= 0.85 or (is_single_word and lev >= 0.70):
            jw = JaroWinkler.similarity(t1, t2)
        elif is_single_word and max(len(t1), len(t2)) <= 6 and lev >= 0.60:
            jw = JaroWinkler.similarity(t1, t2) * 0.85
        else:
            jw = lev
            
        # 4. Character 3-Gram Dice similarity [0.0, 1.0]
        ng_sim = ngram_similarity(t1, t2, n=NGRAM_SIZE)
        
        # Aggregation policy
        if ORTHOGRAPHIC_AGGREGATION_POLICY == "mean":
            agg = (lev + jw + token_sim + ng_sim) / 4.0
        else:
            # Conservative max aggregation
            agg = max(lev, jw, token_sim, ng_sim)
            
        return {
            "jaro_winkler": round(float(jw), 4),
            "levenshtein_ratio": round(float(lev), 4),
            "token_sort_ratio": round(float(token_sim), 4),
            "ngram_sim": round(float(ng_sim), 4),
            "aggregate_orthographic_score": round(float(agg), 4)
        }
    except Exception:
        # Fallback pure-Python calculation if rapidfuzz unavailable
        ng_sim = ngram_similarity(t1, t2, n=NGRAM_SIZE)
        agg = round(max(ng_sim, jaccard), 4)
        return {
            "jaro_winkler": agg,
            "levenshtein_ratio": agg,
            "token_sort_ratio": round(float(jaccard), 4),
            "ngram_sim": round(float(ng_sim), 4),
            "aggregate_orthographic_score": agg
        }
