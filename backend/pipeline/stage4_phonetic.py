"""
Stage 4A: Phonetic Similarity Engine

Uses Double Metaphone (English) and Indic Phonetic Mapping / Indic-Soundex to convert
titles into phonetic token codes.

Catches deceptive phonetic copies, homophones, spelling variations:
- "Namascar" vs "Namaskar" -> 100% phonetic match
- "Dainik" vs "Daineq" vs "Daynik" -> 100% phonetic match
- "Bharat" vs "Bhaarat" vs "Bharath" -> 100% phonetic match
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Indic phonetic transliteration character normalization table
INDIC_PHONETIC_MAP = [
    (r"sh[h]?", "SH"),
    (r"ch[h]?", "CH"),
    (r"kh", "K"),
    (r"gh", "G"),
    (r"th", "T"),
    (r"dh", "D"),
    (r"bh", "B"),
    (r"ph", "F"),
    (r"ee|oo|aa|ii|uu", lambda m: m.group(0)[0]),
    (r"v", "W"),
    (r"w", "W"),
    (r"q", "K"),
    (r"c(?=[eiy])", "S"),
    (r"c", "K"),
    (r"z", "J"),
    (r"x", "KS")
]


def indic_soundex(word: str) -> str:
    """
    Computes an Indic-tailored phonetic soundex representation for Indian words / transliterated titles.
    """
    if not word:
        return ""
    word = word.lower().strip()
    
    s = word
    for pattern, replacement in INDIC_PHONETIC_MAP:
        if callable(replacement):
            s = re.sub(pattern, replacement, s)
        else:
            s = re.sub(pattern, replacement.lower(), s)
            
    s = re.sub(r"[^a-z]", "", s)
    if not s:
        return ""
        
    first_char = s[0].upper()
    
    mapping = {
        'b': '1', 'f': '1', 'p': '1', 'v': '1', 'w': '1',
        'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
        'd': '3', 't': '3',
        'l': '4',
        'm': '5', 'n': '5',
        'r': '6'
    }
    
    encoded = [first_char]
    prev_code = mapping.get(s[0], '')
    
    for char in s[1:]:
        code = mapping.get(char, '')
        if code:
            if code != prev_code:
                encoded.append(code)
                prev_code = code
        else:
            prev_code = ''
            
    code_str = "".join(encoded)
    return (code_str + "0000")[:5]


def get_double_metaphone(word: str) -> Tuple[str, str]:
    """
    Returns (primary, secondary) Double Metaphone keys for English words.
    """
    try:
        import jellyfish
        res = jellyfish.metaphone(word)
        return res, res
    except Exception:
        clean = re.sub(r"[^a-zA-Z]", "", word).upper()
        if not clean:
            return "", ""
        vowels = "AEIOU"
        skeleton = clean[0] + "".join([c for c in clean[1:] if c not in vowels])
        return skeleton[:6], skeleton[:6]


def compute_phonetic_fingerprint(title: str) -> Dict[str, Any]:
    """
    Generate phonetic fingerprint for a given title.
    """
    words = [w for w in re.sub(r"[^\w\s]", " ", title).lower().split() if w]
    meta_keys = []
    indic_keys = []
    
    for w in words:
        primary, _ = get_double_metaphone(w)
        if primary:
            meta_keys.append(primary)
        ind_code = indic_soundex(w)
        if ind_code:
            indic_keys.append(ind_code)
            
    return {
        "title": title,
        "metaphone_tokens": meta_keys,
        "metaphone_str": " ".join(meta_keys),
        "indic_soundex_tokens": indic_keys,
        "indic_soundex_str": "-".join(indic_keys)
    }


def compare_phonetic_similarity(title1: str, title2: str) -> float:
    """
    Compute token-aligned phonetic similarity score [0.0 to 1.0] between two titles.
    """
    if not title1 or not title2:
        return 0.0
        
    w1 = [w for w in re.sub(r"[^\w\s]", " ", title1).lower().split() if w]
    w2 = [w for w in re.sub(r"[^\w\s]", " ", title2).lower().split() if w]
    
    if not w1 or not w2:
        return 0.0
        
    # Exact full match
    if " ".join(w1) == " ".join(w2):
        return 1.0
        
    try:
        from rapidfuzz.distance import JaroWinkler
    except Exception:
        JaroWinkler = None

    m1 = [get_double_metaphone(w)[0] for w in w1]
    m2 = [get_double_metaphone(w)[0] for w in w2]
    
    s1 = [indic_soundex(w) for w in w1]
    s2 = [indic_soundex(w) for w in w2]

    # Check exact metaphone string match
    m1_str = " ".join([m for m in m1 if m])
    m2_str = " ".join([m for m in m2 if m])
    if m1_str and m1_str == m2_str:
        char_sim = JaroWinkler.similarity(" ".join(w1), " ".join(w2)) if JaroWinkler else 0.8
        if char_sim >= 0.70:
            return 1.0


    # Token-level bipartite alignment matching
    used_indices = set()
    total_token_match_score = 0.0

    for i in range(len(w1)):
        tok_m1 = m1[i]
        tok_s1 = s1[i]
        
        best_score = 0.0
        best_j = -1
        
        for j in range(len(w2)):
            if j in used_indices:
                continue
                
            tok_m2 = m2[j]
            tok_s2 = s2[j]
            
            score = 0.0
            
            # Exact metaphone match
            if tok_m1 and tok_m2 and tok_m1 == tok_m2:
                char_sim = JaroWinkler.similarity(w1[i], w2[j]) if JaroWinkler else 0.8
                if char_sim >= 0.70:
                    score = 1.0
                else:
                    score = 0.50
            # Exact Indic soundex match
            elif tok_s1 and tok_s2 and tok_s1 == tok_s2:
                char_sim = JaroWinkler.similarity(w1[i], w2[j]) if JaroWinkler else 0.8
                if char_sim >= 0.70:
                    score = 0.95
                else:
                    score = 0.40
            elif JaroWinkler:
                sim_m = JaroWinkler.similarity(tok_m1, tok_m2) if tok_m1 and tok_m2 else 0.0
                sim_s = JaroWinkler.similarity(tok_s1, tok_s2) if tok_s1 and tok_s2 else 0.0
                max_sim = max(sim_m, sim_s)
                # Only consider high similarity (> 0.85)
                if max_sim >= 0.85:
                    score = max_sim
                    
            if score > best_score:
                best_score = score
                best_j = j
                if score >= 1.0:
                    break
                    
        if best_j != -1 and best_score >= 0.80:
            used_indices.add(best_j)
            total_token_match_score += best_score

    max_len = max(len(w1), len(w2))
    overall_sim = total_token_match_score / max_len if max_len > 0 else 0.0
    return round(overall_sim, 4)
