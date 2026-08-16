"""
Protected Names Registry for Corporate Brands, Copyrights, and Organizations.
Loaded strictly from this Python file (no database access).
"""

from typing import Dict

# Protected Brand Names (lowercase normalized -> Display Name)
PROTECTED_BRANDS: Dict[str, str] = {
    "tata": "Tata",
    "microsoft": "Microsoft",
    "google": "Google",
    "apple": "Apple",
    "amazon": "Amazon",
    "reliance": "Reliance",
    "infosys": "Infosys",
    "wipro": "Wipro",
    "titan": "Titan",
}

# Protected Organization / Statutory Names (lowercase normalized -> Display Name)
PROTECTED_ORGANIZATIONS: Dict[str, str] = {
    "red cross": "Red Cross",
    "unesco": "UNESCO",
    "unicef": "UNICEF",
    "world health organization": "World Health Organization",
}

# Protected Copyright / Media / Character Entities (lowercase normalized -> Display Name)
PROTECTED_COPYRIGHTS: Dict[str, str] = {
    "disney": "Disney",
    "marvel": "Marvel",
    "pokemon": "Pokemon",
}

# Unified Registry mapping normalized name -> metadata dictionary
PROTECTED_NAMES_REGISTRY: Dict[str, Dict[str, str]] = {}

for name_key, display_name in PROTECTED_BRANDS.items():
    PROTECTED_NAMES_REGISTRY[name_key] = {
        "canonical_name": display_name,
        "category": "Brand"
    }

for name_key, display_name in PROTECTED_ORGANIZATIONS.items():
    PROTECTED_NAMES_REGISTRY[name_key] = {
        "canonical_name": display_name,
        "category": "Organization"
    }

for name_key, display_name in PROTECTED_COPYRIGHTS.items():
    PROTECTED_NAMES_REGISTRY[name_key] = {
        "canonical_name": display_name,
        "category": "Copyright"
    }
