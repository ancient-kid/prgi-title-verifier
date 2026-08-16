"""
Stage 4B: Orthographic (String Distance & Fuzzy) Similarity Engine

Computes string-level orthographic distances and fuzzy similarities:
1. Normalized Levenshtein / Damerau-Levenshtein Edit Distance.
2. Token Sort Ratio weighted by Jaccard Token Overlap.
3. Character 3-Gram Dice Similarity.
4. Jaro-Winkler Similarity for single-word / high-edit candidates.
"""

from typing import Dict, List, Optional, Set, Tuple


def compute_char_ngrams(text: str, n: int = 3) -> Set[str]:
    """Extract character n-grams from string."""
    text = f"_{text}_"
    return {text[i:i + n] for i in range(len(text) - n + 1)} if len(text) >= n else {text}


def ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Compute Dice coefficient on character n-grams."""
    ngrams1 = compute_char_ngrams(text1, n)
    ngrams2 = compute_char_ngrams(text2, n)
    if not ngrams1 or not ngrams2:
        return 0.0
    intersection = len(ngrams1 & ngrams2)
    return (2.0 * intersection) / (len(ngrams1) + len(ngrams2))


def compute_orthographic_similarity(title1: str, title2: str) -> Dict[str, float]:
    """
    Compute comprehensive orthographic similarity metrics between two strings.
    """
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    
    if t1 == t2:
        return {
            "jaro_winkler": 1.0,
            "levenshtein_ratio": 1.0,
            "token_sort_ratio": 1.0,
            "ngram_sim": 1.0,
            "aggregate_orthographic_score": 1.0
        }
        
    s1, s2 = set(t1.split()), set(t2.split())
    jaccard = len(s1 & s2) / max(len(s1 | s2), 1)
    len_ratio = min(len(t1), len(t2)) / max(len(t1), len(t2))
    
    try:
        from rapidfuzz.distance import JaroWinkler, Levenshtein
        from rapidfuzz import fuzz
        
        lev = Levenshtein.normalized_similarity(t1, t2)
        raw_token_sort = fuzz.token_sort_ratio(t1, t2) / 100.0
        token_sim = raw_token_sort if jaccard >= 0.5 else raw_token_sort * (0.2 + 0.8 * jaccard)
        
        # Only use Jaro-Winkler if edit similarity is already high (>=0.70) or short single word
        if lev >= 0.70 or max(len(t1), len(t2)) <= 10:
            jw = JaroWinkler.similarity(t1, t2)
        else:
            jw = lev
            
        ng_sim = ngram_similarity(t1, t2, n=3) * (0.3 + 0.7 * jaccard)
        agg = max(lev, jw, token_sim, ng_sim)
        
        return {
            "jaro_winkler": round(jw, 4),
            "levenshtein_ratio": round(lev, 4),
            "token_sort_ratio": round(token_sim, 4),
            "ngram_sim": round(ng_sim, 4),
            "aggregate_orthographic_score": round(agg, 4)
        }
    except Exception:
        ng_sim = ngram_similarity(t1, t2, n=3)
        agg = round(max(ng_sim * len_ratio, jaccard), 4)
        
        return {
            "jaro_winkler": agg,
            "levenshtein_ratio": agg,
            "token_sort_ratio": round(jaccard, 4),
            "ngram_sim": round(ng_sim, 4),
            "aggregate_orthographic_score": agg
        }
