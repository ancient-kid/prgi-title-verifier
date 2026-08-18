"""
High-Performance Data Ingestion, Indexing, and Search Engine

Loads and indexes 82,000+ to 160,000+ registered titles with sub-millisecond candidate retrieval:
1. Fast Word Token Inverted Index
2. Character 3-Gram Inverted Index (for instant fuzzy string candidates)
3. Phonetic Metaphone & Indic-Soundex Inverted Index
4. Exact Match Hash Sets & Anchor Sets
"""

import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from backend.config import DATA_DIR, TITLES_FILE, TITLES_PARQUET_FILE, TITLES_SQLITE_FILE
from backend.pipeline.stage1_preprocessor import clean_text, extract_anchor_words
from backend.pipeline.stage4_phonetic import compute_phonetic_fingerprint, get_double_metaphone, indic_soundex
from backend.pipeline.stage4_semantic import CROSS_LINGUAL_LEXICON, INDIAN_TO_ENGLISH


class TitleIndex:
    def __init__(self):
        self.titles_data: List[Dict[str, Any]] = []
        self.all_titles: List[str] = []
        self.all_anchors: List[str] = []
        self.title_to_id: Dict[str, int] = {}
        
        # Inverted Indices
        self.word_index: Dict[str, List[int]] = defaultdict(list)
        self.ngram_index: Dict[str, List[int]] = defaultdict(list)
        self.phonetic_index: Dict[str, List[int]] = defaultdict(list)
        self.indic_soundex_index: Dict[str, List[int]] = defaultdict(list)
        self.concept_index: Dict[str, List[int]] = defaultdict(list)
        
        self.is_loaded = False

    def get_all_titles(self) -> List[str]:
        return self.all_titles

    def get_all_anchors(self) -> List[str]:
        return self.all_anchors

    def get_total_count(self) -> int:
        return len(self.titles_data)

    def load_data(self, file_path: Optional[Path] = None, max_rows: Optional[int] = None) -> int:
        """
        Load titles from Parquet or Excel cache in sub-second time.
        """
        start_time = time.perf_counter()
        target_file = file_path or TITLES_FILE
        
        df = None
        
        # 1. Try Parquet cache first for instant sub-second loading
        if TITLES_PARQUET_FILE.exists():
            try:
                df = pd.read_parquet(TITLES_PARQUET_FILE)
                if max_rows and len(df) > max_rows:
                    df = df.iloc[:max_rows]
                print(f"[TitleIndex] Loaded {len(df)} titles from Parquet cache in {round((time.perf_counter() - start_time)*1000, 1)}ms.")
            except Exception as e:
                print(f"[TitleIndex] Parquet read error: {e}")

        # 2. Try Excel source file if parquet not present
        if df is None and target_file.exists():
            try:
                print(f"[TitleIndex] Reading Excel dataset from {target_file}...")
                df = pd.read_excel(target_file, nrows=max_rows)
                for col in df.columns:
                    df[col] = df[col].astype(str)
                # Cache to parquet for next sub-second loads
                try:
                    df.to_parquet(TITLES_PARQUET_FILE)
                except Exception:
                    pass
            except Exception as e:
                print(f"[TitleIndex] Excel reading error: {e}")

        # 3. Fallback rich seed dataset
        if df is None or len(df) == 0:
            print("[TitleIndex] Creating comprehensive seed dataset...")
            df = self._generate_seed_dataset()

        # Standardize column names
        df = self._standardize_dataframe(df)
        
        # Build in-memory indices in < 0.1s
        self._build_indices(df)
        self._sync_to_db()
        self.is_loaded = True
        
        elapsed = round(time.perf_counter() - start_time, 3)
        print(f"[TitleIndex] Successfully indexed {len(self.titles_data)} registered titles in {elapsed}s.")
        return len(self.titles_data)

    def _sync_to_db(self):
        """Ensure registered titles are populated in relational DB with B-tree indexes."""
        try:
            from backend.database import RegisteredTitleModel, SessionLocal, init_db
            init_db()
            db = SessionLocal()
            try:
                count = db.query(RegisteredTitleModel).count()
                if count < len(self.titles_data):
                    mappings = [
                        {
                            "id": item["id"] + 1,
                            "title": item["title"],
                            "cleaned_title": item["cleaned_title"],
                            "anchor_words": item.get("anchor_words", ""),
                            "registration_no": item.get("registration_no", "N/A"),
                            "language": item.get("language", "English"),
                            "state": item.get("state", "National"),
                            "periodicity": item.get("periodicity", "Daily"),
                            "publisher": item.get("publisher", None),
                            "phonetic_metaphone": item.get("phonetic_metaphone", None),
                            "indic_soundex": item.get("indic_soundex", None),
                        }
                        for item in self.titles_data
                    ]
                    db.bulk_insert_mappings(RegisteredTitleModel, mappings)
                    db.commit()
                    print(f"[TitleIndex] Synchronized {len(mappings)} titles to relational database with B-tree indexes.")
            except Exception as e:
                db.rollback()
                print(f"[TitleIndex] DB sync notice: {e}")
            finally:
                db.close()
        except Exception as e:
            print(f"[TitleIndex] DB connection notice: {e}")

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map diverse column naming variations to standard schema."""
        col_map = {}
        assigned = set()
        for c in df.columns:
            c_low = str(c).lower().strip().replace(" ", "_")
            if "title" not in assigned and any(k in c_low for k in ["title_name", "titlename", "title"]):
                col_map[c] = "title"
                assigned.add("title")
            elif "registration_no" not in assigned and any(k in c_low for k in ["reg_no", "registration_number", "regn_no", "reg"]):
                col_map[c] = "registration_no"
                assigned.add("registration_no")
            elif "language" not in assigned and "lang" in c_low:
                col_map[c] = "language"
                assigned.add("language")
            elif "state" not in assigned and any(k in c_low for k in ["publication_state", "state"]):
                col_map[c] = "state"
                assigned.add("state")
            elif "periodicity" not in assigned and any(k in c_low for k in ["periodicity", "period"]):
                col_map[c] = "periodicity"
                assigned.add("periodicity")
            elif "publisher" not in assigned and any(k in c_low for k in ["publisher", "owner"]):
                col_map[c] = "publisher"
                assigned.add("publisher")
                
        df = df.rename(columns=col_map)
        
        # Deduplicate columns if any duplicates exist
        df = df.loc[:, ~df.columns.duplicated()]
        
        if "title" not in df.columns:
            df["title"] = df.iloc[:, 0].astype(str)
        if "registration_no" not in df.columns:
            df["registration_no"] = [f"PRGI/REG/{i+100000}" for i in range(len(df))]
        if "language" not in df.columns:
            df["language"] = "English"
        if "state" not in df.columns:
            df["state"] = "National"
        if "periodicity" not in df.columns:
            df["periodicity"] = "Daily"
            
        df = df.dropna(subset=["title"])
        df["title"] = df["title"].astype(str).str.strip()
        df = df[df["title"].str.len() > 1]
        return df

    def _build_indices(self, df: pd.DataFrame):
        """Construct multi-layer inverted indices optimized for instantaneous lookup."""
        self.titles_data = []
        self.all_titles = []
        self.all_anchors = []
        self.title_to_id = {}
        
        self.word_index = defaultdict(list)
        self.ngram_index = defaultdict(list)
        self.phonetic_index = defaultdict(list)
        self.indic_soundex_index = defaultdict(list)
        self.concept_index = defaultdict(list)
        
        titles_list = df["title"].tolist()
        reg_list = df["registration_no"].tolist() if "registration_no" in df.columns else ["N/A"] * len(df)
        lang_list = df["language"].tolist() if "language" in df.columns else ["English"] * len(df)
        state_list = df["state"].tolist() if "state" in df.columns else ["National"] * len(df)
        period_list = df["periodicity"].tolist() if "periodicity" in df.columns else ["Daily"] * len(df)
        
        for entry_id in range(len(titles_list)):
            title_str = str(titles_list[entry_id]).strip()
            clean_str = clean_text(title_str)
            if not clean_str:
                continue
                
            words = clean_str.split()
            
            # Simple fast anchor extraction
            from backend.pipeline.stage1_preprocessor import GENERIC_MODIFIERS
            non_gen = [w for w in words if w not in GENERIC_MODIFIERS]
            anchor = " ".join(non_gen) if non_gen else ""
            
            item = {
                "id": entry_id,
                "title": title_str,
                "cleaned_title": clean_str,
                "anchor_words": anchor,
                "registration_no": str(reg_list[entry_id]),
                "language": str(lang_list[entry_id]),
                "state": str(state_list[entry_id]),
                "periodicity": str(period_list[entry_id])
            }
            
            self.titles_data.append(item)
            self.all_titles.append(clean_str)
            if anchor:
                self.all_anchors.append(anchor)
            self.title_to_id[clean_str] = entry_id
            
            # 1. Word token indexing
            for w in words:
                if len(w) >= 2:
                    self.word_index[w].append(entry_id)
                    
                    # 2. Phonetic token indexing (both primary and secondary Double Metaphone keys)
                    p_meta_prim, p_meta_sec = get_double_metaphone(w)
                    if p_meta_prim:
                        self.phonetic_index[p_meta_prim].append(entry_id)
                    if p_meta_sec and p_meta_sec != p_meta_prim:
                        self.phonetic_index[p_meta_sec].append(entry_id)
                        
                    p_ind = indic_soundex(w)
                    if p_ind:
                        self.indic_soundex_index[p_ind].append(entry_id)
                        
                    # 3. Semantic Concept indexing
                    if w in CROSS_LINGUAL_LEXICON:
                        self.concept_index[w].append(entry_id)
                    elif w in INDIAN_TO_ENGLISH:
                        for eng_c in INDIAN_TO_ENGLISH[w]:
                            self.concept_index[eng_c].append(entry_id)
                    
            # 4. Character 3-gram indexing (for anchor or short title)
            target_gram = anchor if anchor else clean_str
            padded = f"_{target_gram}_"
            for i in range(len(padded) - 2):
                gram = padded[i:i+3]
                self.ngram_index[gram].append(entry_id)

    def find_exact(self, cleaned_title: str) -> Optional[Dict[str, Any]]:
        """
        O(1) lookup for exact title match in registered titles registry.
        """
        clean = cleaned_title.strip().lower()
        if clean in self.title_to_id:
            tid = self.title_to_id[clean]
            return self.titles_data[tid]
        return None

    def find_candidates(
        self,
        cleaned_title: str,
        anchor_words: str = "",
        limit: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Fast multi-vector inverted index search in < 1ms with weighted candidate ranking.
        """
        if not self.titles_data:
            return []
            
        candidate_scores: Dict[int, float] = defaultdict(float)
        matched_tokens_per_cand: Dict[int, Set[str]] = defaultdict(set)
        
        # 1. Exact Anchor Word matches
        if anchor_words:
            for at in anchor_words.split():
                if at in self.word_index:
                    for tid in self.word_index[at]:
                        candidate_scores[tid] += 4.0
                        matched_tokens_per_cand[tid].add(at)
                    
        # 2. Word token matches
        tokens = cleaned_title.split()
        for t in tokens:
            if t in self.word_index:
                for tid in self.word_index[t]:
                    candidate_scores[tid] += 3.0
                    matched_tokens_per_cand[tid].add(t)
                
            # 3. Phonetic matches (primary and secondary Double Metaphone + Indic-Soundex)
            p_prim, p_sec = get_double_metaphone(t)
            if p_prim in self.phonetic_index:
                for tid in self.phonetic_index[p_prim][:120]:
                    candidate_scores[tid] += 1.5
            if p_sec and p_sec != p_prim and p_sec in self.phonetic_index:
                for tid in self.phonetic_index[p_sec][:120]:
                    candidate_scores[tid] += 1.2
                
            p_ind = indic_soundex(t)
            if p_ind in self.indic_soundex_index:
                for tid in self.indic_soundex_index[p_ind][:120]:
                    candidate_scores[tid] += 1.5
                
            # 4. Semantic Concept alias matches
            if t in CROSS_LINGUAL_LEXICON:
                if t in self.concept_index:
                    for tid in self.concept_index[t]:
                        candidate_scores[tid] += 3.0
                        matched_tokens_per_cand[tid].add(t)
            elif t in INDIAN_TO_ENGLISH:
                for eng_c in INDIAN_TO_ENGLISH[t]:
                    if eng_c in self.concept_index:
                        for tid in self.concept_index[eng_c]:
                            candidate_scores[tid] += 3.0
                            matched_tokens_per_cand[tid].add(t)
                
        # 5. Multi-token / Multi-concept boost (titles matching 2+ words/concepts get prioritized)
        for tid, matched_set in matched_tokens_per_cand.items():
            if len(matched_set) > 1:
                candidate_scores[tid] += len(matched_set) * 4.0

        # 6. Trigram matches if candidate scores are sparse (< 30 candidates)
        if len(candidate_scores) < 30:
            target_gram = anchor_words if anchor_words else cleaned_title
            padded = f"_{target_gram}_"
            for i in range(len(padded) - 2):
                gram = padded[i:i+3]
                if gram in self.ngram_index:
                    for tid in self.ngram_index[gram][:50]:
                        candidate_scores[tid] += 0.8
                    
        if not candidate_scores:
            return []
            
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        selected_ids = [tid for tid, _ in sorted_candidates[:limit]]
        return [self.titles_data[tid] for tid in selected_ids]

    def search_titles(self, query: str, limit: int = 30, db: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        PostgreSQL B-tree indexed search across registered titles database.
        
        Executes index-optimized equality and prefix queries leveraging B-tree indexes
        on title, cleaned_title, anchor_words, and registration_no without full-table scans.
        Prioritizes exact B-tree matches first, followed by indexed prefix matches.
        """
        raw_q = query.strip() if query else ""
        clean_q = clean_text(raw_q) if raw_q else ""

        try:
            from sqlalchemy import or_
            from backend.database import RegisteredTitleModel, SessionLocal

            session = db if db is not None else SessionLocal()
            should_close = db is None

            try:
                if not clean_q and not raw_q:
                    # B-tree index scan on primary key id
                    records = session.query(RegisteredTitleModel).order_by(RegisteredTitleModel.id).limit(limit).all()
                    if records:
                        return [
                            {
                                "id": r.id - 1 if r.id else 0,
                                "title": r.title,
                                "cleaned_title": r.cleaned_title,
                                "anchor_words": r.anchor_words or "",
                                "registration_no": r.registration_no or "N/A",
                                "language": r.language or "English",
                                "state": r.state or "National",
                                "periodicity": r.periodicity or "Daily",
                                "publisher": r.publisher or ""
                            }
                            for r in records
                        ]
                else:
                    seen_ids = set()
                    ordered_records = []

                    # Tier 1: Exact B-tree match on cleaned_title, title, registration_no, anchor_words
                    t1_conds = []
                    if raw_q:
                        t1_conds.append(RegisteredTitleModel.title == raw_q)
                        t1_conds.append(RegisteredTitleModel.registration_no == raw_q)
                    if clean_q:
                        t1_conds.append(RegisteredTitleModel.cleaned_title == clean_q)
                        t1_conds.append(RegisteredTitleModel.anchor_words == clean_q)

                    if t1_conds:
                        t1_records = session.query(RegisteredTitleModel).filter(or_(*t1_conds)).limit(limit).all()
                        for r in t1_records:
                            if r.id not in seen_ids:
                                seen_ids.add(r.id)
                                ordered_records.append(r)

                    # Tier 2: B-tree Prefix match on full title, cleaned_title, registration_no
                    if len(ordered_records) < limit:
                        t2_conds = []
                        if raw_q:
                            t2_conds.append(RegisteredTitleModel.title.like(f"{raw_q}%"))
                            t2_conds.append(RegisteredTitleModel.registration_no.like(f"{raw_q}%"))
                        if clean_q:
                            t2_conds.append(RegisteredTitleModel.cleaned_title.like(f"{clean_q}%"))
                            t2_conds.append(RegisteredTitleModel.anchor_words.like(f"{clean_q}%"))

                        if t2_conds:
                            remaining = limit - len(ordered_records)
                            t2_records = session.query(RegisteredTitleModel).filter(or_(*t2_conds)).limit(remaining + len(seen_ids)).all()
                            for r in t2_records:
                                if r.id not in seen_ids:
                                    seen_ids.add(r.id)
                                    ordered_records.append(r)
                                    if len(ordered_records) >= limit:
                                        break

                    # Tier 3: Token / Anchor prefix matches if space remains
                    if len(ordered_records) < limit and clean_q:
                        tokens = [t for t in clean_q.split() if len(t) >= 3]
                        for tok in tokens:
                            if len(ordered_records) >= limit:
                                break
                            remaining = limit - len(ordered_records)
                            t3_conds = [
                                RegisteredTitleModel.anchor_words == tok,
                                RegisteredTitleModel.anchor_words.like(f"{tok}%"),
                                RegisteredTitleModel.cleaned_title.like(f"{tok}%")
                            ]
                            t3_records = session.query(RegisteredTitleModel).filter(or_(*t3_conds)).limit(remaining + len(seen_ids)).all()
                            for r in t3_records:
                                if r.id not in seen_ids:
                                    seen_ids.add(r.id)
                                    ordered_records.append(r)
                                    if len(ordered_records) >= limit:
                                        break

                    if ordered_records:
                        return [
                            {
                                "id": r.id - 1 if r.id else 0,
                                "title": r.title,
                                "cleaned_title": r.cleaned_title,
                                "anchor_words": r.anchor_words or "",
                                "registration_no": r.registration_no or "N/A",
                                "language": r.language or "English",
                                "state": r.state or "National",
                                "periodicity": r.periodicity or "Daily",
                                "publisher": r.publisher or ""
                            }
                            for r in ordered_records
                        ]

            finally:
                if should_close:
                    session.close()

        except Exception as e:
            print(f"[Search] B-tree search notice: {e}")

        # In-memory fallback if DB query returned empty or during cold boot
        if not clean_q and not raw_q:
            return self.titles_data[:limit]

        cand_matches = []
        # Exact first
        for item in self.titles_data:
            if item["cleaned_title"] == clean_q or item["title"] == raw_q or item["registration_no"] == raw_q:
                cand_matches.append(item)
                if len(cand_matches) >= limit:
                    return cand_matches

        # Prefix second
        for item in self.titles_data:
            if item not in cand_matches and (item["cleaned_title"].startswith(clean_q) or item["title"].startswith(raw_q)):
                cand_matches.append(item)
                if len(cand_matches) >= limit:
                    return cand_matches

        # Substring third
        for item in self.titles_data:
            if item not in cand_matches and (clean_q in item["cleaned_title"] or raw_q in item["title"]):
                cand_matches.append(item)
                if len(cand_matches) >= limit:
                    break

        return cand_matches

    def _generate_seed_dataset(self) -> pd.DataFrame:
        """Seed dataset containing famous Indian registered titles."""
        sample_records = [
            {"title": "The Times of India", "language": "English", "state": "Maharashtra", "periodicity": "Daily"},
            {"title": "The Hindu", "language": "English", "state": "Tamil Nadu", "periodicity": "Daily"},
            {"title": "The Indian Express", "language": "English", "state": "Delhi", "periodicity": "Daily"},
            {"title": "Hindustan Times", "language": "English", "state": "Delhi", "periodicity": "Daily"},
            {"title": "The Telegraph", "language": "English", "state": "West Bengal", "periodicity": "Daily"},
            {"title": "Deccan Chronicle", "language": "English", "state": "Telangana", "periodicity": "Daily"},
            {"title": "The Economic Times", "language": "English", "state": "Maharashtra", "periodicity": "Daily"},
            {"title": "Dainik Jagran", "language": "Hindi", "state": "Uttar Pradesh", "periodicity": "Daily"},
            {"title": "Dainik Bhaskar", "language": "Hindi", "state": "Madhya Pradesh", "periodicity": "Daily"},
            {"title": "Amar Ujala", "language": "Hindi", "state": "Uttar Pradesh", "periodicity": "Daily"},
            {"title": "Punjab Kesari", "language": "Hindi", "state": "Punjab", "periodicity": "Daily"},
            {"title": "Rajasthan Patrika", "language": "Hindi", "state": "Rajasthan", "periodicity": "Daily"},
            {"title": "Namaskar India", "language": "Hindi", "state": "Delhi", "periodicity": "Daily"},
            {"title": "Pratidin Sandhya", "language": "Hindi", "state": "West Bengal", "periodicity": "Daily"},
            {"title": "Jan Vani", "language": "Hindi", "state": "Uttar Pradesh", "periodicity": "Daily"},
            {"title": "Dainik Prabhat", "language": "Hindi", "state": "Uttar Pradesh", "periodicity": "Daily"},
            {"title": "Anandabazar Patrika", "language": "Bengali", "state": "West Bengal", "periodicity": "Daily"},
            {"title": "Bartaman", "language": "Bengali", "state": "West Bengal", "periodicity": "Daily"},
            {"title": "Lokmat", "language": "Marathi", "state": "Maharashtra", "periodicity": "Daily"},
            {"title": "Daily Sakal", "language": "Marathi", "state": "Maharashtra", "periodicity": "Daily"},
            {"title": "Dina Thanthi", "language": "Tamil", "state": "Tamil Nadu", "periodicity": "Daily"},
            {"title": "Dinamalar", "language": "Tamil", "state": "Tamil Nadu", "periodicity": "Daily"},
            {"title": "Eenadu", "language": "Telugu", "state": "Andhra Pradesh", "periodicity": "Daily"},
            {"title": "Sakshi", "language": "Telugu", "state": "Andhra Pradesh", "periodicity": "Daily"},
            {"title": "Malayala Manorama", "language": "Malayalam", "state": "Kerala", "periodicity": "Daily"},
            {"title": "Mathrubhumi", "language": "Malayalam", "state": "Kerala", "periodicity": "Daily"},
            {"title": "Gujarat Samachar", "language": "Gujarati", "state": "Gujarat", "periodicity": "Daily"},
            {"title": "Sandesh", "language": "Gujarati", "state": "Gujarat", "periodicity": "Daily"},
            {"title": "Ajit", "language": "Punjabi", "state": "Punjab", "periodicity": "Daily"},
            {"title": "Inquilab", "language": "Urdu", "state": "Maharashtra", "periodicity": "Daily"},
            {"title": "The Siasat Daily", "language": "Urdu", "state": "Telangana", "periodicity": "Daily"}
        ]
        return pd.DataFrame(sample_records)
