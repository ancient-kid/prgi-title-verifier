"""
Stage 4A: Phonetic Similarity Engine

Uses Double Metaphone (English/foreign pronunciations), Indic Phonetic Normalization,
and Indic-Soundex to convert titles into phonetic token representations and compute
bipartite token-aligned phonetic similarity.

Catches deceptive phonetic copies, homophones, and Romanized Indian language spelling variations:
- "Namascar" vs "Namaskar" -> 100% phonetic match
- "Dainik" vs "Daineq" vs "Daynik" -> 100% phonetic match
- "Bharat" vs "Bhaarat" vs "Bharath" -> 100% phonetic match
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.config import (
    PHONETIC_MATCH_THRESHOLD,
    PHONETIC_SHORT_WORD_MAX_LEN,
    PHONETIC_SHORT_WORD_MIN_CHAR_SIM,
)
from backend.pipeline.double_metaphone import double_metaphone

# Ordered transformation rules for Romanized Indic phonetic normalization
INDIC_PHONETIC_TRANSFORMATIONS: List[Tuple[str, str]] = [
    # 1. Multi-character aspirates and digraphs
    (r"sh[h]?", "s"),
    (r"ch[h]?", "c"),
    (r"kh", "k"),
    (r"gh", "g"),
    (r"th", "t"),
    (r"dh", "d"),
    (r"bh", "b"),
    (r"ph", "f"),
    # 2. Elongated vowels normalized to single vowel
    (r"aa+", "a"),
    (r"ee+", "i"),
    (r"ii+", "i"),
    (r"oo+", "u"),
    (r"uu+", "u"),
    (r"ay", "e"),
    (r"ai", "e"),
    (r"au", "o"),
    (r"ou", "o"),
    # 3. Consonant equivalences
    (r"v", "w"),
    (r"q", "k"),
    (r"c(?=[eiy])", "s"),
    (r"c", "k"),
    (r"z", "j"),
    (r"x", "ks"),
]


def normalize_indic_phonetic(word: str) -> str:
    """
    Applies deterministic, ordered transliteration normalization rules for
    Romanized Indian language words.
    
    Transforms common spelling variations (aspirates, double vowels, interchangeable
    consonants like v/w, q/k, sh/s) into canonical phonetic representations.
    """
    if not word:
        return ""
    s = word.lower().strip()
    for pattern, replacement in INDIC_PHONETIC_TRANSFORMATIONS:
        s = re.sub(pattern, replacement, s)
    return re.sub(r"[^a-z]", "", s)


def indic_soundex(word: str) -> str:
    """
    Computes an Indic-tailored phonetic Soundex code (5 characters: 1 letter + 4 digits).
    
    Consonant Classes:
        1: B, F, P, V, W
        2: C, G, J, K, Q, S, X, Z
        3: D, T
        4: L
        5: M, N
        6: R
    
    Vowels (A, E, I, O, U, Y) and H act as separators that reset adjacency
    without emitting a digit.
    """
    if not word:
        return ""
    
    # Pre-normalize with Indic phonetic transformations
    normalized = normalize_indic_phonetic(word)
    if not normalized:
        return ""
        
    first_char = normalized[0].upper()
    
    mapping = {
        'b': '1', 'f': '1', 'p': '1', 'v': '1', 'w': '1',
        'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
        'd': '3', 't': '3',
        'l': '4',
        'm': '5', 'n': '5',
        'r': '6'
    }
    
    encoded = [first_char]
    prev_code = mapping.get(normalized[0], '')
    
    for char in normalized[1:]:
        code = mapping.get(char, '')
        if code:
            if code != prev_code:
                encoded.append(code)
                prev_code = code
        else:
            # Vowels and unmapped letters reset the consecutive code tracker
            prev_code = ''
            
    code_str = "".join(encoded)
    return (code_str + "0000")[:5]


def get_double_metaphone(word: str) -> Tuple[str, str]:
    """
    Returns (primary, secondary) Double Metaphone keys for a given word.
    Uses Lawrence Philips' algorithm with full English and foreign sound handling.
    """
    return double_metaphone(word)


def compute_phonetic_fingerprint(title: str) -> Dict[str, Any]:
    """
    Generate complete phonetic fingerprint containing Double Metaphone and
    Indic-Soundex representations for all tokens in a title.
    """
    words = [w for w in re.sub(r"[^\w\s]", " ", title).lower().split() if w]
    meta_primary = []
    meta_secondary = []
    indic_keys = []
    
    for w in words:
        prim, sec = get_double_metaphone(w)
        if prim:
            meta_primary.append(prim)
        if sec:
            meta_secondary.append(sec)
        ind_code = indic_soundex(w)
        if ind_code:
            indic_keys.append(ind_code)
            
    return {
        "title": title,
        "metaphone_primary_tokens": meta_primary,
        "metaphone_secondary_tokens": meta_secondary,
        "metaphone_str": " ".join(meta_primary),
        "indic_soundex_tokens": indic_keys,
        "indic_soundex_str": "-".join(indic_keys)
    }


def compare_phonetic_similarity_detailed(title1: str, title2: str) -> Dict[str, Any]:
    """
    Computes bipartite token-aligned phonetic similarity between two titles and
    returns a comprehensive diagnostic breakdown.
    
    Returns:
        Dict containing:
            - score: float [0.0, 1.0]
            - title1_tokens: List[str]
            - title2_tokens: List[str]
            - matched_tokens: List[Dict[str, Any]]
            - phonetic_keys: Dict[str, Any]
            - indic_soundex_keys: Dict[str, Any]
            - reason: str
    """
    if not title1 or not title2:
        return {
            "score": 0.0,
            "title1_tokens": [],
            "title2_tokens": [],
            "matched_tokens": [],
            "phonetic_keys": {"title1": [], "title2": []},
            "indic_soundex_keys": {"title1": [], "title2": []},
            "reason": "Empty title provided"
        }
        
    w1 = [w for w in re.sub(r"[^\w\s]", " ", title1).lower().split() if w]
    w2 = [w for w in re.sub(r"[^\w\s]", " ", title2).lower().split() if w]
    
    if not w1 or not w2:
        return {
            "score": 0.0,
            "title1_tokens": w1,
            "title2_tokens": w2,
            "matched_tokens": [],
            "phonetic_keys": {"title1": [], "title2": []},
            "indic_soundex_keys": {"title1": [], "title2": []},
            "reason": "No valid tokens found"
        }
        
    # Exact normalized token string equality
    if " ".join(w1) == " ".join(w2):
        dm1 = [get_double_metaphone(w) for w in w1]
        s1 = [indic_soundex(w) for w in w1]
        return {
            "score": 1.0,
            "title1_tokens": w1,
            "title2_tokens": w2,
            "matched_tokens": [{"t1": w, "t2": w, "match_type": "exact", "score": 1.0} for w in w1],
            "phonetic_keys": {"title1": dm1, "title2": dm1},
            "indic_soundex_keys": {"title1": s1, "title2": s1},
            "reason": "Exact token match"
        }
        
    try:
        from rapidfuzz.distance import JaroWinkler, Levenshtein
    except Exception:
        JaroWinkler = None
        Levenshtein = None

    dm1 = [get_double_metaphone(w) for w in w1]
    dm2 = [get_double_metaphone(w) for w in w2]
    
    s1 = [indic_soundex(w) for w in w1]
    s2 = [indic_soundex(w) for w in w2]

    # Check whole-title exact metaphone equality
    m1_prim_str = " ".join([p for p, _ in dm1 if p])
    m2_prim_str = " ".join([p for p, _ in dm2 if p])
    
    if m1_prim_str and m1_prim_str == m2_prim_str:
        s1_str = " ".join(w1)
        s2_str = " ".join(w2)
        char_sim = JaroWinkler.similarity(s1_str, s2_str) if JaroWinkler else 0.8
        lev_sim = Levenshtein.normalized_similarity(s1_str, s2_str) if Levenshtein else 0.8
        
        # Short-word safeguard (e.g. bat/bet, pan/pin)
        max_title_len = max(len(s1_str), len(s2_str))
        if max_title_len <= PHONETIC_SHORT_WORD_MAX_LEN:
            if char_sim >= PHONETIC_SHORT_WORD_MIN_CHAR_SIM or lev_sim >= 0.80:
                score = 1.0
            else:
                score = round(max(char_sim, lev_sim) * 0.5, 4)
        elif char_sim >= 0.70:
            score = 1.0
        else:
            score = round(max(char_sim, 0.75), 4)

        if score >= 0.70:
            return {
                "score": score,
                "title1_tokens": w1,
                "title2_tokens": w2,
                "matched_tokens": [{"t1": w1[i], "t2": w2[i], "match_type": "metaphone_exact", "score": score} for i in range(min(len(w1), len(w2)))],
                "phonetic_keys": {"title1": dm1, "title2": dm2},
                "indic_soundex_keys": {"title1": s1, "title2": s2},
                "reason": f"Full Double Metaphone match ({m1_prim_str})"
            }

    # Bipartite token-level matching
    used_indices: Set[int] = set()
    matched_pairs: List[Dict[str, Any]] = []
    total_token_match_score = 0.0

    for i in range(len(w1)):
        p1, sec1 = dm1[i]
        ind1 = s1[i]
        
        best_score = 0.0
        best_j = -1
        best_match_type = "none"
        
        for j in range(len(w2)):
            if j in used_indices:
                continue
                
            p2, sec2 = dm2[j]
            ind2 = s2[j]
            
            score = 0.0
            match_type = "none"
            word_len = max(len(w1[i]), len(w2[j]))
            char_sim = JaroWinkler.similarity(w1[i], w2[j]) if JaroWinkler else 0.8
            lev_sim = Levenshtein.normalized_similarity(w1[i], w2[j]) if Levenshtein else 0.8
            
            # 1. Double Metaphone Primary - Primary
            if p1 and p2 and p1 == p2:
                match_type = "dm_primary_primary"
                if word_len <= PHONETIC_SHORT_WORD_MAX_LEN:
                    if char_sim >= PHONETIC_SHORT_WORD_MIN_CHAR_SIM or lev_sim >= 0.80:
                        score = 1.0
                    else:
                        score = 0.35  # Distinguish minimal vowel pairs like bat/bet
                elif char_sim >= 0.70:
                    score = 1.0
                else:
                    score = 0.75
            # 2. Double Metaphone Primary - Secondary / Secondary - Primary
            elif (p1 and sec2 and p1 == sec2) or (sec1 and p2 and sec1 == p2):
                match_type = "dm_cross_secondary"
                if word_len <= PHONETIC_SHORT_WORD_MAX_LEN:
                    score = 0.90 if (char_sim >= PHONETIC_SHORT_WORD_MIN_CHAR_SIM or lev_sim >= 0.80) else 0.30
                elif char_sim >= 0.70:
                    score = 0.90
                else:
                    score = 0.65
            # 3. Double Metaphone Secondary - Secondary
            elif sec1 and sec2 and sec1 == sec2:
                match_type = "dm_secondary_secondary"
                if word_len <= PHONETIC_SHORT_WORD_MAX_LEN:
                    score = 0.85 if (char_sim >= PHONETIC_SHORT_WORD_MIN_CHAR_SIM or lev_sim >= 0.80) else 0.25
                else:
                    score = 0.85
            # 4. Indic-Soundex Match
            elif ind1 and ind2 and ind1 == ind2:
                match_type = "indic_soundex"
                if word_len <= PHONETIC_SHORT_WORD_MAX_LEN:
                    if char_sim >= PHONETIC_SHORT_WORD_MIN_CHAR_SIM or lev_sim >= 0.80:
                        score = 0.95
                    else:
                        score = 0.30
                elif char_sim >= 0.70:
                    score = 0.95
                else:
                    score = 0.50
            # 5. Indic Normalization Exact Match
            elif normalize_indic_phonetic(w1[i]) == normalize_indic_phonetic(w2[j]):
                match_type = "indic_normalized"
                score = 0.95
            # 6. Fuzzy Metaphone Match
            elif JaroWinkler and p1 and p2:
                sim_m = JaroWinkler.similarity(p1, p2)
                if sim_m >= 0.88 and char_sim >= 0.75:
                    match_type = "dm_fuzzy"
                    score = sim_m * 0.90
                    
            if score > best_score:
                best_score = score
                best_j = j
                best_match_type = match_type
                if score >= 1.0:
                    break
                    
        if best_j != -1 and best_score >= 0.60:
            used_indices.add(best_j)
            total_token_match_score += best_score
            matched_pairs.append({
                "t1": w1[i],
                "t2": w2[best_j],
                "match_type": best_match_type,
                "score": round(best_score, 4)
            })

    max_len = max(len(w1), len(w2))
    overall_sim = total_token_match_score / max_len if max_len > 0 else 0.0
    overall_sim = round(min(1.0, max(0.0, overall_sim)), 4)
    
    reason_desc = (
        f"{len(matched_pairs)} token(s) phonetically aligned across titles"
        if matched_pairs else "No strong phonetic alignments found"
    )
    
    return {
        "score": overall_sim,
        "title1_tokens": w1,
        "title2_tokens": w2,
        "matched_tokens": matched_pairs,
        "phonetic_keys": {"title1": dm1, "title2": dm2},
        "indic_soundex_keys": {"title1": s1, "title2": s2},
        "reason": reason_desc
    }


def compare_phonetic_similarity(title1: str, title2: str) -> float:
    """
    Backwards-compatible API returning scalar phonetic similarity score in [0.0, 1.0].
    """
    res = compare_phonetic_similarity_detailed(title1, title2)
    return res["score"]
