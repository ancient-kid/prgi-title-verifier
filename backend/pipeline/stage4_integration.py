"""
Stage 4 Unified Integration API

Provides a unified integration entry point to evaluate candidate pairs across all three
Stage 4 similarity dimensions (4A Phonetic, 4B Orthographic, 4C Cross-Lingual Semantic)
and formulate structured diagnostics for Stage 5 aggregation.
"""

from typing import Any, Dict, Optional

from backend.pipeline.stage4_orthographic import compute_orthographic_similarity
from backend.pipeline.stage4_phonetic import compare_phonetic_similarity_detailed
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine

# Module-level default singleton for semantic engine
_DEFAULT_SEMANTIC_ENGINE = SemanticSimilarityEngine()


def compare_title_against_candidate(
    new_title: str,
    candidate_title: str,
    new_anchor: Optional[str] = None,
    candidate_anchor: Optional[str] = None,
    semantic_engine: Optional[SemanticSimilarityEngine] = None
) -> Dict[str, Any]:
    """
    Evaluates similarity between a target title and an existing registered candidate title
    across Phonetic, Orthographic, and Cross-Lingual Semantic dimensions.
    
    Args:
        new_title: Submitted title (cleaned)
        candidate_title: Registered candidate title (cleaned)
        new_anchor: Distinctive anchor words for new title (optional)
        candidate_anchor: Distinctive anchor words for candidate title (optional)
        semantic_engine: Custom SemanticSimilarityEngine instance (optional)
        
    Returns:
        Dict containing:
            - phonetic_similarity: float [0.0, 1.0]
            - orthographic_similarity: float [0.0, 1.0]
            - semantic_similarity: float [0.0, 1.0]
            - highest_similarity: float [0.0, 1.0]
            - diagnostics:
                - phonetic: Dict[str, Any]
                - orthographic: Dict[str, Any]
                - semantic: Dict[str, Any]
    """
    sem_engine = semantic_engine or _DEFAULT_SEMANTIC_ENGINE
    
    # 1. Stage 4A: Phonetic Similarity
    phonetic_full = compare_phonetic_similarity_detailed(new_title, candidate_title)
    if new_anchor and candidate_anchor and (new_anchor != new_title or candidate_anchor != candidate_title):
        phonetic_anchor = compare_phonetic_similarity_detailed(new_anchor, candidate_anchor)
        if phonetic_anchor["score"] > phonetic_full["score"]:
            phonetic_diag = phonetic_anchor
            ph_score = phonetic_anchor["score"]
        else:
            phonetic_diag = phonetic_full
            ph_score = phonetic_full["score"]
    else:
        phonetic_diag = phonetic_full
        ph_score = phonetic_full["score"]
        
    # 2. Stage 4B: Orthographic Similarity
    ortho_full = compute_orthographic_similarity(new_title, candidate_title)
    if new_title == candidate_title:
        ortho_score = 1.0
        ortho_diag = ortho_full
    elif new_anchor and candidate_anchor and new_anchor == candidate_anchor:
        ortho_score = 0.95
        ortho_diag = {
            "full_title": ortho_full,
            "anchor_words": compute_orthographic_similarity(new_anchor, candidate_anchor),
            "aggregate_orthographic_score": 0.95
        }
    elif new_anchor and candidate_anchor:
        ortho_anchor = compute_orthographic_similarity(new_anchor, candidate_anchor)
        ortho_score = max(
            ortho_anchor["aggregate_orthographic_score"],
            ortho_full["aggregate_orthographic_score"] * 0.70
        )
        ortho_diag = {
            "full_title": ortho_full,
            "anchor_words": ortho_anchor,
            "aggregate_orthographic_score": round(ortho_score, 4)
        }
    else:
        ortho_score = ortho_full["aggregate_orthographic_score"] * 0.75
        ortho_diag = {
            "full_title": ortho_full,
            "aggregate_orthographic_score": round(ortho_score, 4)
        }
        
    # 3. Stage 4C: Cross-Lingual Semantic Similarity
    sem_diag = sem_engine.compare_semantic_similarity(new_title, candidate_title)
    sem_score = sem_diag["aggregate_semantic_score"]
    
    # Calculate highest similarity across all 3 dimensions
    highest_sim = max(ph_score, ortho_score, sem_score)
    
    return {
        "phonetic_similarity": round(ph_score, 4),
        "orthographic_similarity": round(ortho_score, 4),
        "semantic_similarity": round(sem_score, 4),
        "highest_similarity": round(highest_sim, 4),
        "diagnostics": {
            "phonetic": phonetic_diag,
            "orthographic": ortho_diag,
            "semantic": sem_diag
        }
    }
