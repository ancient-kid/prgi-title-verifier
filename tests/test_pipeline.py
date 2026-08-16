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
from backend.pipeline.stage1_preprocessor import extract_anchor_words
from backend.pipeline.stage2_guidelines import check_guidelines
from backend.pipeline.stage3_frankentitle import FrankentitleDetector
from backend.pipeline.stage4_orthographic import compute_orthographic_similarity
from backend.pipeline.stage4_phonetic import compare_phonetic_similarity
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine
from backend.data_loader import TitleIndex
from backend.pipeline.engine import TitleVerificationEngine


def test_stage1_anchor_extraction():
    # Test case 1: "The Daily Mumbai Express" -> Anchor should be "mumbai"
    res = extract_anchor_words("The Daily Mumbai Express")
    assert res["is_purely_generic"] is False
    assert res["anchor_words"] == "mumbai"
    assert "the" in res["stripped_prefixes"]
    assert "daily" in res["stripped_prefixes"]
    assert "express" in res["stripped_suffixes"]


def test_stage1_purely_generic_rejection():
    # Test case 2: "The Daily News" -> Pure generic
    res = extract_anchor_words("The Daily News")
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

    # 1. Prohibited word -> 0%
    r1 = engine.verify_title("The Crime Investigation Daily")
    assert r1["verification_probability"] == 0.0
    assert r1["status"] == "Rejected"

    # 2. Pure generic -> 0%
    r2 = engine.verify_title("The Daily News")
    assert r2["verification_probability"] == 0.0
    assert r2["status"] == "Rejected"

    # 3. Phonetic homophone of registered title -> high similarity, low probability
    r3 = engine.verify_title("Namascar India")
    assert r3["status"] == "Rejected"
    assert r3["verification_probability"] <= 25.0

    # 4. Novel distinct title -> High verification probability
    r4 = engine.verify_title("Zylophonic Quantum Astroflora")
    assert r4["status"] == "Approved"
    assert r4["verification_probability"] >= 60.0
