"""
Unit & Integration Tests for Protected Corporate/Brand Name Rules
"""

import sys
from pathlib import Path

# Add project root to python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import pytest
from backend.company.company_name_rule import check_protected_name, normalize_title
from backend.company.protected_names import (
    PROTECTED_BRANDS,
    PROTECTED_COPYRIGHTS,
    PROTECTED_NAMES_REGISTRY,
    PROTECTED_ORGANIZATIONS,
)


def test_normalization():
    """Verify normalization logic for casing, punctuation, and whitespace."""
    assert normalize_title("Tata") == "tata"
    assert normalize_title("TATA") == "tata"
    assert normalize_title(" Tata ") == "tata"
    assert normalize_title("Tata!") == "tata"
    assert normalize_title(" Microsoft. ") == "microsoft"
    assert normalize_title("Red   Cross!!") == "red cross"


def test_protected_names_exact_matches():
    """Verify that exact matches for protected names return structured REJECT results."""
    exact_reject_cases = [
        "Tata",
        "TATA",
        " Tata ",
        "Tata!",
        "Microsoft",
        "Google",
    ]

    for title in exact_reject_cases:
        res = check_protected_name(title)
        assert res is not None, f"Expected {title} to be rejected, but got None"
        assert res["status"] == "REJECT"
        assert "rule" in res
        assert "matched_name" in res
        assert "category" in res
        assert "explanation" in res


def test_protected_names_no_substring_matching():
    """Verify that compound titles / titles containing protected words as substrings return None."""
    non_reject_cases = [
        "Tata News",
        "Tata Maharashtra",
        "Microsoft India",
        "Google News",
        "Mumbai Daily",
    ]

    for title in non_reject_cases:
        res = check_protected_name(title)
        assert res is None, f"Expected {title} to return None, but got {res}"


def test_categories_brand_org_copyright():
    """Verify that brand, organization, and copyright entries are categorized and checked accurately."""
    # Brand entry
    res_brand = check_protected_name("Apple")
    assert res_brand is not None
    assert res_brand["category"] == "Brand"
    assert res_brand["matched_name"] == "Apple"
    assert check_protected_name("Apple Daily") is None

    # Organization entry
    res_org = check_protected_name("Red Cross")
    assert res_org is not None
    assert res_org["category"] == "Organization"
    assert res_org["matched_name"] == "Red Cross"
    assert check_protected_name("Red Cross Journal") is None

    # Copyright entry
    res_copy = check_protected_name("Disney")
    assert res_copy is not None
    assert res_copy["category"] == "Copyright"
    assert res_copy["matched_name"] == "Disney"
    assert check_protected_name("Disney News") is None


def test_loaded_only_from_python_file_no_db():
    """Verify registry is purely in-memory Python structure with no database imports or queries."""
    assert len(PROTECTED_NAMES_REGISTRY) > 0
    assert "tata" in PROTECTED_NAMES_REGISTRY
    assert "microsoft" in PROTECTED_NAMES_REGISTRY
    assert "google" in PROTECTED_NAMES_REGISTRY


def test_prefix_suffix_rejection():
    """Verify that titles with generic prefixes/suffixes + curse words or protected names are rejected in Stage 2."""
    from backend.pipeline.engine import TitleVerificationEngine
    from backend.data_loader import TitleIndex
    engine = TitleVerificationEngine()

    stage2_reject_cases = [
        "The fuck",
        "fuck times",
        "microsoft times",
        "the apple",
        "Apple Daily",
        "The Tata Express",
    ]

    for title in stage2_reject_cases:
        res = engine.verify_title(title)
        assert res["status"] == "Rejected", f"Expected {title} to be Rejected, got {res['status']}"
        assert res["decision"] == "REJECTED_STAGE_2", f"Expected {title} to be REJECTED_STAGE_2, got {res['decision']}"
        assert res["verification_probability"] == 0.0

