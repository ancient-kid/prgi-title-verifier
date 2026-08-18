"""
Unit Tests for Stage 4 Integration API
"""

import pytest
from backend.pipeline.stage4_integration import compare_title_against_candidate


class TestStage4IntegrationAPI:
    def test_complete_similarity_bundle(self):
        res = compare_title_against_candidate(
            new_title="namascar daily",
            candidate_title="namaskar daily",
            new_anchor="namascar",
            candidate_anchor="namaskar"
        )
        assert "phonetic_similarity" in res
        assert "orthographic_similarity" in res
        assert "semantic_similarity" in res
        assert "highest_similarity" in res
        assert "diagnostics" in res

        # Expected high phonetic match
        assert res["phonetic_similarity"] >= 0.90
        assert res["highest_similarity"] >= 0.90

        # Diagnostics structure
        assert "phonetic" in res["diagnostics"]
        assert "orthographic" in res["diagnostics"]
        assert "semantic" in res["diagnostics"]

    def test_semantic_dominant_match(self):
        res = compare_title_against_candidate(
            new_title="daily evening",
            candidate_title="pratidin sandhya"
        )
        assert res["semantic_similarity"] >= 0.85
        assert res["highest_similarity"] >= 0.85
        assert len(res["diagnostics"]["semantic"]["concept_pairs"]) >= 2

    def test_orthographic_dominant_match(self):
        res = compare_title_against_candidate(
            new_title="the times of india",
            candidate_title="the tymes of india",
            new_anchor="times",
            candidate_anchor="tymes"
        )
        assert res["orthographic_similarity"] >= 0.85
        assert res["highest_similarity"] >= 0.85

    def test_anchor_precedence(self):
        # Different generic prefixes/suffixes, identical distinctive anchors
        res = compare_title_against_candidate(
            new_title="the weekly navbharat post",
            candidate_title="daily navbharat express",
            new_anchor="navbharat",
            candidate_anchor="navbharat"
        )
        assert res["orthographic_similarity"] >= 0.90
        assert res["highest_similarity"] >= 0.90
