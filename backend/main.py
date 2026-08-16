"""
PRGI Title Verification System - High-Performance FastAPI Application
"""

import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.config import BASE_DIR, HOST, PORT
from backend.data_loader import TitleIndex
from backend.database import PRGIGuidelineModel, RegisteredTitleModel, TitleApplicationModel, get_db, init_db
from backend.lock_manager import LockManager
from backend.models.schemas import (
    ActiveLockItem,
    BatchVerificationRequest,
    BatchVerificationResponse,
    GuidelineItem,
    LockApplicationRequest,
    LockApplicationResponse,
    SystemHealthResponse,
    TitleVerificationRequest,
    TitleVerificationResponse,
)
from backend.pipeline.engine import TitleVerificationEngine

# Global singletons
titles_index = TitleIndex()
lock_manager = LockManager()
engine = TitleVerificationEngine(titles_index=titles_index, lock_manager=lock_manager)

# Ensure data and db are loaded on module load
init_db()
if not titles_index.is_loaded:
    titles_index.load_data()
    engine.load_index(titles_index)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB and 160k+ dataset index are ready
    if not titles_index.is_loaded:
        init_db()
        titles_index.load_data()
        engine.load_index(titles_index)
    print(f"[Startup] Verification Engine ready with {titles_index.get_total_count()} registered titles indexed.")
    yield
    print("[Shutdown] Cleaning up resources...")


app = FastAPI(
    title="PRGI Automated Title Verification Engine",
    description="Automated NLP, Phonetic, Orthographic, and Cross-Lingual Semantic Title Verification for the Press Registrar General of India (PRGI)",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"


# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.get("/api/health", response_model=SystemHealthResponse)
def health_check():
    """System status, index statistics, and loaded models."""
    return {
        "status": "healthy",
        "database_connected": True,
        "total_registered_titles": titles_index.get_total_count(),
        "active_locks_count": len(lock_manager.list_active_locks()),
        "models_loaded": {
            "inverted_index": titles_index.is_loaded,
            "metaphone_phonetic": True,
            "indic_soundex": True,
            "multilingual_semantic": engine.semantic_engine.is_loaded
        },
        "version": "2.0.0"
    }


@app.post("/api/verify", response_model=TitleVerificationResponse)
def verify_title(req: TitleVerificationRequest, db: Session = Depends(get_db)):
    """
    Run full 5-stage verification funnel for a submitted title.
    """
    result = engine.verify_title(
        raw_title=req.title,
        language=req.language,
        state=req.state,
        periodicity=req.periodicity,
        applicant_id=req.applicant_id
    )
    return result


@app.post("/api/batch-verify", response_model=BatchVerificationResponse)
def batch_verify_titles(req: BatchVerificationRequest):
    """
    Process batch list of candidate titles with aggregate stats.
    """
    start_time = time.perf_counter()
    results = []
    appr_cnt = 0
    rej_cnt = 0
    rev_cnt = 0
    
    for t in req.titles:
        t_str = t.strip()
        if not t_str:
            continue
        res = engine.verify_title(
            raw_title=t_str,
            language=req.language,
            state=req.state,
            periodicity=req.periodicity
        )
        if res["status"] == "Approved":
            appr_cnt += 1
        elif res["status"] == "Rejected":
            rej_cnt += 1
        else:
            rev_cnt += 1
        results.append(res)
        
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    return {
        "total_processed": len(results),
        "approved_count": appr_cnt,
        "rejected_count": rej_cnt,
        "review_needed_count": rev_cnt,
        "execution_time_ms": elapsed_ms,
        "results": results
    }


@app.post("/api/apply", response_model=LockApplicationResponse)
def submit_application(req: LockApplicationRequest, db: Session = Depends(get_db)):
    """
    Apply for a title and acquire pending lock (preventing concurrent duplicates).
    """
    # 1. Run Verification Check
    ver_res = engine.verify_title(
        raw_title=req.title,
        language=req.language,
        state=req.state,
        periodicity=req.periodicity,
        applicant_id=req.applicant_id
    )
    
    # If hard rejected by pipeline rules
    if ver_res["verification_probability"] < 40.0 and ver_res["status"] == "Rejected":
        reasons_summary = "; ".join(r["explanation"] for r in ver_res["reasons"])
        return {
            "success": False,
            "message": f"Application cannot be submitted because the title failed verification: {reasons_summary}",
            "lock_info": None,
            "application_no": None
        }

    # 2. Acquire Pending Application Lock
    success, err_msg, lock_data = lock_manager.acquire_lock(
        title=req.title,
        applicant_id=req.applicant_id,
        applicant_name=req.applicant_name or "Anonymous",
        ttl_seconds=req.ttl_seconds or 600
    )
    
    if not success:
        return {
            "success": False,
            "message": err_msg or "Failed to lock title due to active pending application conflict.",
            "lock_info": lock_data,
            "application_no": None
        }
        
    app_no = f"PRGI-APP-{uuid.uuid4().hex[:8].upper()}"
    
    # 3. Log to Relational DB
    try:
        app_record = TitleApplicationModel(
            application_no=app_no,
            title=req.title,
            applicant_id=req.applicant_id,
            applicant_name=req.applicant_name,
            applicant_email=req.applicant_email,
            language=req.language,
            state=req.state,
            periodicity=req.periodicity,
            verification_probability=ver_res["verification_probability"],
            status=ver_res["status"],
            decision_code=ver_res["decision"],
            execution_time_ms=ver_res["execution_time_ms"]
        )
        db.add(app_record)
        db.commit()
    except Exception as e:
        print(f"[DB] Error saving application record: {e}")

    return {
        "success": True,
        "message": f"Application successfully filed! Pending title lock active for {req.ttl_seconds or 600} seconds.",
        "lock_info": lock_data,
        "application_no": app_no
    }


@app.get("/api/locks", response_model=List[Dict[str, Any]])
def list_active_locks():
    """List all active pending application locks."""
    return lock_manager.list_active_locks()


@app.post("/api/locks/release")
def release_lock(title: str = Query(...), applicant_id: str = Query(...)):
    """Release an active pending title lock."""
    released = lock_manager.release_lock(title=title, applicant_id=applicant_id)
    return {"success": released, "title": title}


@app.get("/api/titles/search")
def search_registered_titles(query: str = Query("", min_length=0), limit: int = Query(25, ge=1, le=100)):
    """Instant search across registered titles database."""
    results = titles_index.search_titles(query=query, limit=limit)
    return {
        "query": query,
        "total_results": len(results),
        "titles": results
    }


@app.get("/api/guidelines")
def get_guidelines():
    """Return PRGI guidelines catalog and disallowed words."""
    from backend.pipeline.stage2_guidelines import (
        DISALLOWED_ENFORCEMENT_WORDS,
        NATIONAL_EMBLEMS_AND_PROTECTED_NAMES,
        OBSCENE_OR_DEFAMATORY_TERMS,
    )
    from backend.pipeline.stage1_preprocessor import GENERIC_MODIFIERS
    
    return {
        "guidelines": [
            {
                "guideline_ref": "PRGI General Rule",
                "title": "Non-Text Characters, Symbols & Emojis Prohibition",
                "description": "Titles containing non-text characters, signs, symbols including mathematical symbols ('+', '*', etc.), pictographs, hallmarks, logos, monograms, phonograms, emojis, etc. are strictly prohibited.",
                "examples": ["News+", "Daily*Express", "Star #1", "News 📰", "Daily@Morning"]
            },
            {
                "guideline_ref": "PRGI General Rule",
                "title": "Numeric-Only Title Prohibition",
                "description": "Titles consisting solely of numbers or digits without substantive alphabetical/text characters are not permitted.",
                "examples": ["12345", "2024", "24 7", "99 100"]
            },
            {
                "guideline_ref": "Guideline 12",
                "title": "Disallowed Law Enforcement & State Organ Words",
                "description": "Prohibits words implying official authority, police, military, courts, or vigilance bodies.",
                "examples": ["Police", "Crime", "CBI", "CID", "Army", "Vigilance", "Sarkar", "Court"]
            },
            {
                "guideline_ref": "Guideline 4",
                "title": "National Emblems & Protected Names Act 1950",
                "description": "Prohibits national symbols, civilian honors, constitutional offices, and UN organizations.",
                "examples": ["Ashoka Chakra", "National Emblem", "Bharat Ratna", "President", "United Nations"]
            },
            {
                "guideline_ref": "Guideline 8",
                "title": "Distinctive Anchor Words Requirement",
                "description": "Rejects titles consisting entirely of generic periodicities and modifiers with no distinctive anchor.",
                "examples": ["The Daily News", "Weekly Express", "Dainik Samachar"]
            },
            {
                "guideline_ref": "Guideline 6",
                "title": "Combination Titles ('Frankentitle' Rule)",
                "description": "Rejects titles that concatenate two or more already registered titles.",
                "examples": ["Hindu Indian Express", "Dainik Jagran Kesari"]
            },
            {
                "guideline_ref": "Guideline 5",
                "title": "Phonetic & Orthographic Similarity",
                "description": "Bars titles with deceptive auditory or visual similarity to existing registered titles.",
                "examples": ["Namascar India vs Namaskar India", "Daineq vs Dainik"]
            },
            {
                "guideline_ref": "Guideline 11",
                "title": "Cross-Lingual Semantic Equivalence",
                "description": "Restricts direct translated copies of registered titles across Indian languages.",
                "examples": ["Daily Evening (English) vs Pratidin Sandhya (Hindi/Bengali)"]
            }
        ],
        "disallowed_words_count": len(DISALLOWED_ENFORCEMENT_WORDS) + len(NATIONAL_EMBLEMS_AND_PROTECTED_NAMES),
        "generic_words_count": len(GENERIC_MODIFIERS)
    }


# -------------------------------------------------------------
# Static Files & Web UI Serving
# -------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PRGI Title Verification Engine API is running. Visit /docs for Swagger UI."}
