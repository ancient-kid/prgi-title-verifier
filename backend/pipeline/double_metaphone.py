"""
Lawrence Philips' Double Metaphone Algorithm (Python implementation)

Double Metaphone computes two phonetic encodings for a given word:
1. Primary key: General English pronunciation
2. Secondary key: Alternative / foreign / Anglicized pronunciation

References:
- Lawrence Philips, "The Double Metaphone Search Algorithm", C/C++ Users Journal, June 2000.
"""

import re
from typing import Tuple


def double_metaphone(word: str) -> Tuple[str, str]:
    """
    Computes (primary, secondary) Double Metaphone keys for a word.
    
    Returns:
        Tuple[str, str]: (primary_key, secondary_key)
    """
    if not word:
        return ("", "")

    # Normalize input
    clean_word = re.sub(r"[^A-Za-z]", "", word).upper()
    if not clean_word:
        return ("", "")

    length = len(clean_word)
    # Pad string to simplify bounds checks
    padded = clean_word + "    "
    
    primary = []
    secondary = []
    
    current = 0
    
    # Helper functions
    def is_vowel(pos: int) -> bool:
        if 0 <= pos < length:
            return padded[pos] in "AEIOUY"
        return False

    def string_at(start: int, match_len: int, *substrs: str) -> bool:
        if start < 0 or start >= length:
            return False
        sub = padded[start:start + match_len]
        return sub in substrs

    # Slavo-Germanic test
    is_slavo_germanic = bool(
        "W" in clean_word or "K" in clean_word or "CZ" in clean_word or "WITZ" in clean_word
    )

    # Initial letter special cases
    if string_at(0, 2, "GN", "KN", "PN", "WR", "PS"):
        current += 1
    elif string_at(0, 1, "X"):
        primary.append("S")
        secondary.append("S")
        current += 1

    while current < length:
        ch = padded[current]

        if ch in "AEIOUY":
            if current == 0:
                primary.append("A")
                secondary.append("A")
            current += 1

        elif ch == "B":
            primary.append("P")
            secondary.append("P")
            if padded[current + 1] == "B":
                current += 2
            else:
                current += 1

        elif ch == "C":
            # Various Germanic / Romanic cases
            if current > 1 and not is_vowel(current - 2) and string_at(current - 1, 3, "ACH") and \
               padded[current + 2] not in "I" and (padded[current + 2] not in "E" or string_at(current - 2, 6, "BACHER", "MACHER")):
                primary.append("K")
                secondary.append("K")
                current += 2
            elif current == 0 and string_at(current, 6, "CAESAR"):
                primary.append("S")
                secondary.append("S")
                current += 2
            elif string_at(current, 4, "CHIA"):
                primary.append("K")
                secondary.append("K")
                current += 2
            elif string_at(current, 2, "CH"):
                if current > 0 and string_at(current, 4, "CHAE"):
                    primary.append("K")
                    secondary.append("X")
                    current += 2
                elif current == 0 and (string_at(current + 1, 5, "HARAC", "HARIS") or string_at(current + 1, 3, "HOR", "HYM", "HIA", "HEM")) and not string_at(0, 5, "CHORE"):
                    primary.append("K")
                    secondary.append("K")
                    current += 2
                elif string_at(0, 4, "VAN ", "VON ") or string_at(0, 3, "SCH") or string_at(current - 2, 6, "ORCHES", "ARCHIT", "ORCHID") or \
                     string_at(current + 2, 1, "T", "S") or ((current == 0 or string_at(current - 1, 1, "A", "O", "U", "E")) and string_at(current + 2, 1, "L", "R", "N", "M", "B", "H", "F", "V", "W", " ")):
                    primary.append("K")
                    secondary.append("K")
                    current += 2
                else:
                    if current > 0:
                        if string_at(0, 2, "MC"):
                            primary.append("K")
                            secondary.append("K")
                        else:
                            primary.append("X")
                            secondary.append("K")
                    else:
                        primary.append("X")
                        secondary.append("X")
                    current += 2
            elif string_at(current, 2, "CZ") and not string_at(current - 2, 4, "WICZ"):
                primary.append("S")
                secondary.append("X")
                current += 2
            elif string_at(current + 1, 3, "CIA"):
                primary.append("X")
                secondary.append("X")
                current += 3
            elif string_at(current, 2, "CC") and not (current == 1 and padded[0] == "M"):
                if string_at(current + 2, 1, "I", "E", "H") and not string_at(current + 2, 2, "HU"):
                    if (current == 1 and padded[current - 1] == "A") or string_at(current - 1, 5, "UCCEE", "UCCES"):
                        primary.append("KS")
                        secondary.append("KS")
                    else:
                        primary.append("X")
                        secondary.append("X")
                    current += 3
                else:
                    primary.append("K")
                    secondary.append("K")
                    current += 2
            elif string_at(current, 2, "CK", "CG", "CQ"):
                primary.append("K")
                secondary.append("K")
                current += 2
            elif string_at(current, 2, "CI", "CE", "CY"):
                if string_at(current, 3, "CIO", "CIE", "CIA"):
                    primary.append("S")
                    secondary.append("X")
                else:
                    primary.append("S")
                    secondary.append("S")
                current += 2
            else:
                primary.append("K")
                secondary.append("K")
                if string_at(current + 1, 2, " C", " Q", " G"):
                    current += 3
                elif string_at(current + 1, 1, "C", "K", "Q") and not string_at(current + 1, 2, "CE", "CI"):
                    current += 2
                else:
                    current += 1

        elif ch == "D":
            if string_at(current, 2, "DG"):
                if string_at(current + 2, 1, "I", "E", "Y"):
                    primary.append("J")
                    secondary.append("J")
                    current += 3
                else:
                    primary.append("TK")
                    secondary.append("TK")
                    current += 2
            elif string_at(current, 2, "DT", "DD"):
                primary.append("T")
                secondary.append("T")
                current += 2
            else:
                primary.append("T")
                secondary.append("T")
                current += 1

        elif ch == "F":
            if padded[current + 1] == "F":
                current += 2
            else:
                current += 1
            primary.append("F")
            secondary.append("F")

        elif ch == "G":
            if padded[current + 1] == "H":
                if current > 0 and not is_vowel(current - 1):
                    primary.append("K")
                    secondary.append("K")
                    current += 2
                elif current == 0:
                    if padded[current + 2] == "I":
                        primary.append("J")
                        secondary.append("J")
                    else:
                        primary.append("K")
                        secondary.append("K")
                    current += 2
                elif (current > 1 and string_at(current - 2, 1, "B", "H", "D")) or \
                     (current > 2 and string_at(current - 3, 1, "B", "H", "D")) or \
                     (current > 3 and string_at(current - 4, 1, "B", "H")):
                    current += 2
                else:
                    if current > 2 and padded[current - 1] == "U" and string_at(current - 3, 1, "C", "G", "L", "R", "T"):
                        primary.append("F")
                        secondary.append("F")
                    elif current > 0 and padded[current - 1] != "I":
                        primary.append("K")
                        secondary.append("K")
                    current += 2
            elif padded[current + 1] == "N":
                if current == 1 and is_vowel(0) and not is_slavo_germanic:
                    primary.append("KN")
                    secondary.append("N")
                elif not string_at(current + 2, 2, "EY") and padded[current + 1] != "Y" and not is_slavo_germanic:
                    primary.append("N")
                    secondary.append("KN")
                else:
                    primary.append("KN")
                    secondary.append("KN")
                current += 2
            elif string_at(current + 1, 2, "LI") and not is_slavo_germanic:
                primary.append("KL")
                secondary.append("L")
                current += 2
            elif current == 0 and (padded[current + 1] == "Y" or string_at(current + 1, 2, "ES", "EP", "EB", "EL", "EY", "IB", "IL", "IN", "IE", "EI", "ER")):
                primary.append("K")
                secondary.append("J")
                current += 2
            elif (string_at(current + 1, 2, "ER") or padded[current + 1] == "Y") and not string_at(0, 6, "DANGER", "RANGER", "MANGER") and \
                 not string_at(current - 1, 1, "E", "I") and not string_at(current - 1, 3, "RGY", "OGY"):
                primary.append("K")
                secondary.append("J")
                current += 2
            elif string_at(current + 1, 1, "E", "I", "Y") or string_at(current - 1, 4, "AGGI", "OGGI"):
                if string_at(0, 4, "VAN ", "VON ") or string_at(0, 3, "SCH") or string_at(current + 1, 2, "ET"):
                    primary.append("K")
                    secondary.append("K")
                elif string_at(current + 1, 3, "IER"):
                    primary.append("J")
                    secondary.append("J")
                else:
                    primary.append("J")
                    secondary.append("K")
                current += 2
            else:
                if padded[current + 1] == "G":
                    current += 2
                else:
                    current += 1
                primary.append("K")
                secondary.append("K")

        elif ch == "H":
            # Keep if first char followed by vowel or between vowels
            if (current == 0 or is_vowel(current - 1)) and is_vowel(current + 1):
                primary.append("H")
                secondary.append("H")
                current += 2
            else:
                current += 1

        elif ch == "J":
            if string_at(current, 4, "JOSE") or string_at(0, 4, "SAN "):
                if (current == 0 and padded[current + 4] == " ") or string_at(0, 4, "SAN "):
                    primary.append("H")
                    secondary.append("H")
                else:
                    primary.append("J")
                    secondary.append("H")
                current += 1
            elif current == 0 and not string_at(current, 4, "JOSE"):
                primary.append("J")
                secondary.append("A")
                if padded[current + 1] == "J":
                    current += 2
                else:
                    current += 1
            elif is_vowel(current - 1) and not is_slavo_germanic and (padded[current + 1] == "A" or padded[current + 1] == "O"):
                primary.append("J")
                secondary.append("H")
                if padded[current + 1] == "J":
                    current += 2
                else:
                    current += 1
            elif current == length - 1:
                primary.append("J")
                current += 1
            else:
                if padded[current + 1] not in "LTKSNMBZ":
                    primary.append("J")
                    secondary.append("J")
                if padded[current + 1] == "J":
                    current += 2
                else:
                    current += 1

        elif ch == "K":
            if padded[current + 1] == "K":
                current += 2
            else:
                current += 1
            primary.append("K")
            secondary.append("K")

        elif ch == "L":
            if padded[current + 1] == "L":
                if (current == length - 3 and string_at(current - 1, 4, "ILLO", "ILLA", "ALLE")) or \
                   ((string_at(length - 2, 2, "AS", "OS") or string_at(length - 1, 1, "A", "O")) and string_at(current - 1, 4, "ALLE")):
                    primary.append("L")
                    current += 2
                else:
                    primary.append("L")
                    secondary.append("L")
                    current += 2
            else:
                current += 1
                primary.append("L")
                secondary.append("L")

        elif ch == "M":
            if (string_at(current - 1, 3, "UMB") and (current + 1 == length - 1 or string_at(current + 2, 2, "ER"))) or padded[current + 1] == "M":
                current += 2
            else:
                current += 1
            primary.append("M")
            secondary.append("M")

        elif ch == "N":
            if padded[current + 1] == "N":
                current += 2
            else:
                current += 1
            primary.append("N")
            secondary.append("N")

        elif ch == "P":
            if padded[current + 1] == "H":
                primary.append("F")
                secondary.append("F")
                current += 2
            elif padded[current + 1] in "PB":
                current += 2
                primary.append("P")
                secondary.append("P")
            else:
                current += 1
                primary.append("P")
                secondary.append("P")

        elif ch == "Q":
            if padded[current + 1] == "Q":
                current += 2
            else:
                current += 1
            primary.append("K")
            secondary.append("K")

        elif ch == "R":
            if current == length - 1 and not is_slavo_germanic and string_at(current - 2, 2, "IE") and not string_at(current - 4, 2, "ME", "RA"):
                secondary.append("R")
            else:
                primary.append("R")
                secondary.append("R")
            if padded[current + 1] == "R":
                current += 2
            else:
                current += 1

        elif ch == "S":
            if string_at(current - 1, 3, "ISL", "YSL"):
                current += 1
            elif current == 0 and string_at(current, 5, "SUGAR"):
                primary.append("X")
                secondary.append("S")
                current += 1
            elif string_at(current, 2, "SH"):
                if string_at(current + 1, 4, "HEIM", "HOEK", "HOLM", "HOLZ"):
                    primary.append("S")
                    secondary.append("S")
                else:
                    primary.append("X")
                    secondary.append("X")
                current += 2
            elif string_at(current, 3, "SIO", "SIA") or string_at(current, 4, "SIAN"):
                if not is_slavo_germanic:
                    primary.append("S")
                    secondary.append("X")
                else:
                    primary.append("S")
                    secondary.append("S")
                current += 3
            elif (current == 0 and string_at(current + 1, 1, "M", "N", "L", "W")) or string_at(current + 1, 1, "Z"):
                primary.append("S")
                secondary.append("X")
                if string_at(current + 1, 1, "Z"):
                    current += 2
                else:
                    current += 1
            elif string_at(current, 2, "SC"):
                if padded[current + 2] == "H":
                    if string_at(current + 3, 2, "OO", "ER", "EN", "UY", "ED", "EM"):
                        if string_at(current + 3, 2, "ER", "EN"):
                            primary.append("X")
                            secondary.append("SK")
                        else:
                            primary.append("SK")
                            secondary.append("SK")
                        current += 3
                    else:
                        if current == 0 and not is_vowel(3) and padded[3] != "W":
                            primary.append("X")
                            secondary.append("S")
                        else:
                            primary.append("X")
                            secondary.append("X")
                        current += 3
                elif string_at(current + 2, 1, "I", "E", "Y"):
                    primary.append("S")
                    secondary.append("S")
                    current += 3
                else:
                    primary.append("SK")
                    secondary.append("SK")
                    current += 3
            elif current == length - 1 and string_at(current - 2, 2, "AI", "OI"):
                secondary.append("S")
                current += 1
            else:
                primary.append("S")
                secondary.append("S")
                if string_at(current + 1, 1, "S", "Z"):
                    current += 2
                else:
                    current += 1

        elif ch == "T":
            if string_at(current, 4, "TION") or string_at(current, 3, "TIA", "TCH"):
                primary.append("X")
                secondary.append("X")
                current += 3
            elif string_at(current, 2, "TH") or string_at(current, 3, "TTH"):
                if string_at(current + 2, 2, "OM", "AM") or string_at(0, 4, "VAN ", "VON ") or string_at(0, 3, "SCH"):
                    primary.append("T")
                    secondary.append("T")
                else:
                    primary.append("0")  # 0 represents theta / TH sound in Double Metaphone
                    secondary.append("T")
                current += 2
            elif string_at(current + 1, 1, "T", "D"):
                current += 2
                primary.append("T")
                secondary.append("T")
            else:
                current += 1
                primary.append("T")
                secondary.append("T")

        elif ch == "V":
            if padded[current + 1] == "V":
                current += 2
            else:
                current += 1
            primary.append("F")
            secondary.append("F")

        elif ch == "W":
            if string_at(current, 2, "WR"):
                primary.append("R")
                secondary.append("R")
                current += 2
            elif current == 0 and (is_vowel(current + 1) or string_at(current, 2, "WH")):
                if is_vowel(current + 1):
                    primary.append("A")
                    secondary.append("F")
                else:
                    primary.append("A")
                    secondary.append("A")
                current += 1
            elif (current == length - 1 and is_vowel(current - 1)) or string_at(current - 1, 5, "EWSKI", "EWSKY", "OWSKI", "OWSKY") or string_at(0, 3, "SCH"):
                secondary.append("F")
                current += 1
            elif string_at(current, 4, "WICZ", "WITZ"):
                primary.append("TS")
                secondary.append("FX")
                current += 4
            else:
                current += 1

        elif ch == "X":
            if not (current == length - 1 and (string_at(current - 3, 3, "IAU", "EAU") or string_at(current - 2, 2, "AU", "OU"))):
                primary.append("KS")
                secondary.append("KS")
            if string_at(current + 1, 1, "C", "X"):
                current += 2
            else:
                current += 1

        elif ch == "Z":
            if padded[current + 1] == "H":
                primary.append("J")
                secondary.append("J")
                current += 2
            elif string_at(current + 1, 2, "ZO", "ZI", "ZA") or (is_slavo_germanic and current > 0 and padded[current - 1] != "T"):
                primary.append("S")
                secondary.append("TS")
                current += 1
            else:
                primary.append("S")
                secondary.append("S")
                if padded[current + 1] == "Z":
                    current += 2
                else:
                    current += 1
        else:
            current += 1

    prim_str = "".join(primary)[:8]
    sec_str = "".join(secondary if secondary else primary)[:8]
    
    return (prim_str, sec_str)
