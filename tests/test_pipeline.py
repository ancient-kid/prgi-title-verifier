"""
Automated Test Suite for PRGI Title Verification Pipeline Stages
"""

import sys
from pathlib import Path

# Add project root to python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import pytest
from backend.lock_manager import LockManager
from backend.pipeline.stage1_preprocessor import extract_anchor_words, validate_title_structure
from backend.pipeline.stage2_guidelines import check_guidelines
from backend.pipeline.stage3_frankentitle import FrankentitleDetector
from backend.pipeline.stage4_orthographic import compute_orthographic_similarity
from backend.pipeline.stage4_phonetic import compare_phonetic_similarity
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine
from backend.data_loader import TitleIndex
from backend.pipeline.engine import TitleVerificationEngine


def test_stage1_prohibited_symbols():
    # Test case 1A: Non-text characters, mathematical symbols (+, *, etc.), emojis
    res_plus = extract_anchor_words("News+")
    assert res_plus["is_valid_structure"] is False
    assert res_plus["error_type"] == "PROHIBITED_SYMBOLS"
    assert "Prohibited Non-Text Characters" in res_plus["rejection_reason"]

    res_star = extract_anchor_words("Daily*Express")
    assert res_star["is_valid_structure"] is False
    assert res_star["error_type"] == "PROHIBITED_SYMBOLS"

    res_hash = extract_anchor_words("Star #1")
    assert res_hash["is_valid_structure"] is False
    assert res_hash["error_type"] == "PROHIBITED_SYMBOLS"


def test_stage1_purely_numeric():
    # Test case 1B: Purely numeric titles (just numbers)
    res_num = extract_anchor_words("12345")
    assert res_num["is_valid_structure"] is False
    assert res_num["error_type"] == "PURE_NUMERIC"
    assert "Numeric-Only Title Violation" in res_num["rejection_reason"]

    res_year = extract_anchor_words("2024")
    assert res_year["is_valid_structure"] is False
    assert res_year["error_type"] == "PURE_NUMERIC"

    res_spaced_num = extract_anchor_words("24 7")
    assert res_spaced_num["is_valid_structure"] is False
    assert res_spaced_num["error_type"] == "PURE_NUMERIC"


def test_stage1_anchor_extraction():
    # Test case 1C: "The Daily Mumbai Express" -> Anchor should be "mumbai"
    res = extract_anchor_words("The Daily Mumbai Express")
    assert res["is_valid_structure"] is True
    assert res["is_purely_generic"] is False
    assert res["anchor_words"] == "mumbai"
    assert "the" in res["stripped_prefixes"]
    assert "daily" in res["stripped_prefixes"]
    assert "express" in res["stripped_suffixes"]


def test_stage1_purely_generic_rejection():
    # Test case 2: "The Daily News" -> Pure generic
    res = extract_anchor_words("The Daily News")
    assert res["is_valid_structure"] is True
    assert res["is_purely_generic"] is True
    assert "Pure Generic Title Violation" in res["rejection_reason"]


def test_stage2_disallowed_words():
    # Test case 3: Disallowed words check (Crime, Police, CBI, Sarkar)
    res_crime = check_guidelines("the crime investigation daily", ["the", "crime", "investigation", "daily"])
    assert res_crime["passed"] is False
    assert res_crime["probability_multiplier"] == 0.0
    terms = [v["term"] for v in res_crime["violations"]]
    assert "Crime" in terms or "Investigation" in terms

    res_police = check_guidelines("mumbai police chronicle", ["mumbai", "police", "chronicle"])
    assert res_police["passed"] is False
    assert any("Police" in v["term"] for v in res_police["violations"])

    res_safe = check_guidelines("green harvest agriculture bulletin", ["green", "harvest", "agriculture", "bulletin"])
    assert res_safe["passed"] is True
    assert res_safe["probability_multiplier"] == 1.0


def test_stage3_frankentitle():
    # Test case 4: "Hindu Indian Express" -> Frankentitle mashup
    detector = FrankentitleDetector(
        registered_titles={"the hindu", "hindu", "the indian express", "indian express", "dainik jagran", "punjab kesari"},
        anchor_set={"hindu", "indian express", "jagran", "kesari"}
    )
    res = detector.check_combination("hindu indian express", ["hindu", "indian", "express"])
    assert res["is_frankentitle"] is True
    assert res["probability_multiplier"] == 0.0

    res_safe = detector.check_combination("aurora quantum science", ["aurora", "quantum", "science"])
    assert res_safe["is_frankentitle"] is False


def test_stage4a_phonetic_similarity():
    # Test case 5: "Namascar" vs "Namaskar" -> 100% or very high phonetic match
    sim = compare_phonetic_similarity("namascar", "namaskar")
    assert sim >= 0.90

    sim2 = compare_phonetic_similarity("daineq", "dainik")
    assert sim2 >= 0.85


def test_stage4b_orthographic_similarity():
    # Test case 6: Typo distance match
    res = compute_orthographic_similarity("The Times of India", "The Tymes of India")
    assert res["jaro_winkler"] >= 0.90
    assert res["aggregate_orthographic_score"] >= 0.90


def test_stage4c_cross_lingual_semantic():
    # Test case 7: "Daily Evening" vs "Pratidin Sandhya" -> High cross-lingual score
    engine = SemanticSimilarityEngine()
    score, pairs = engine.calculate_lexicon_similarity("daily evening", "pratidin sandhya")
    assert score >= 0.85
    assert len(pairs) > 0


def test_lock_manager():
    # Test case 8: Lock acquisition and collision detection
    lm = LockManager()
    success, err, data = lm.acquire_lock("Nova Solar Gazette", "USER_A", "Alpha Media", ttl_seconds=60)
    assert success is True

    # User B attempts to acquire same title
    success_b, err_b, _ = lm.acquire_lock("Nova Solar Gazette", "USER_B", "Beta Press")
    assert success_b is False
    assert "currently locked" in err_b

    # Release lock
    lm.release_lock("Nova Solar Gazette", "USER_A")
    success_b2, _, _ = lm.acquire_lock("Nova Solar Gazette", "USER_B", "Beta Press")
    assert success_b2 is True
    lm.release_lock("Nova Solar Gazette", "USER_B")


def test_end_to_end_engine_verification():
    # Test case 9: Full engine integration
    index = TitleIndex()
    index.load_data()
    lm = LockManager()
    engine = TitleVerificationEngine(titles_index=index, lock_manager=lm)

    # 1. Prohibited symbols -> 0%
    r_sym = engine.verify_title("News+")
    assert r_sym["verification_probability"] == 0.0
    assert r_sym["status"] == "Rejected"
    assert r_sym["decision"] == "REJECTED_PROHIBITED_SYMBOLS"

    # 2. Purely numeric -> 0%
    r_num = engine.verify_title("2024")
    assert r_num["verification_probability"] == 0.0
    assert r_num["status"] == "Rejected"
    assert r_num["decision"] == "REJECTED_PURE_NUMERIC"

    # 3. Prohibited word -> 0%
    r1 = engine.verify_title("The Crime Investigation Daily")
    assert r1["verification_probability"] == 0.0
    assert r1["status"] == "Rejected"

    # 4. Pure generic -> 0%
    r2 = engine.verify_title("The Daily News")
    assert r2["verification_probability"] == 0.0
    assert r2["status"] == "Rejected"

    # 5. Phonetic homophone of registered title -> high similarity, low probability
    r3 = engine.verify_title("Namascar India")
    assert r3["status"] == "Rejected"
    assert r3["verification_probability"] <= 25.0

    # 6. Novel distinct title -> High verification probability
    r4 = engine.verify_title("Zylophonic Quantum Astroflora")
    assert r4["status"] == "Approved"
    assert r4["verification_probability"] >= 60.0
