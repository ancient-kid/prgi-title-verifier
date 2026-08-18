"""
Unit Tests for Stage 4C: Cross-Lingual Semantic Similarity Engine
"""

import numpy as np
import pytest
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine, _stable_hash_index


class TestSemanticLexicon:
    def setup_method(self):
        self.engine = SemanticSimilarityEngine()

    def test_required_cross_lingual_pairs(self):
        # 1. Daily Evening <-> Pratidin Sandhya
        res1 = self.engine.compare_semantic_similarity("Daily Evening", "Pratidin Sandhya")
        assert res1["lexicon_score"] >= 0.85
        assert res1["aggregate_semantic_score"] >= 0.85
        assert len(res1["concept_pairs"]) >= 2
        assert "daily" in res1["canonical_concepts_title1"]
        assert "evening" in res1["canonical_concepts_title1"]

        # 2. Morning News <-> Prabhat Samachar
        res2 = self.engine.compare_semantic_similarity("Morning News", "Prabhat Samachar")
        assert res2["lexicon_score"] >= 0.85
        assert res2["aggregate_semantic_score"] >= 0.85
        assert len(res2["concept_pairs"]) >= 2

        # 3. People's Voice <-> Jan Vani
        res3 = self.engine.compare_semantic_similarity("Peoples Voice", "Jan Vani")
        assert res3["lexicon_score"] >= 0.85
        assert res3["aggregate_semantic_score"] >= 0.85
        assert len(res3["concept_pairs"]) >= 2

    def test_cross_regional_indian_language_pairs(self):
        # Hindi <-> Bengali/Odia: Prabhat Samachar <-> Sakala Sambad
        res_morn = self.engine.compare_semantic_similarity("Prabhat Samachar", "Sakala Sambad")
        assert res_morn["lexicon_score"] >= 0.85
        assert len(res_morn["concept_pairs"]) >= 2

        # Bengali <-> Urdu/Hindi: Pratidin Sandhya <-> Rozana Shaam
        res_eve = self.engine.compare_semantic_similarity("Pratidin Sandhya", "Rozana Shaam")
        assert res_eve["lexicon_score"] >= 0.85
        assert len(res_eve["concept_pairs"]) >= 2

    def test_negative_controls(self):
        # Daily News vs Solar Science (distinct concepts)
        res_neg = self.engine.compare_semantic_similarity("Daily News", "Solar Science")
        assert res_neg["lexicon_score"] == 0.0
        assert res_neg["aggregate_semantic_score"] < 0.30
        assert len(res_neg["concept_pairs"]) == 0

    def test_empty_and_edge_inputs(self):
        res_empty = self.engine.compare_semantic_similarity("", "")
        assert res_empty["lexicon_score"] == 0.0
        assert res_empty["aggregate_semantic_score"] == 0.0

        res_half_empty = self.engine.compare_semantic_similarity("Daily", "")
        assert res_half_empty["lexicon_score"] == 0.0


class TestDeterministicVectorSpace:
    def setup_method(self):
        self.engine = SemanticSimilarityEngine()

    def test_fixed_dimensionality(self):
        vec = self.engine._hash_vector("Daily Evening News")
        assert len(vec) == 2048
        assert vec.dtype == np.float32

    def test_deterministic_vector_generation(self):
        # Ensure hashing is 100% reproducible across invocations
        v1 = self.engine._hash_vector("Pratidin Sandhya")
        v2 = self.engine._hash_vector("Pratidin Sandhya")
        np.testing.assert_array_almost_equal(v1, v2)

    def test_stable_hash_modulo(self):
        idx1 = _stable_hash_index("CONCEPT:daily", 2048)
        idx2 = _stable_hash_index("CONCEPT:daily", 2048)
        assert idx1 == idx2
        assert 0 <= idx1 < 2048

    def test_cosine_similarity_normalized(self):
        v1 = self.engine._hash_vector("Daily Evening")
        v2 = self.engine._hash_vector("Pratidin Sandhya")
        cosine_sim = float(np.dot(v1, v2))
        assert cosine_sim >= 0.80

    def test_structured_output_contract(self):
        res = self.engine.compare_semantic_similarity("Morning News", "Prabhat Samachar")
        assert "lexicon_score" in res
        assert "vector_score" in res
        assert "aggregate_semantic_score" in res
        assert "concept_pairs" in res
        assert "canonical_concepts_title1" in res
        assert "canonical_concepts_title2" in res
