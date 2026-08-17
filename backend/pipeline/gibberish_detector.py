"""
PRGI Gibberish & Meaningless Word Detector

Combines:
1. Shannon Character Entropy (detects repetitive key-mashes like 'aaaaaa', 'asdfasdf')
2. Character N-Gram Transition Scoring (detects unpronounceable strings like 'ghibrisg', 'qwrtpzx')
3. Vowel-Consonant Ratio & Consonant Cluster Heuristics
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Vowels including 'y' which acts as a vowel in many contexts
VOWELS: Set[str] = set("aeiouy")
CONSONANTS: Set[str] = set("bcdfghjklmnpqrstvwxz")

# Known legitimate short acronyms (2-5 letters) commonly used in media/news
KNOWN_ACRONYMS: Set[str] = {
    "bbc", "cnn", "ndtv", "isro", "pti", "uni", "air", "ani", "aaj", "dd",
    "etv", "ht", "toi", "ibn", "abp", "tv9", "zeetv", "republic", "news18"
}

# Extremely rare or impossible English / Romanized Indian bigrams (letter pairs)
INVALID_BIGRAMS: Set[str] = {
    "bk", "bx", "bz", "cb", "cd", "cf", "cg", "cj", "cx", "cz",
    "db", "dc", "df", "dg", "dx", "fb", "fc", "fd", "fg", "fj", "fk", "fm", "fn", "fp", "fq", "fx", "fz",
    "gb", "gc", "gd", "gf", "gj", "gk", "gp", "gq", "gx", "gz",
    "hb", "hc", "hd", "hf", "hg", "hj", "hk", "hp", "hq", "hx", "hz",
    "jb", "jc", "jd", "jf", "jg", "jh", "jk", "jl", "jm", "jn", "jp", "jq", "jr", "js", "jt", "jv", "jw", "jx", "jz",
    "kx", "kz", "lx", "lz", "mx", "mz", "pb", "pc", "pd", "pf", "pj", "pq", "px", "pz",
    "qb", "qc", "qd", "qe", "qf", "qg", "qh", "qi", "qj", "qk", "ql", "qm", "qn", "qo", "qp", "qq", "qr", "qs", "qt", "qv", "qw", "qx", "qy", "qz",
    "sx", "sz", "tb", "td", "tf", "tg", "tj", "tq", "tx", "tz",
    "vb", "vc", "vd", "vf", "vg", "vh", "vj", "vk", "vm", "vp", "vq", "vx", "vz",
    "wb", "wc", "wd", "wf", "wg", "wj", "wk", "wq", "wx", "wz",
    "xb", "xc", "xd", "xf", "xg", "xh", "xj", "xk", "xl", "xm", "xn", "xp", "xq", "xr", "xs", "xt", "xv", "xw", "xx", "xz",
    "yb", "yc", "yd", "yf", "yg", "yh", "yj", "yk", "ym", "yp", "yq", "yr", "ys", "yt", "yv", "yw", "yx", "yz",
    "zb", "zc", "zd", "zf", "zg", "zh", "zj", "zk", "zl", "zm", "zn", "zp", "zq", "zr", "zs", "zt", "zv", "zw", "zx", "zy", "zz"
}

# Unlikely character combinations at the end of words
INVALID_WORD_ENDINGS: Set[str] = {
    "isg", "sg", "brsg", "rtp", "pzx", "xjgh", "zxt", "vbg", "qwr", "bgr", "tpx"
}


def compute_shannon_entropy(text: str) -> float:
    """
    Computes Shannon Entropy of character distribution in text:
    H(X) = -sum( P(x_i) * log2( P(x_i) ) )
    Lower entropy indicates repetitive patterns (e.g. 'aaaaaa', 'asdfasdf').
    """
    clean_str = [ch.lower() for ch in text if ch.isalpha()]
    if not clean_str:
        return 0.0
    
    length = len(clean_str)
    counts: Dict[str, int] = {}
    for ch in clean_str:
        counts[ch] = counts.get(ch, 0) + 1
        
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
        
    return round(entropy, 3)


def check_vowel_consonant_rules(word: str) -> Tuple[bool, Optional[str]]:
    """
    Validates word structure against consonant/vowel rules:
    - Maximum consecutive consonants
    - Minimum vowel ratio for words >= 5 letters
    """
    clean_w = word.lower().strip()
    if not clean_w or len(clean_w) <= 3:
        return True, None
        
    if clean_w in KNOWN_ACRONYMS:
        return True, None
        
    # Count maximum consecutive consonants
    max_consecutive_consonants = 0
    current_consonants = 0
    vowel_count = 0
    
    for ch in clean_w:
        if ch in VOWELS:
            vowel_count += 1
            current_consonants = 0
        elif ch in CONSONANTS:
            current_consonants += 1
            if current_consonants > max_consecutive_consonants:
                max_consecutive_consonants = current_consonants
        else:
            current_consonants = 0
            
    # Rule 1: 5 or more consecutive consonants (e.g. 'ghbrsg', 'qwrtp')
    if max_consecutive_consonants >= 5:
        return False, f"Unpronounceable consonant cluster ({max_consecutive_consonants} consecutive consonants in '{word}')."
        
    # Rule 2: 4 consecutive consonants if word length >= 6 and low vowel count
    if max_consecutive_consonants >= 4 and vowel_count <= 1 and len(clean_w) >= 6:
        return False, f"Excessive consecutive consonants with insufficient vowels in '{word}'."
        
    # Rule 3: Zero vowels in words of length >= 5
    if len(clean_w) >= 5 and vowel_count == 0:
        return False, f"No vowels detected in word '{word}'."
        
    return True, None


def check_ngram_transitions(word: str) -> Tuple[bool, Optional[str]]:
    """
    Checks character bigram and word-ending n-gram transitions for impossible/gibberish letter pairs.
    """
    clean_w = word.lower().strip()
    if len(clean_w) <= 2 or clean_w in KNOWN_ACRONYMS:
        return True, None
        
    # Check invalid endings
    for ending in INVALID_WORD_ENDINGS:
        if clean_w.endswith(ending):
            return False, f"Unusual/unpronounceable character ending '{ending}' in word '{word}'."
            
    # Count invalid bigram occurrences
    invalid_pair_count = 0
    found_invalid_pairs = []
    
    for i in range(len(clean_w) - 1):
        bigram = clean_w[i:i+2]
        if bigram in INVALID_BIGRAMS:
            invalid_pair_count += 1
            found_invalid_pairs.append(bigram)
            
    if invalid_pair_count >= 2:
        pairs_str = ", ".join(f"'{p}'" for p in set(found_invalid_pairs))
        return False, f"Multiple invalid character pairs ({pairs_str}) detected in word '{word}'."
        
    if invalid_pair_count >= 1 and len(clean_w) <= 6:
        pairs_str = ", ".join(f"'{p}'" for p in set(found_invalid_pairs))
        return False, f"Unnatural character combination '{pairs_str}' detected in word '{word}'."
        
    return True, None


def is_gibberish_word(word: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates if a single word is gibberish or meaningless using entropy, n-grams, and phonetic rules.
    Returns: (is_gibberish, error_type, reason)
    """
    clean_w = word.lower().strip()
    if not clean_w:
        return False, None, None
        
    if clean_w in KNOWN_ACRONYMS:
        return False, None, None
        
    # 1. Repetitive characters / low entropy check
    if len(clean_w) >= 5:
        # Check single repeated character (e.g. 'aaaaaa', 'zzzzzzz')
        unique_chars = set(clean_w)
        if len(unique_chars) == 1:
            char_sample = list(unique_chars)[0]
            return True, "REPETITIVE_GIBBERISH", f"Word '{word}' consists of repeated single character '{char_sample}'."
            
        # Check repeated pattern of any sub-chunk length (e.g. 'asdfasdf', 'asdfasdfasdf', 'abcabc')
        n = len(clean_w)
        for k in range(2, n // 2 + 1):
            if n % k == 0:
                chunk = clean_w[:k]
                if chunk * (n // k) == clean_w:
                    return True, "REPETITIVE_GIBBERISH", f"Word '{word}' consists of repeating pattern '{chunk}'."
            
        # Check Shannon Entropy
        entropy = compute_shannon_entropy(clean_w)
        if len(clean_w) >= 7 and entropy < 1.4:
            return True, "LOW_ENTROPY_GIBBERISH", f"Word '{word}' has unnaturally low character entropy ({entropy})."
            
    # 2. Vowel-Consonant phonetic rules
    vc_valid, vc_reason = check_vowel_consonant_rules(clean_w)
    if not vc_valid:
        return True, "UNPRONOUNCEABLE_GIBBERISH", vc_reason
        
    # 3. N-gram transition check
    ngram_valid, ngram_reason = check_ngram_transitions(clean_w)
    if not ngram_valid:
        return True, "UNPRONOUNCEABLE_GIBBERISH", ngram_reason
        
    return False, None, None


def validate_title_meaningfulness(title: str) -> Dict[str, Any]:
    """
    Main validation function for checking overall title meaningfulness.
    Returns structured validation status dict.
    """
    if not title or not title.strip():
        return {"valid": True, "error_type": None, "reason": None}
        
    # Extract alpha words from title
    words = [w.strip() for w in title.split() if w.strip()]
    
    for word in words:
        # Strip trailing/leading punctuation
        clean_w = re.sub(r"^[^\w]+|[^\w]+$", "", word)
        if not clean_w or clean_w.isdigit():
            continue
            
        is_gib, error_type, reason = is_gibberish_word(clean_w)
        if is_gib:
            return {
                "valid": False,
                "error_type": error_type,
                "flagged_word": clean_w,
                "rule": "Meaningless Word & Gibberish Prohibition",
                "guideline_ref": "PRGI Guideline on Substantive Titles",
                "reason": (
                    f"Meaningless/Gibberish Title Violation: The word '{clean_w}' in submitted title "
                    f"'{title}' was identified as random or meaningless text. {reason}"
                )
            }
            
    return {
        "valid": True,
        "error_type": None,
        "flagged_word": None,
        "rule": None,
        "guideline_ref": None,
        "reason": None
    }
