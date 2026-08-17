"""
Company Name / Protected Name Rule Enforcement.

Checks if a title is an EXACT match for a protected corporate, brand, organization, or copyright name.
- Uses exact normalized matching.
- Substring matching is NOT used.
- Fuzzy matching is NOT used.
- No database access is used.
"""

import re
from typing import Any, Dict, Optional

from backend.company.protected_names import (
    PROTECTED_BRANDS,
    PROTECTED_COPYRIGHTS,
    PROTECTED_NAMES_REGISTRY,
    PROTECTED_ORGANIZATIONS,
)


def normalize_title(title: str) -> str:
    """
    Normalizes input title for exact protected name matching:
    1. Strips leading/trailing whitespace.
    2. Converts to lowercase.
    3. Strips punctuation characters (e.g. !, ., ?, etc.).
    4. Collapses multiple whitespace spaces into a single space.
    """
    if not title:
        return ""
    text = title.strip().lower()
    # Strip punctuation
    text = re.sub(r"[^\w\s]", "", text)
    # Normalize multiple whitespace characters
    text = re.sub(r"\s+", " ", text).strip()
    return text


def check_protected_name(title: str) -> Optional[Dict[str, Any]]:
    """
    Checks if title is an exact match for any protected corporate/brand/org/copyright name.

    Returns:
        Structured result dict if exact match is found:
        {
            "status": "REJECT",
            "rule": "Protected Corporate/Brand Name Violation",
            "matched_name": canonical_name,
            "category": category,
            "explanation": f"Title matches protected corporate/brand/organization name '{canonical_name}'."
        }
        None if no exact match is found.
    """
    normalized = normalize_title(title)
    if not normalized:
        return None

    entry = PROTECTED_NAMES_REGISTRY.get(normalized)
    if entry:
        canonical_name = entry.get("canonical_name", title.strip())
        category = entry.get("category", "Brand/Corporate")
        return {
            "status": "REJECT",
            "rule": "Protected Corporate/Brand Name Violation",
            "matched_name": canonical_name,
            "category": category,
            "explanation": f"Title matches protected corporate/brand/organization name '{canonical_name}'."
        }

    return None
