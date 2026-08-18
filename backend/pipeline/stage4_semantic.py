"""
Stage 4C: Cross-Lingual Semantic Similarity Engine

Detects cross-lingual semantic equivalents between English and Indian languages:
- "Daily Evening" (English) <-> "Pratidin Sandhya" (Bengali/Hindi) -> 90%+ similarity
- "Morning News" (English) <-> "Prabhat Samachar" (Hindi) -> 90%+ similarity
- "People's Voice" (English) <-> "Jan Vani" (Hindi) -> 90%+ similarity

Components:
1. Multilingual Concept Lexicon (Domain Knowledge): Exact semantic alignment across 12 languages.
2. 2048-dimensional Concept and Character-Feature Hash Vector Space: Deterministic feature hashing
   with L2 normalization and Cosine Similarity.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from backend.config import (
    SEMANTIC_MATCH_THRESHOLD,
    SEMANTIC_VECTOR_DIM,
)
from backend.pipeline.lexicon_data import (
    CONCEPT_TO_WORDS,
    CROSS_LINGUAL_LEXICON,
    INDIAN_TO_ENGLISH,
    WORD_TO_CONCEPT,
    WORD_TO_LANG,
)


def _stable_hash_index(s: str, dimension: int = SEMANTIC_VECTOR_DIM) -> int:
    """
    Computes a deterministic feature bucket index [0, dimension - 1]
    using SHA-256 to ensure stability across Python processes and runs.
    """
    digest = hashlib.sha256(s.encode("utf-8")).digest()
    val = int.from_bytes(digest[:4], byteorder="big")
    return val % dimension


class SemanticSimilarityEngine:
    """
    Cross-Lingual Semantic Similarity Engine based on structured domain lexicon
    and a deterministic 2048-dimensional concept and character-feature hash vector space.
    """

    def __init__(self, vector_dim: int = SEMANTIC_VECTOR_DIM):
        self.vector_dim = vector_dim
        self.is_loaded = True

    def _hash_vector(self, text: str) -> np.ndarray:
        """
        Generates a deterministic 2048-dimensional dense concept and subword feature hash vector.
        
        Features:
        - Canonical Concepts: weighted 3.0
        - Character 3-grams: weighted 0.3
        
        Normalized with L2 norm for standard cosine similarity calculation.
        """
        words = [w for w in re.sub(r"[^\w\s]", " ", text).lower().split() if w]
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        
        if not words:
            return vec
            
        for w in words:
            # 1. Map to canonical concept if in lexicon
            if w in WORD_TO_CONCEPT:
                canonical = f"CONCEPT:{WORD_TO_CONCEPT[w]}"
                idx = _stable_hash_index(canonical, self.vector_dim)
                vec[idx] += 3.0
            else:
                # Regular word token feature
                idx = _stable_hash_index(f"WORD:{w}", self.vector_dim)
                vec[idx] += 1.0
                
            # 2. Subword character 3-gram features for morphological similarity
            padded = f"_{w}_"
            for i in range(len(padded) - 2):
                gram = f"GRAM:{padded[i:i+3]}"
                g_idx = _stable_hash_index(gram, self.vector_dim)
                vec[g_idx] += 0.3
                
        norm = float(np.linalg.norm(vec))
        if norm > 0.0:
            vec = vec / norm
        return vec

    def calculate_lexicon_similarity(
        self, title1: str, title2: str
    ) -> Tuple[float, List[str]]:
        """
        Compares titles using the structured domain concept lexicon.
        
        Returns:
            Tuple of (similarity_score, concept_pairs)
        """
        t1_words = [w for w in re.sub(r"[^\w\s]", " ", title1).lower().split() if w]
        t2_words = [w for w in re.sub(r"[^\w\s]", " ", title2).lower().split() if w]
        
        if not t1_words or not t2_words:
            return 0.0, []
            
        concepts_t1 = [WORD_TO_CONCEPT.get(w, "") for w in t1_words]
        concepts_t2 = [WORD_TO_CONCEPT.get(w, "") for w in t2_words]
        
        matched_pairs: List[str] = []
        used_t2_indices: Set[int] = set()
        match_count = 0
        
        for i, w1 in enumerate(t1_words):
            c1 = concepts_t1[i]
            if not c1:
                continue
                
            for j, w2 in enumerate(t2_words):
                if j in used_t2_indices:
                    continue
                c2 = concepts_t2[j]
                if not c2:
                    continue
                    
                if c1 == c2:
                    used_t2_indices.add(j)
                    lang1 = WORD_TO_LANG.get(w1, "unk")
                    lang2 = WORD_TO_LANG.get(w2, "unk")
                    matched_pairs.append(f"'{w1}' ({lang1}) ~= '{w2}' ({lang2}) [Concept: {c1}]")
                    match_count += 1
                    break
                    
        total_tokens = max(len(t1_words), len(t2_words))
        if total_tokens == 0:
            return 0.0, []
            
        score = round(match_count / total_tokens, 4)
        
        # High confidence match if all meaningful words in the shorter title match concepts
        min_tokens = min(len(t1_words), len(t2_words))
        if match_count >= min_tokens and match_count > 0:
            score = max(score, 0.90)
            
        return score, matched_pairs

    def compare_semantic_similarity(self, title1: str, title2: str) -> Dict[str, Any]:
        """
        Computes combined semantic similarity (Lexicon + 2048-dim Vector Space).
        
        Returns:
            Dict containing:
                - lexicon_score: float
                - vector_score: float
                - aggregate_semantic_score: float
                - concept_pairs: List[str]
                - canonical_concepts_title1: List[str]
                - canonical_concepts_title2: List[str]
        """
        t1_words = [w for w in re.sub(r"[^\w\s]", " ", title1).lower().split() if w]
        t2_words = [w for w in re.sub(r"[^\w\s]", " ", title2).lower().split() if w]
        
        canon_t1 = [WORD_TO_CONCEPT[w] for w in t1_words if w in WORD_TO_CONCEPT]
        canon_t2 = [WORD_TO_CONCEPT[w] for w in t2_words if w in WORD_TO_CONCEPT]
        
        lexicon_score, concept_pairs = self.calculate_lexicon_similarity(title1, title2)
        
        v1 = self._hash_vector(title1)
        v2 = self._hash_vector(title2)
        
        # Cosine similarity between L2-normalized vectors
        vector_score = float(np.dot(v1, v2))
        vector_score = round(float(np.clip(vector_score, 0.0, 1.0)), 4)
        
        # Explainable aggregation
        if lexicon_score >= 0.80:
            aggregate_score = lexicon_score
        elif lexicon_score >= 0.50:
            # Strong multi-concept match corroborated by vector evidence
            aggregate_score = round(max(lexicon_score, (lexicon_score * 0.8) + (vector_score * 0.2)), 4)
        elif lexicon_score > 0.0:
            # Minor concept match (e.g. 1 token out of 3): retain precise lexicon score without vector inflation
            aggregate_score = lexicon_score
        else:
            # When no lexicon concept matches, scale vector score with token Jaccard to prevent collision inflation
            t1_set = set(t1_words)
            t2_set = set(t2_words)
            jaccard = len(t1_set & t2_set) / max(len(t1_set | t2_set), 1)
            aggregate_score = round(vector_score * (0.2 + 0.8 * jaccard), 4)
            
        return {
            "lexicon_score": round(lexicon_score, 4),
            "vector_score": round(vector_score, 4),
            "aggregate_semantic_score": round(aggregate_score, 4),
            "concept_pairs": concept_pairs,
            "canonical_concepts_title1": canon_t1,
            "canonical_concepts_title2": canon_t2
        }
