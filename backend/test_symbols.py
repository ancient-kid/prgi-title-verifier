import re
import unicodedata

def check_title_validity(raw_title: str):
    if not raw_title or not raw_title.strip():
        return {"valid": False, "reason": "Title is empty"}
        
    prohibited_symbols = []
    explicit_bad = set('+=*@#$%^&_~|\\/!?()[]{}<>;:"`©®™°•§¶†‡₹€£¥±÷×√∞')
    
    for ch in raw_title:
        cat = unicodedata.category(ch)
        # So: Symbol other (emojis, hallmarks, pictographs)
        # Sm: Symbol math (+, =, etc.)
        # Sc: Symbol currency ($, ₹, etc.)
        # Sk: Symbol modifier
        if ch in explicit_bad or cat in ('So', 'Sm', 'Sc', 'Sk'):
            if ch not in prohibited_symbols:
                prohibited_symbols.append(ch)
                
    if prohibited_symbols:
        return {
            "valid": False,
            "has_prohibited_symbols": True,
            "symbols": prohibited_symbols,
            "reason": (
                f"Titles containing non-text characters, or any form of signs, symbols including "
                f"mathematical symbols (like '+', '*', etc.), pictographs, photographs, hallmarks, logos, "
                f"monograms, phonograms, emojis, etc. are strictly prohibited under PRGI Guidelines. "
                f"(Detected prohibited characters: {', '.join(prohibited_symbols)})"
            )
        }
        
    # Check if purely numeric (digits and punctuation only, no letters)
    has_letters = any(unicodedata.category(ch).startswith('L') for ch in raw_title)
    
    if not has_letters:
        return {
            "valid": False,
            "is_purely_numeric": True,
            "reason": (
                "Numeric-Only Title Violation: Titles consisting solely of numbers, digits, or numerical figures "
                "without substantive alphabetical/text characters are strictly prohibited under PRGI Title Allocation Guidelines."
            )
        }
        
    return {"valid": True}

if __name__ == "__main__":
    test_cases = [
        "News+",
        "Daily*Express",
        "Star #1",
        "Morning News 📰",
        "12345",
        "2024",
        "24 7",
        "24 Hours News",
        "The Times of India",
        "People's Voice",
        "Indo-Asian Times",
        "दैनिक जागरण",
        "आज तक"
    ]
    for t in test_cases:
        res = check_title_validity(t)
        print(f"{t:25} -> Valid: {res.get('valid')}, Reason: {res.get('reason', 'OK')}")
