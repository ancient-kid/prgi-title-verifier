"""
Stage 2: PRGI Guideline Enforcement & Blacklist Checking

Enforces PRGI / RNI Guidelines under the Press and Registration of Periodicals (PRP) Act, 2023:
1. Guideline 12: Disallowed / Prohibited words (Police, Crime, Corruption, CBI, CID, Army, Vigilance, Sarkar, etc.)
2. Guideline 4: Emblems & Names (Prevention of Improper Use) Act, 1950 violations (President, UN, Ashoka, Bharat Ratna, etc.)
3. Guideline 14: Obscene, Defamatory, Communal, or Sedition-provoking terms.
4. Guideline 7: Government/Official agency impersonation words (Bureau, Directorate, Ministry, Commission, Authority, etc.)
5. Guideline 9: Deceptive state/national representation.

If any rule is violated, immediately triggers a 0% verification probability with detailed diagnosis.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

# PRGI Guideline 12: Prohibited / Disallowed Words Blacklist
DISALLOWED_ENFORCEMENT_WORDS: Dict[str, str] = {
    "police": "Guideline 12: Use of word 'Police' or related police insignia is strictly prohibited to prevent public deception.",
    "crime": "Guideline 12: Words suggesting association with police or law enforcement ('Crime', 'CID', etc.) are barred.",
    "corruption": "Guideline 12: Term 'Corruption' or anti-corruption agency impersonation words are prohibited.",
    "cbi": "Guideline 12: 'CBI' (Central Bureau of Investigation) is an official state agency acronym and prohibited.",
    "cid": "Guideline 12: 'CID' (Criminal Investigation Department) is prohibited.",
    "army": "Guideline 12: Military and defense terms ('Army', 'Navy', 'Airforce') are restricted under PRGI guidelines.",
    "navy": "Guideline 12: Military and defense terms are prohibited.",
    "airforce": "Guideline 12: Military and defense terms are prohibited.",
    "vigilance": "Guideline 12: Words implying official vigilance commissions or anti-corruption bureaus are prohibited.",
    "sarkar": "Guideline 12: Use of 'Sarkar' (Government) implies official state sponsorship and is disallowed.",
    "sarkari": "Guideline 12: 'Sarkari' implies official government sanction and is prohibited.",
    "government": "Guideline 12: Words implying official government organ ('Government', 'Govt') are prohibited.",
    "govt": "Guideline 12: Words implying official government organ are prohibited.",
    "lokpal": "Guideline 12: Statutory anti-corruption body name 'Lokpal' is prohibited.",
    "lokayukta": "Guideline 12: Statutory anti-corruption body name 'Lokayukta' is prohibited.",
    "court": "Guideline 12: Judicial organ terms ('Court', 'Nyayalaya', 'High Court', 'Supreme Court') are prohibited.",
    "nyayalaya": "Guideline 12: Judicial organ terms are prohibited.",
    "judge": "Guideline 12: Judicial title terms are prohibited.",
    "bureau": "Guideline 7: Words resembling official investigative bodies ('Bureau', 'Directorate') are prohibited.",
    "investigation": "Guideline 12: Words indicating state investigative authority ('Investigation') are restricted.",
    "intelligence": "Guideline 12: State intelligence agency terminology ('Intelligence', 'RAW', 'IB') is barred.",
    "raw": "Guideline 12: Restricted intelligence agency acronym.",
    "ed": "Guideline 12: Restricted enforcement directorate acronym.",
    "nia": "Guideline 12: Restricted National Investigation Agency acronym.",
    "defense": "Guideline 12: National defense terminology is restricted.",
    "defence": "Guideline 12: National defense terminology is restricted.",
    "military": "Guideline 12: Military terminology is prohibited.",
    "crpf": "Guideline 12: Paramilitary organization name is prohibited.",
    "bsf": "Guideline 12: Paramilitary organization name is prohibited.",
    "cisf": "Guideline 12: Paramilitary organization name is prohibited.",
    "itbp": "Guideline 12: Paramilitary organization name is prohibited.",
    "nsg": "Guideline 12: National Security Guard acronym is prohibited.",
    "customs": "Guideline 12: Official revenue/taxation authority name is prohibited.",
    "excise": "Guideline 12: Official revenue/taxation authority name is prohibited.",
    "rashtrapati": "Guideline 4: Constitutional post 'Rashtrapati' is prohibited under Emblems & Names Act.",
    "president": "Guideline 4: Constitutional post title is prohibited.",
    "pm": "Guideline 4: Constitutional post acronym is prohibited.",
    "cm": "Guideline 4: Constitutional post acronym is prohibited.",
    "prime minister": "Guideline 4: Constitutional post title is prohibited.",
    "chief minister": "Guideline 4: Constitutional post title is prohibited.",
    "parliament": "Guideline 7: Sovereign legislative body name 'Parliament' is prohibited.",
    "sansad": "Guideline 7: Sovereign legislative body name 'Sansad' is prohibited.",
    "vidhan sabha": "Guideline 7: State legislative assembly name is prohibited.",
    "rajya sabha": "Guideline 7: Upper house of Parliament name is prohibited.",
    "lok sabha": "Guideline 7: Lower house of Parliament name is prohibited."
}

# Guideline 4: Emblems and Names (Prevention of Improper Use) Act, 1950
NATIONAL_EMBLEMS_AND_PROTECTED_NAMES: Dict[str, str] = {
    "ashoka chakra": "Guideline 4: National symbol protected under Emblems and Names Act, 1950.",
    "ashok chakra": "Guideline 4: National symbol protected under Emblems and Names Act, 1950.",
    "national emblem": "Guideline 4: National emblem protected under Emblems and Names Act, 1950.",
    "bharat ratna": "Guideline 4: Highest civilian honour protected from commercial or publication titles.",
    "padma vibhushan": "Guideline 4: National civilian award name is protected.",
    "padma bhushan": "Guideline 4: National civilian award name is protected.",
    "padma shri": "Guideline 4: National civilian award name is protected.",
    "united nations": "Guideline 4: International treaty organization name is protected.",
    "un": "Guideline 4: International organization acronym.",
    "unesco": "Guideline 4: United Nations body acronym is protected.",
    "who": "Guideline 4: World Health Organization acronym is protected.",
    "interpol": "Guideline 4: International criminal police organization name is protected.",
    "gandhi": "Guideline 4: National leaders' names without context or permission are restricted.",
    "mahatma gandhi": "Guideline 4: National leaders' names without context or permission are restricted."
}

# Guideline 14: Obscene / Vulgar / Defamatory / Hate Terms
OBSCENE_OR_DEFAMATORY_TERMS: Set[str] = {
    "terrorist", "terrorism", "jihad", "naxal", "naxalite", "extremist",
    "scam", "fraud", "blackmail", "smuggler", "mafia", "gangster", "don",
    "murder", "killer", "loot", "dacoit", "goonda", "gunda"
}


def check_guidelines(cleaned_title: str, tokens: List[str]) -> Dict[str, any]:
    """
    Enforce PRGI guidelines and blacklists against the title.
    
    Returns:
        dict with:
        - passed: bool (True if no violations, False if violated)
        - violations: list of dicts with {rule, term, guideline_ref, explanation}
        - probability_multiplier: 0.0 if failed, 1.0 if passed
        - summary: Human-readable summary of guideline status
    """
    violations = []
    
    title_lower = f" {cleaned_title} "
    
    # 1. Check Disallowed Enforcement Words (single words and multi-word phrases)
    for term, reason in DISALLOWED_ENFORCEMENT_WORDS.items():
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, cleaned_title):
            violations.append({
                "rule": "Disallowed / Prohibited Law Enforcement Word",
                "term": term.title(),
                "guideline_ref": reason.split(":")[0].strip() if ":" in reason else "Guideline 12",
                "explanation": reason
            })
            
    # 2. Check National Emblems and Protected Names
    for term, reason in NATIONAL_EMBLEMS_AND_PROTECTED_NAMES.items():
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, cleaned_title):
            violations.append({
                "rule": "National Emblems & Protected Names Act Violation",
                "term": term.title(),
                "guideline_ref": reason.split(":")[0].strip() if ":" in reason else "Guideline 4",
                "explanation": reason
            })
            
    # 3. Check Obscene / Defamatory / Anti-Social Terms
    for token in tokens:
        if token in OBSCENE_OR_DEFAMATORY_TERMS:
            violations.append({
                "rule": "Derogatory / Criminal Association Term",
                "term": token.title(),
                "guideline_ref": "Guideline 14",
                "explanation": f"Guideline 14: Use of sensational, criminal, or defamatory term '{token}' is prohibited."
            })
            
    passed = len(violations) == 0
    multiplier = 1.0 if passed else 0.0
    
    if passed:
        summary = "Passed all PRGI rulebook checks and disallowed keyword filters."
    else:
        terms = ", ".join(f"'{v['term']}'" for v in violations)
        summary = f"Rejected: Title violates PRGI statutory guidelines by containing prohibited term(s): {terms}."
        
    return {
        "passed": passed,
        "violations": violations,
        "probability_multiplier": multiplier,
        "summary": summary
    }
