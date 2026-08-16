"""
Unit Tests for Gibberish & Meaningless Word Detector (Stage 1)
"""

import sys
from pathlib import Path

# Add project root to python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import pytest
from backend.pipeline.gibberish_detector import (
    compute_shannon_entropy,
    is_gibberish_word,
    validate_title_meaningfulness,
)
from backend.pipeline.stage1_preprocessor import extract_anchor_words
from backend.pipeline.engine import TitleVerificationEngine


def test_shannon_entropy_calculation():
    # Repetitive characters have low entropy
    low_ent = compute_shannon_entropy("aaaaaaa")
    assert low_ent == 0.0

    # Diverse characters have higher entropy
    high_ent = compute_shannon_entropy("newspaper")
    assert high_ent > 2.5


def test_repetitive_gibberish():
    is_gib, err_type, reason = is_gibberish_word("zzzzzzz")
    assert is_gib is True
    assert err_type == "REPETITIVE_GIBBERISH"

    is_gib, err_type, reason = is_gibberish_word("asdfasdfasdf")
    assert is_gib is True
    assert err_type == "REPETITIVE_GIBBERISH"


def test_unpronounceable_consonant_clusters():
    # 5+ consecutive consonants
    is_gib, err_type, reason = is_gibberish_word("ghibrisg")
    assert is_gib is True
    assert err_type == "UNPRONOUNCEABLE_GIBBERISH"

    is_gib, err_type, reason = is_gibberish_word("qwrtpzx")
    assert is_gib is True
    assert err_type == "UNPRONOUNCEABLE_GIBBERISH"


def test_valid_titles_pass():
    # English valid titles
    res = validate_title_meaningfulness("The Daily Herald")
    assert res["valid"] is True

    res_in = validate_title_meaningfulness("Prabhat Samachar")
    assert res_in["valid"] is True

    res_reg = validate_title_meaningfulness("Vishwa Varta")
    assert res_reg["valid"] is True


def test_valid_acronyms_pass():
    res_bbc = validate_title_meaningfulness("BBC News India")
    assert res_bbc["valid"] is True

    res_isro = validate_title_meaningfulness("ISRO Bulletin")
    assert res_isro["valid"] is True

    res_ndtv = validate_title_meaningfulness("NDTV Express")
    assert res_ndtv["valid"] is True


def test_stage1_preprocessor_gibberish_rejection():
    # Test Stage 1 preprocessor rejection on gibberish title
    res = extract_anchor_words("ghibrisg daily")
    assert res["is_valid_structure"] is False
    assert res["error_type"] == "UNPRONOUNCEABLE_GIBBERISH"
    assert "Meaningless/Gibberish Title Violation" in res["rejection_reason"]


def test_verification_engine_gibberish_rejection():
    engine = TitleVerificationEngine()
    result = engine.verify_title("ghibrisg news")

    assert result["status"] == "Rejected"
    assert result["verification_probability"] == 0.0
    assert result["decision"] == "REJECTED_UNPRONOUNCEABLE_GIBBERISH"
    assert len(result["suggestions"]) > 0
    assert "gibberish" in result["suggestions"][1].lower() or "meaningful" in result["suggestions"][0].lower()
