"""
Unit Tests for Stage 4B: Orthographic (String Distance & Fuzzy) Similarity Engine
"""

import pytest
from backend.pipeline.stage4_orthographic import (
    clean_orthographic_text,
    compute_char_ngrams,
    compute_orthographic_similarity,
    ngram_similarity,
)


class TestNgramDice:
    def test_ngram_extraction_with_boundary_markers(self):
        ngrams = compute_char_ngrams("test", n=3)
        # Padded text is _test_ -> _te, tes, est, st_
        assert "_te" in ngrams
        assert "tes" in ngrams
        assert "est" in ngrams
        assert "st_" in ngrams

    def test_short_string_ngram(self):
        ngrams = compute_char_ngrams("a", n=3)
        assert len(ngrams) == 1
        assert "_a_" in ngrams

    def test_dice_similarity_exact_and_disjoint(self):
        assert ngram_similarity("Hindustan", "Hindustan") == 1.0
        assert ngram_similarity("ABCDEF", "UVWXYZ") == 0.0

    def test_dice_similarity_partial_match(self):
        sim = ngram_similarity("Times", "Tymes")
        assert 0.40 <= sim <= 0.80


class TestOrthographicSimilarity:
    def test_required_typo_pairs(self):
        # Hindustan Times <-> Hindustan Tymes
        res = compute_orthographic_similarity("Hindustan Times", "Hindustan Tymes")
        assert res["levenshtein_ratio"] >= 0.85
        assert res["jaro_winkler"] >= 0.85
        assert res["aggregate_orthographic_score"] >= 0.85

    def test_required_token_reordering(self):
        # Times of India <-> India Times
        res = compute_orthographic_similarity("Times of India", "India Times")
        assert res["token_sort_ratio"] >= 0.80
        assert res["aggregate_orthographic_score"] >= 0.80

    def test_single_word_and_short_strings(self):
        # Orbit vs Debit - distinct short words
        res_orbit = compute_orthographic_similarity("orbit", "debit")
        assert res_orbit["aggregate_orthographic_score"] < 0.65

        # Exact match
        res_exact = compute_orthographic_similarity("Tribune", "Tribune")
        assert res_exact["aggregate_orthographic_score"] == 1.0

    def test_case_and_punctuation_insensitivity(self):
        res1 = compute_orthographic_similarity("Daily News!", "daily news")
        assert res1["aggregate_orthographic_score"] == 1.0

        res2 = compute_orthographic_similarity("The Times of India", "the times of india")
        assert res2["aggregate_orthographic_score"] == 1.0

    def test_empty_and_whitespace(self):
        res_empty = compute_orthographic_similarity("", "")
        assert res_empty["aggregate_orthographic_score"] == 0.0
        assert res_empty["levenshtein_ratio"] == 0.0

        res_one_empty = compute_orthographic_similarity("India", "  ")
        assert res_one_empty["aggregate_orthographic_score"] == 0.0

    def test_structured_output_contract(self):
        res = compute_orthographic_similarity("Express", "Express")
        assert "jaro_winkler" in res
        assert "levenshtein_ratio" in res
        assert "token_sort_ratio" in res
        assert "ngram_sim" in res
        assert "aggregate_orthographic_score" in res
