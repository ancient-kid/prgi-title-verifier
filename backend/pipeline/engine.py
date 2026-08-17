"""
PRGI Unified Verification Pipeline Engine

Integrates Stages 1 through 5:
- Stage 1: Preprocessing & Anchor Extraction
- Stage 2: PRGI Guideline Blacklist Checks
- Stage 3: Frankentitle (Combination) Check
- Stage 4: Tri-Vector Similarity (Phonetic, Orthographic, Cross-Lingual Semantic)
- Stage 5: Verification Probability Aggregation & Diagnostic Formulation

Formula:
Verification Probability = max(0, 100% - Highest_Similarity_Score) * hard_rule_multiplier
"""

import time
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.config import (
    ORTHOGRAPHIC_THRESHOLD,
    OVERALL_REJECTION_THRESHOLD,
    PHONETIC_THRESHOLD,
    SEMANTIC_THRESHOLD,
    TOP_MATCHES_RETURN,
)
from backend.pipeline.stage1_preprocessor import extract_anchor_words
from backend.pipeline.stage2_guidelines import check_guidelines
from backend.pipeline.stage3_frankentitle import FrankentitleDetector
from backend.pipeline.stage4_orthographic import compute_orthographic_similarity
from backend.pipeline.stage4_phonetic import compare_phonetic_similarity, compute_phonetic_fingerprint
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine


class TitleVerificationEngine:
    def __init__(self, titles_index=None, lock_manager=None):
        self.titles_index = titles_index
        self.lock_manager = lock_manager
        self.frankentitle_detector = FrankentitleDetector()
        self.semantic_engine = SemanticSimilarityEngine()
        
        if titles_index:
            self.load_index(titles_index)

    def load_index(self, titles_index):
        """Update reference to loaded titles index."""
        self.titles_index = titles_index
        all_titles = set(titles_index.get_all_titles())
        all_anchors = set(titles_index.get_all_anchors())
        self.frankentitle_detector.load_titles(all_titles, all_anchors)

    def _get_ai_suggestions(
        self,
        raw_title: str,
        anchor_words: str,
        language: Optional[str],
        state: Optional[str],
        periodicity: Optional[str],
        skip_suggestions: bool
    ) -> List[Dict[str, Any]]:
        if skip_suggestions:
            return []
        try:
            from backend.pipeline.title_suggester import generate_title_suggestions
            return generate_title_suggestions(
                raw_title=raw_title,
                anchor_words=anchor_words,
                language=language or "English",
                state=state or "National",
                periodicity=periodicity or "Daily",
                engine_instance=self
            )
        except Exception as e:
            print(f"[Engine] AI Suggester error: {e}")
            return []

    def verify_title(
        self,
        raw_title: str,
        language: Optional[str] = None,
        state: Optional[str] = None,
        periodicity: Optional[str] = None,
        applicant_id: Optional[str] = None,
        skip_suggestions: bool = False
    ) -> Dict[str, Any]:
        """
        Execute full multi-stage verification pipeline for a submitted title.
        """
        start_time = time.perf_counter()
        
        # 0. Pending Application Lock Check
        if self.lock_manager:
            is_locked, lock_info = self.lock_manager.check_lock(raw_title)
            if is_locked and lock_info and lock_info.get("applicant_id") != applicant_id:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "raw_title": raw_title,
                    "verification_probability": 0.0,
                    "status": "Rejected",
                    "decision": "REJECTED_PENDING_COLLISION",
                    "execution_time_ms": elapsed_ms,
                    "reasons": [
                        {
                            "stage": "Pending Applications Lock",
                            "rule": "Concurrent Application Conflict",
                            "guideline_ref": "Lock Policy",
                            "explanation": (
                                f"Conflict: Title '{raw_title}' is currently locked under an active pending "
                                f"application submitted by applicant '{lock_info.get('applicant_id', 'Another User')}'. "
                                f"Lock expires in {lock_info.get('ttl_remaining', 0)} seconds."
                            )
                        }
                    ],
                    "stage_results": {
                        "pending_lock": {"passed": False, "lock_info": lock_info},
                        "stage1": None,
                        "stage2": None,
                        "stage3": None,
                        "stage4": None
                    },
                    "suggestions": [
                        f"Choose an alternate distinctive prefix or suffix for '{raw_title}'.",
                        "Wait for the active application lock window to expire if unconfirmed."
                    ],
                    "ai_suggestions": self._get_ai_suggestions(raw_title, raw_title, language, state, periodicity, skip_suggestions)
                }

        # Stage 1: Preprocessing, Structural Validation & Anchor Extraction
        s1_res = extract_anchor_words(raw_title)
        cleaned_title = s1_res["cleaned_title"]
        tokens = s1_res["tokens"]
        anchor_words = s1_res["anchor_words"]
        
        # 1A. Check structural invalidity (Prohibited Symbols, Math chars, Emojis, Pure Numbers)
        if not s1_res.get("is_valid_structure", True):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_type = s1_res.get("error_type", "STRUCTURAL_ERROR")
            decision_code = f"REJECTED_{error_type}"
            
            suggestions = []
            if error_type == "PROHIBITED_SYMBOLS":
                suggestions.append("Remove all symbols, signs, mathematical symbols ('+', '*', etc.), punctuation, and emojis from the title.")
                suggestions.append("Spell out words in full alphabetical text (e.g. use 'Plus' instead of '+', or 'Star' instead of '*').")
            elif error_type == "PURE_NUMERIC":
                suggestions.append("Combine numerical digits with substantive distinctive alphabetical words (e.g. 'Channel 24', 'Studio 365').")
                suggestions.append("Do not submit publication titles consisting exclusively of numbers or digits.")
            elif error_type in ("REPETITIVE_GIBBERISH", "UNPRONOUNCEABLE_GIBBERISH", "LOW_ENTROPY_GIBBERISH"):
                suggestions.append("Ensure all words in the title are meaningful and pronounceable in English or recognized Indian languages.")
                suggestions.append("Avoid random key mashing or unpronounceable character combinations (e.g. 'ghibrisg', 'qwrtp').")
                suggestions.append("If using an acronym, use standard, recognized abbreviations (e.g. 'BBC', 'NDTV', 'ISRO').")
            else:
                suggestions.append("Ensure the title contains valid text characters.")

            return {
                "raw_title": raw_title,
                "cleaned_title": cleaned_title,
                "anchor_words": anchor_words,
                "verification_probability": 0.0,
                "status": "Rejected",
                "decision": decision_code,
                "execution_time_ms": elapsed_ms,
                "reasons": [
                    {
                        "stage": "Stage 1: Structural & Symbol Verification",
                        "rule": s1_res["rule"],
                        "guideline_ref": s1_res["guideline_ref"],
                        "explanation": s1_res["rejection_reason"]
                    }
                ],
                "stage_results": {
                    "stage1": s1_res,
                    "stage2": None,
                    "stage3": None,
                    "stage4": None
                },
                "suggestions": suggestions
            }

        # 1B. Check for EXACT Match against already registered titles in PRGI Registry
        # If an exact registered title exists, this takes top precedence over generic/structural rules.
        if self.titles_index:
            exact_cand = self.titles_index.find_exact(cleaned_title)
            if exact_cand:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                reg_no = exact_cand.get("registration_no", "N/A")
                state = exact_cand.get("state", "N/A")
                lang = exact_cand.get("language", "N/A")
                period = exact_cand.get("periodicity", "N/A")
                orig_title = exact_cand.get("title", raw_title.upper())
                
                return {
                    "raw_title": raw_title,
                    "cleaned_title": cleaned_title,
                    "anchor_words": anchor_words,
                    "verification_probability": 0.0,
                    "status": "Rejected",
                    "decision": "REJECTED_ALREADY_REGISTERED",
                    "highest_similarity_score": 100.0,
                    "max_scores": {
                        "orthographic": 100.0,
                        "phonetic": 100.0,
                        "semantic": 100.0
                    },
                    "execution_time_ms": elapsed_ms,
                    "reasons": [
                        {
                            "stage": "Registry Search: Exact Title Conflict",
                            "rule": "Already Registered Title (Exact Match Violation)",
                            "guideline_ref": "PRP Act 2023 Section 5 / PRGI Guideline 5 (Identical Title Prohibition)",
                            "explanation": (
                                f"Direct Conflict: The title '{orig_title}' is already registered in the PRGI Registry "
                                f"(Registration No: {reg_no}, State: {state}, Language: {lang}, Periodicity: {period}). "
                                f"Under Section 5 of the Press and Registration of Periodicals Act, 2023 and PRGI Guideline 5, "
                                f"exact duplicates of existing registered titles cannot be allotted."
                            )
                        }
                    ],
                    "top_matches": [
                        {
                            "title": orig_title,
                            "registration_no": reg_no,
                            "language": lang,
                            "state": state,
                            "periodicity": period,
                            "orthographic_similarity": 1.0,
                            "phonetic_similarity": 1.0,
                            "semantic_similarity": 1.0,
                            "highest_similarity": 1.0,
                            "semantic_pairs": []
                        }
                    ],
                    "stage_results": {
                        "stage1": s1_res,
                        "stage2": None,
                        "stage3": None,
                        "stage4": {
                            "total_candidates_analyzed": 1,
                            "top_matches": [
                                {
                                    "title": orig_title,
                                    "registration_no": reg_no,
                                    "language": lang,
                                    "state": state,
                                    "periodicity": period,
                                    "orthographic_similarity": 1.0,
                                    "phonetic_similarity": 1.0,
                                    "semantic_similarity": 1.0,
                                    "highest_similarity": 1.0,
                                    "semantic_pairs": []
                                }
                            ]
                        }
                    },
                    "suggestions": [
                        f"Title '{raw_title}' is already an active registered publication and cannot be re-allocated.",
                        "Choose a distinctive, original title not present in the PRGI registry."
                    ]
                }

        # 1C. Check purely generic composition
        if s1_res["is_purely_generic"]:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "raw_title": raw_title,
                "cleaned_title": cleaned_title,
                "anchor_words": anchor_words,
                "verification_probability": 0.0,
                "status": "Rejected",
                "decision": "REJECTED_STAGE_1",
                "execution_time_ms": elapsed_ms,
                "reasons": [
                    {
                        "stage": "Stage 1: Pre-processing & Anchor Extraction",
                        "rule": "Pure Generic Title Violation",
                        "guideline_ref": "Guideline 8 (Generic Terms)",
                        "explanation": s1_res["rejection_reason"]
                    }
                ],
                "stage_results": {
                    "stage1": s1_res,
                    "stage2": None,
                    "stage3": None,
                    "stage4": None
                },
                "suggestions": [
                    f"Add a distinctive geographical anchor (e.g. 'Mumbai {raw_title.title()}').",
                    f"Add a specific thematic anchor (e.g. 'Vikas {raw_title.title()}').",
                    "Avoid names consisting exclusively of words like 'Daily', 'News', 'Express', 'Samachar'."
                ]
            }

        # Stage 2: Guideline Enforcement & Blacklist Checking
        s2_res = check_guidelines(cleaned_title, tokens, anchor_words=anchor_words)
        if not s2_res["passed"]:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            reasons = [
                {
                    "stage": "Stage 2: Guideline Enforcement",
                    "rule": v["rule"],
                    "guideline_ref": v["guideline_ref"],
                    "explanation": v["explanation"]
                }
                for v in s2_res["violations"]
            ]
            return {
                "raw_title": raw_title,
                "cleaned_title": cleaned_title,
                "anchor_words": anchor_words,
                "verification_probability": 0.0,
                "status": "Rejected",
                "decision": "REJECTED_STAGE_2",
                "execution_time_ms": elapsed_ms,
                "reasons": reasons,
                "stage_results": {
                    "stage1": s1_res,
                    "stage2": s2_res,
                    "stage3": None,
                    "stage4": None
                },
                "suggestions": [
                    "Remove prohibited security/enforcement terms (e.g. 'Police', 'Crime', 'CBI', 'Sarkar').",
                    "Ensure title does not falsely claim government, statutory, or judicial authority."
                ],
                "ai_suggestions": self._get_ai_suggestions(raw_title, anchor_words, language, state, periodicity, skip_suggestions)
            }

        # Stage 3: The Frankentitle Check
        s3_res = self.frankentitle_detector.check_combination(cleaned_title, tokens)
        if s3_res["is_frankentitle"]:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "raw_title": raw_title,
                "cleaned_title": cleaned_title,
                "anchor_words": anchor_words,
                "verification_probability": 0.0,
                "status": "Rejected",
                "decision": "REJECTED_STAGE_3",
                "execution_time_ms": elapsed_ms,
                "reasons": [
                    {
                        "stage": "Stage 3: Frankentitle Combination Check",
                        "rule": "Compound Title of Existing Registered Titles",
                        "guideline_ref": "Guideline 6 / Frankentitle Rule",
                        "explanation": s3_res["explanation"]
                    }
                ],
                "stage_results": {
                    "stage1": s1_res,
                    "stage2": s2_res,
                    "stage3": s3_res,
                    "stage4": None
                },
                "suggestions": [
                    f"Create an original title rather than combining '{' + '.join(s3_res['components'])}'.",
                    "Do not join established publication names together."
                ],
                "ai_suggestions": self._get_ai_suggestions(raw_title, anchor_words, language, state, periodicity, skip_suggestions)
            }

        # Stage 4: Similarity Checks across the 160k+ dataset
        top_matches = []
        max_ortho_score = 0.0
        max_phonetic_score = 0.0
        max_semantic_score = 0.0
        
        if self.titles_index:
            # Query fast candidate search from index
            candidates = self.titles_index.find_candidates(
                cleaned_title=cleaned_title,
                anchor_words=anchor_words,
                limit=100
            )
            
            for cand in candidates:
                cand_title = cand.get("title", "")
                cand_clean = cand.get("cleaned_title", cand_title.lower())
                cand_anchor = cand.get("anchor_words", cand_clean)
                
                # 4A: Phonetic comparison (on both full title and anchor)
                ph_score_full = compare_phonetic_similarity(cleaned_title, cand_clean)
                ph_score_anchor = compare_phonetic_similarity(anchor_words, cand_anchor) if anchor_words and cand_anchor else 0.0
                ph_score = max(ph_score_full, ph_score_anchor)
                
                # 4B: Orthographic comparison (on both full title and anchor)
                ortho_dict_full = compute_orthographic_similarity(cleaned_title, cand_clean)
                ortho_dict_anchor = compute_orthographic_similarity(anchor_words, cand_anchor) if anchor_words and cand_anchor else {"aggregate_orthographic_score": 0.0}
                
                # If exact title match or high anchor similarity
                if cleaned_title == cand_clean:
                    ortho_score = 1.0
                elif anchor_words and cand_anchor and anchor_words == cand_anchor:
                    ortho_score = 0.95
                elif anchor_words and cand_anchor:
                    # When both titles have distinct anchors, anchor comparison takes precedence
                    ortho_score = max(ortho_dict_anchor["aggregate_orthographic_score"], ortho_dict_full["aggregate_orthographic_score"] * 0.70)
                else:
                    ortho_score = ortho_dict_full["aggregate_orthographic_score"] * 0.75
                
                # 4C: Semantic comparison
                sem_dict = self.semantic_engine.compare_semantic_similarity(cleaned_title, cand_clean)
                sem_score = sem_dict["aggregate_semantic_score"]
                
                max_score_for_cand = max(ortho_score, ph_score, sem_score)
                
                # Check exact token overlap between target anchor and candidate non-generic anchor
                cand_non_gen = set(cand_anchor.split()) if cand_anchor else set(cand_clean.split())
                anchor_token_set = set(anchor_words.split()) if anchor_words else set(cleaned_title.split())
                common_tokens = anchor_token_set.intersection(cand_non_gen)
                if common_tokens:
                    # If candidate shares exact non-generic token, boost candidate similarity
                    overlap_ratio = len(common_tokens) / max(len(anchor_token_set), len(cand_non_gen))
                    max_score_for_cand = max(max_score_for_cand, overlap_ratio * 0.95)
                    
                max_ortho_score = max(max_ortho_score, ortho_score)
                max_phonetic_score = max(max_phonetic_score, ph_score)
                max_semantic_score = max(max_semantic_score, sem_score)
                
                top_matches.append({
                    "title": cand_title,
                    "registration_no": cand.get("registration_no", "N/A"),
                    "language": cand.get("language", "N/A"),
                    "state": cand.get("state", "N/A"),
                    "periodicity": cand.get("periodicity", "N/A"),
                    "orthographic_similarity": round(ortho_score, 4),
                    "phonetic_similarity": round(ph_score, 4),
                    "semantic_similarity": round(sem_score, 4),
                    "highest_similarity": round(max_score_for_cand, 4),
                    "semantic_pairs": sem_dict.get("concept_pairs", [])
                })
                
            # Sort top matches by highest similarity descending
            top_matches.sort(key=lambda x: x["highest_similarity"], reverse=True)
            top_matches = top_matches[:TOP_MATCHES_RETURN]

        # Stage 5: Verification Probability Calculation
        highest_similarity = max(max_ortho_score, max_phonetic_score, max_semantic_score)
        
        # Formula: Verification Probability = max(0, 100% - Highest_Similarity_Score)
        # Convert to percentage
        highest_sim_pct = round(highest_similarity * 100, 1)
        verification_prob_pct = round(max(0.0, 100.0 - highest_sim_pct), 1)
        
        reasons = []
        status = "Approved"
        decision = "APPROVED"
        
        if highest_similarity >= OVERALL_REJECTION_THRESHOLD:
            status = "Rejected"
            decision = "REJECTED_SIMILARITY"
            top_match = top_matches[0] if top_matches else None
            
            if top_match:
                if top_match["phonetic_similarity"] >= PHONETIC_THRESHOLD:
                    reasons.append({
                        "stage": "Stage 4A: Phonetic Similarity Check",
                        "rule": f"Phonetic Similarity ({round(top_match['phonetic_similarity'] * 100, 1)}%)",
                        "guideline_ref": "Guideline 5 (Phonetic Equivalence)",
                        "explanation": (
                            f"Phonetic Similarity ({round(top_match['phonetic_similarity'] * 100, 1)}%): "
                            f"Sounds deceptively identical/similar to currently registered title '{top_match['title']}'."
                        )
                    })
                if top_match["orthographic_similarity"] >= ORTHOGRAPHIC_THRESHOLD:
                    reasons.append({
                        "stage": "Stage 4B: Orthographic Similarity Check",
                        "rule": f"String Distance Match ({round(top_match['orthographic_similarity'] * 100, 1)}%)",
                        "guideline_ref": "Guideline 5 (Deceptive Similarity)",
                        "explanation": (
                            f"Orthographic Similarity ({round(top_match['orthographic_similarity'] * 100, 1)}%): "
                            f"Close spelling/visual resemblance to registered title '{top_match['title']}'."
                        )
                    })
                if top_match["semantic_similarity"] >= SEMANTIC_THRESHOLD:
                    reasons.append({
                        "stage": "Stage 4C: Cross-Lingual Semantic Similarity",
                        "rule": f"Cross-Lingual Equivalence ({round(top_match['semantic_similarity'] * 100, 1)}%)",
                        "guideline_ref": "Guideline 11 (Cross-Lingual Translation)",
                        "explanation": (
                            f"Cross-Lingual Semantic Similarity ({round(top_match['semantic_similarity'] * 100, 1)}%): "
                            f"Shares identical meaning with registered title '{top_match['title']}'. "
                            f"Matched concepts: {', '.join(top_match['semantic_pairs']) if top_match['semantic_pairs'] else 'Cross-lingual semantic embedding proximity'}."
                        )
                    })
                if not reasons:
                    reasons.append({
                        "stage": "Stage 4: Similarity Engine",
                        "rule": f"Combined Similarity ({highest_sim_pct}%)",
                        "guideline_ref": "Guideline 5 (Deceptive Resemblance)",
                        "explanation": f"High resemblance ({highest_sim_pct}%) to registered title '{top_match['title']}'."
                    })
        elif highest_similarity >= 0.45:
            status = "Review Needed"
            decision = "MODERATE_SIMILARITY_FLAG"
            reasons.append({
                "stage": "Stage 4: Similarity Evaluation",
                "rule": f"Moderate Similarity ({highest_sim_pct}%)",
                "guideline_ref": "Officer Discretion",
                "explanation": f"Moderate similarity ({highest_sim_pct}%) detected against existing title '{top_matches[0]['title'] if top_matches else ''}'. Manual PRGI officer review recommended."
            })
        else:
            status = "Approved"
            decision = "APPROVED"
            reasons.append({
                "stage": "Verification Funnel",
                "rule": "Distinctiveness Verification Passed",
                "guideline_ref": "PRP Act 2023 Compliant",
                "explanation": f"High distinctiveness score ({verification_prob_pct}%). No deceptive similarity or guideline conflicts detected."
            })

        suggestions = []
        ai_suggestions = []
        if status != "Approved":
            base_anchor = anchor_words if anchor_words else cleaned_title
            suggestions.append(f"Consider prefixing a regional identifier, e.g., 'Maharashtra {raw_title.title()}'.")
            suggestions.append(f"Modify the distinctive keyword to be unique from '{top_matches[0]['title'] if top_matches else ''}'.")
            suggestions.append("Ensure periodicity modifiers do not mimic registered brands.")
            
            if not skip_suggestions:
                try:
                    from backend.pipeline.title_suggester import generate_title_suggestions
                    ai_suggestions = generate_title_suggestions(
                        raw_title=raw_title,
                        anchor_words=anchor_words,
                        language=language or "English",
                        state=state or "National",
                        periodicity=periodicity or "Daily",
                        engine_instance=self
                    )
                except Exception as e:
                    print(f"[Engine] AI Title Suggester error: {e}")
        else:
            suggestions.append("Title meets PRGI uniqueness standards and is eligible for formal application filing.")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        return {
            "raw_title": raw_title,
            "cleaned_title": cleaned_title,
            "anchor_words": anchor_words,
            "verification_probability": verification_prob_pct,
            "status": status,
            "decision": decision,
            "highest_similarity_score": highest_sim_pct,
            "max_scores": {
                "orthographic": round(max_ortho_score * 100, 1),
                "phonetic": round(max_phonetic_score * 100, 1),
                "semantic": round(max_semantic_score * 100, 1)
            },
            "execution_time_ms": elapsed_ms,
            "reasons": reasons,
            "top_matches": top_matches,
            "stage_results": {
                "stage1": s1_res,
                "stage2": s2_res,
                "stage3": s3_res,
                "stage4": {
                    "total_candidates_analyzed": len(candidates) if self.titles_index else 0,
                    "top_matches": top_matches
                }
            },
            "suggestions": suggestions,
            "ai_suggestions": ai_suggestions
        }
