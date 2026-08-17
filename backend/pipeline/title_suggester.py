"""
Dynamic Multi-Vector AI Title Alternative Generator

Generates intelligent, context-aware, and language-tailored title alternatives
when a proposed publication title is rejected or encounters high similarity conflicts.
"""

import re
from typing import List, Dict, Any


# Language-specific prefix & suffix dictionaries
LANGUAGE_MODIFIERS = {
    "Hindi": {
        "prefixes": ["Rashtriya", "Lok", "Jan", "Pratidin", "Swadesh", "Prabhat", "Dainik", "Sanmarg"],
        "suffixes": ["Sandesh", "Varta", "Samachar", "Jagran", "Uday", "Patrika", "Vani"]
    },
    "Marathi": {
        "prefixes": ["Maharashtra", "Lok", "Jan", "Prabhat", "Dainik", "Maha"],
        "suffixes": ["Varta", "Sandesh", "Patrika", "Vrutta", "Vani", "Uday"]
    },
    "Bengali": {
        "prefixes": ["Ananda", "Pratidin", "Sangbad", "Khabar", "Bangla", "Dainik"],
        "suffixes": ["Khabar", "Patrika", "Barta", "Darpan", "Samachar"]
    },
    "Tamil": {
        "prefixes": ["Tamil", "Dina", "Kadir", "Prabha"],
        "suffixes": ["Vani", "Malar", "Velicham", "Sudhar", "Kadir"]
    },
    "Telugu": {
        "prefixes": ["Telugu", "Dina", "Praja", "Jan"],
        "suffixes": ["Vani", "Prabha", "Galam", "Jyothi", "Samachar"]
    },
    "English": {
        "prefixes": ["Vanguard", "Apex", "Zenith", "Pinnacle", "Astro", "Quantum", "Omni", "Meridian", "Stellar"],
        "suffixes": ["Chronicle", "Herald", "Observer", "Journal", "Post", "Voice", "Globe", "Courier", "Standard", "Spectrum", "Horizon"]
    }
}

# Domain & Keyword Substitution Map for blocked or blacklisted words
KEYWORD_SUBSTITUTIONS = {
    "namascar": [
        ("Abhinandan", "Replaced 'Namascar' with distinctive Sanskrit/Hindi synonym 'Abhinandan'"),
        ("Swagatam", "Replaced 'Namascar' with distinctive welcoming synonym 'Swagatam'"),
        ("Pranama", "Replaced 'Namascar' with respectful synonym 'Pranama'"),
        ("Subhashish", "Replaced 'Namascar' with auspicious synonym 'Subhashish'"),
        ("Bandhan", "Replaced 'Namascar' with community title 'Bandhan'")
    ],
    "namaskar": [
        ("Abhinandan", "Replaced 'Namaskar' with distinctive synonym 'Abhinandan'"),
        ("Swagatam", "Replaced 'Namaskar' with welcoming synonym 'Swagatam'"),
        ("Pranama", "Replaced 'Namaskar' with respectful synonym 'Pranama'"),
        ("Subhashish", "Replaced 'Namaskar' with auspicious synonym 'Subhashish'")
    ],
    "crime": [
        ("Public Truth", "Replaced prohibited security word 'Crime' with 'Public Truth'"),
        ("Satyashodhak", "Replaced prohibited term with 'Satyashodhak' (Truth Seeker)"),
        ("Vigilant Citizen", "Replaced prohibited term with 'Vigilant Citizen'"),
        ("Nyaya Mirror", "Replaced prohibited term with 'Nyaya Mirror'")
    ],
    "police": [
        ("Citizen Voice", "Replaced prohibited security word 'Police' with 'Citizen Voice'"),
        ("Jan Nayak", "Replaced prohibited authority term with 'Jan Nayak'"),
        ("Public Watchdog", "Replaced prohibited security term with 'Public Watchdog'")
    ],
    "investigation": [
        ("Fact Finder", "Replaced prohibited security term 'Investigation' with 'Fact Finder'"),
        ("Satyashodhak", "Replaced prohibited term with 'Satyashodhak'"),
        ("Transparency Journal", "Replaced prohibited term with 'Transparency Journal'")
    ],
    "hindu": [
        ("Hindustan", "Replaced conflicting brand with 'Hindustan'"),
        ("Bharat", "Replaced conflicting brand with national identifier 'Bharat'"),
        ("Rashtra", "Replaced conflicting brand with 'Rashtra'")
    ]
}


def generate_title_suggestions(
    raw_title: str,
    anchor_words: str,
    language: str,
    state: str,
    periodicity: str,
    engine_instance: Any,
    max_suggestions: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate and pre-verify dynamic, context-aware title alternatives.
    Returns a list of dicts: [{"title": str, "verification_probability": float, "category": str, "reason": str}]
    """
    if not raw_title:
        return []

    raw_clean = raw_title.strip()
    raw_title_title = raw_clean.title()
    clean_anchor = anchor_words.strip() if anchor_words else re.sub(r'[^a-zA-Z\s]', '', raw_clean).strip()
    if not clean_anchor:
        clean_anchor = raw_clean
    anchor_title = clean_anchor.title()
    low_raw = raw_clean.lower()

    candidates = []

    # -------------------------------------------------------------
    # Vector 1: Semantic Keyword Substitutions    # 1. Domain Specific Smart Synonym & Anchor Replacements
    low_raw = raw_clean.lower()
    if any(p in low_raw for p in ["crime", "police", "investigation", "cbi", "cid", "vigilance"]):
        # Strip all prohibited terms from the title string
        prohibited_words = ["crime", "police", "investigation", "cbi", "cid", "vigilance", "army", "navy"]
        clean_base = raw_title_title
        for pw in prohibited_words:
            clean_base = re.sub(r'\b' + pw + r'\b', '', clean_base, flags=re.IGNORECASE)
        clean_base = re.sub(r'\s+', ' ', clean_base).strip()
        if not clean_base or clean_base.lower() in ("the", "daily", "weekly"):
            clean_base = "Journal"

        candidates.append((f"Public Truth {clean_base}", "Semantic Substitution", "Replaced prohibited security terms with 'Public Truth'"))
        candidates.append((f"Satyashodhak {clean_base}", "Semantic Substitution", "Replaced prohibited security terms with 'Satyashodhak' (Truth Seeker)"))
        candidates.append((f"Vigilant Citizen {clean_base}", "Semantic Substitution", "Replaced prohibited security terms with 'Vigilant Citizen'"))
        candidates.append((f"Transparency {clean_base}", "Semantic Substitution", "Replaced prohibited terms with 'Transparency'"))

    if "namascar" in low_raw or "namaskar" in low_raw:
        for blocked_word, sub_list in KEYWORD_SUBSTITUTIONS.items():
            if blocked_word in low_raw:
                for sub_term, sub_reason in sub_list:
                    # Replace the blocked keyword in the raw title
                    new_title = re.sub(re.escape(blocked_word), sub_term, raw_title_title, flags=re.IGNORECASE)
                    candidates.append((new_title, "Semantic Substitution", sub_reason))

    # -------------------------------------------------------------
    # Vector 2: Language-Specific Morphological Variations
    # -------------------------------------------------------------
    lang_mods = LANGUAGE_MODIFIERS.get(language, LANGUAGE_MODIFIERS["English"])
    for pfx in lang_mods["prefixes"][:3]:
        candidates.append((f"{pfx} {anchor_title}", "Linguistic Variant", f"Added {language} prefix '{pfx}'"))
    for sfx in lang_mods["suffixes"][:3]:
        candidates.append((f"{anchor_title} {sfx}", "Linguistic Variant", f"Appended {language} modifier '{sfx}'"))

    # -------------------------------------------------------------
    # Vector 3: Geographic Boundary Scoping
    # -------------------------------------------------------------
    st_prefix = state if (state and state not in ("National", "All India", "Unknown")) else "Maharashtra"
    candidates.append((f"{st_prefix} {raw_title_title}", "Regional Scope", f"Added regional state identifier '{st_prefix}'"))
    candidates.append((f"Delhi {raw_title_title}", "Regional Scope", "Added national capital prefix 'Delhi'"))
    candidates.append((f"Bharat {anchor_title}", "Regional Scope", "Added national scope prefix 'Bharat'"))

    # -------------------------------------------------------------
    # Vector 4: High-Distinctiveness Brand Modifiers (English / Global)
    # -------------------------------------------------------------
    eng_suffixes = ["Chronicle", "Herald", "Observer", "Journal", "Post", "Horizon", "Spectrum", "Sentinel"]
    for eng_sfx in eng_suffixes:
        candidates.append((f"{anchor_title} {eng_sfx}", "Domain Brand", f"Appended distinctive modifier '{eng_sfx}'"))
        candidates.append((f"{raw_title_title} {eng_sfx}", "Domain Brand", f"Appended distinctive modifier '{eng_sfx}'"))

    # -------------------------------------------------------------
    # Vector 5: Unique Compound Anchor Formations
    # -------------------------------------------------------------
    eng_prefixes = ["Vanguard", "Apex", "Zenith", "Pinnacle", "Astro", "Quantum", "Stellar"]
    for eng_pfx in eng_prefixes:
        candidates.append((f"{eng_pfx} {anchor_title}", "Distinctive Compound", f"Prepended distinctive brand token '{eng_pfx}'"))

    evaluated_results = []
    seen_titles = set()
    seen_titles.add(raw_clean.lower())

    # Pre-verification validation loop
    for cand_title, category_tag, reason_desc in candidates:
        cand_key = cand_title.strip().lower()
        if cand_key in seen_titles:
            continue
        seen_titles.add(cand_key)

        try:
            # Self-validate candidate through pipeline (skip_suggestions=True to prevent recursion)
            res = engine_instance.verify_title(
                raw_title=cand_title,
                language=language,
                state=state,
                periodicity=periodicity,
                skip_suggestions=True
            )
            
            prob = res.get("verification_probability", 0.0)
            status = res.get("status", "")

            evaluated_results.append({
                "title": cand_title,
                "verification_probability": prob,
                "status": status,
                "category": category_tag,
                "reason": reason_desc
            })
        except Exception as e:
            print(f"[TitleSuggester] Error validating candidate '{cand_title}': {e}")
            continue

    # Sort candidates by verification probability descending
    evaluated_results.sort(key=lambda x: x["verification_probability"], reverse=True)

    # Return top N suggestions
    return evaluated_results[:max_suggestions]
