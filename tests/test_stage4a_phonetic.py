"""
Unit Tests for Stage 4A: Phonetic Similarity Engine
"""

import pytest
from backend.pipeline.double_metaphone import double_metaphone
from backend.pipeline.stage4_phonetic import (
    compare_phonetic_similarity,
    compare_phonetic_similarity_detailed,
    compute_phonetic_fingerprint,
    get_double_metaphone,
    indic_soundex,
    normalize_indic_phonetic,
)


class TestIndicNormalization:
    def test_aspirate_normalization(self):
        assert normalize_indic_phonetic("Bharat") == normalize_indic_phonetic("Barat")
        assert normalize_indic_phonetic("Dharwad") == normalize_indic_phonetic("Darwad")
        assert normalize_indic_phonetic("Khabar") == normalize_indic_phonetic("Kabar")
        assert normalize_indic_phonetic("Ghat") == normalize_indic_phonetic("Gat")
        assert normalize_indic_phonetic("Than") == normalize_indic_phonetic("Tan")

    def test_elongated_vowels(self):
        assert normalize_indic_phonetic("Bhaarat") == normalize_indic_phonetic("Bharat")
        assert normalize_indic_phonetic("Dainik") == normalize_indic_phonetic("Daynik")
        assert normalize_indic_phonetic("Deen") == normalize_indic_phonetic("Din")
        assert normalize_indic_phonetic("Sooraj") == normalize_indic_phonetic("Suraj")

    def test_interchangeable_consonants(self):
        assert normalize_indic_phonetic("Vani") == normalize_indic_phonetic("Wani")
        assert normalize_indic_phonetic("Namascar") == normalize_indic_phonetic("Namaskar")
        assert normalize_indic_phonetic("Qaumi") == normalize_indic_phonetic("Kaumi")

    def test_empty_and_special_chars(self):
        assert normalize_indic_phonetic("") == ""
        assert normalize_indic_phonetic("   ") == ""
        assert normalize_indic_phonetic("1234") == ""
        assert normalize_indic_phonetic("News!#") == "news"


class TestDoubleMetaphone:
    def test_primary_and_secondary_generation(self):
        prim, sec = double_metaphone("Smith")
        assert prim == "SM0"
        assert sec == "XMT"

        prim_sch, sec_sch = double_metaphone("Schmidt")
        assert prim_sch == "XMT"
        assert sec_sch == "SMT"

    def test_anglicized_and_indian_words(self):
        prim_k, sec_k = double_metaphone("Namaskar")
        prim_c, sec_c = double_metaphone("Namascar")
        assert prim_k == prim_c

        prim_d1, _ = double_metaphone("Dainik")
        prim_d2, _ = double_metaphone("Daineq")
        assert prim_d1 == prim_d2

    def test_empty_input(self):
        assert double_metaphone("") == ("", "")
        assert double_metaphone("   ") == ("", "")


class TestIndicSoundex:
    def test_fixed_length_format(self):
        code = indic_soundex("Bharat")
        assert len(code) == 5
        assert code[0] == "B"
        assert code[1:].isdigit()

    def test_consonant_classes(self):
        # B/P/V/W -> class 1
        assert indic_soundex("Bharat")[0] == "B"
        assert indic_soundex("Vani")[0] == "W"

    def test_soundex_homophones(self):
        assert indic_soundex("Dainik") == indic_soundex("Daineq")
        assert indic_soundex("Namaskar") == indic_soundex("Namascar")

    def test_empty_soundex(self):
        assert indic_soundex("") == ""
        assert indic_soundex("12345") == ""


class TestPhoneticSimilarityComparison:
    def test_required_homophone_pairs(self):
        # Namaskar <-> Namascar
        assert compare_phonetic_similarity("Namaskar", "Namascar") >= 0.90
        # Bharat <-> Bhaarat
        assert compare_phonetic_similarity("Bharat", "Bhaarat") >= 0.90
        # Bharat <-> Bharath
        assert compare_phonetic_similarity("Bharat", "Bharath") >= 0.85
        # Dainik <-> Daineq
        assert compare_phonetic_similarity("Dainik", "Daineq") >= 0.85

    def test_short_word_protection(self):
        # Unrelated short words with similar soundex starting letters must NOT match
        assert compare_phonetic_similarity("bat", "buzz") < 0.35
        assert compare_phonetic_similarity("pen", "pit") < 0.35
        assert compare_phonetic_similarity("cat", "cup") < 0.35
        assert compare_phonetic_similarity("red", "run") < 0.35
        assert compare_phonetic_similarity("top", "ten") < 0.35
        assert compare_phonetic_similarity("sun", "sea") < 0.35

        # Minimal vowel pairs
        assert compare_phonetic_similarity("bat", "bet") < 0.50
        assert compare_phonetic_similarity("pan", "pin") < 0.50

    def test_multi_word_titles_and_reordering(self):
        # Token reordering
        score_ordered = compare_phonetic_similarity("Daily India Times", "Times Daily India")
        assert score_ordered >= 0.90

        # Multi-word phonetic copy
        score_copy = compare_phonetic_similarity("Dainik Bhaarat Samachar", "Daynik Bharat Samachar")
        assert score_copy >= 0.90

    def test_negative_controls(self):
        assert compare_phonetic_similarity("Hindustan Times", "Gujarat Samachar") < 0.30
        assert compare_phonetic_similarity("Solar Energy Review", "Navbharat Express") < 0.30

    def test_empty_and_edge_inputs(self):
        assert compare_phonetic_similarity("", "") == 0.0
        assert compare_phonetic_similarity("Daily", "") == 0.0
        assert compare_phonetic_similarity("   ", "Daily") == 0.0

    def test_detailed_diagnostic_contract(self):
        res = compare_phonetic_similarity_detailed("Namaskar Express", "Namascar Express")
        assert "score" in res
        assert "title1_tokens" in res
        assert "title2_tokens" in res
        assert "matched_tokens" in res
        assert "phonetic_keys" in res
        assert "indic_soundex_keys" in res
        assert "reason" in res
        assert res["score"] >= 0.90
        assert len(res["matched_tokens"]) == 2
