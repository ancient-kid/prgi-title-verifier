"""
PRGI Title Verification REST API Server
Updated: 2026-08-17 (Suggester Matrix Active)
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
def release_lock(title: str = Query(...), applicant_id: Optional[str] = Query(None)):
    """Release an active pending title lock."""
    if not applicant_id:
        is_locked, lock_info = lock_manager.check_lock(title)
        if is_locked and lock_info:
            applicant_id = lock_info.get("applicant_id")
    released = lock_manager.release_lock(title=title, applicant_id=applicant_id or "")
    return {"success": released, "title": title}


@app.get("/api/titles/search")
def search_registered_titles(
    query: str = Query("", min_length=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Instant search across registered titles database using PostgreSQL B-tree index."""
    results = titles_index.search_titles(query=query, limit=limit, db=db)
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
                "guideline_ref": "Guideline 1",
                "category": "Distinctiveness & Root Words",
                "title": "Generic or Root Word Titles Prohibited",
                "description": "The proposed titles should preferably contain more than one word formed by combining distinct and meaningful terms. Generic, or root word titles shall not be registered. Generic or Root words are those words which cannot be broken down further.",
                "examples": ["Manthan", "Darpan", "Inspire", "Success", "Khulasa", "Rahasya", "Katha", "Herald", "Malar", "Mukhi", "Nukkad"]
            },
            {
                "guideline_ref": "Guideline 2",
                "category": "Phonetic & Visual Uniqueness",
                "title": "Phonetic and Visual Deceptive Similarity",
                "description": "The proposed titles must be unique and shall not be phonetically or visually similar to any existing registered title whether in the same language across India or any other language within the same State.",
                "examples": ["Namascar vs Namaskar", "Daineq vs Dainik", "Same state cross-language resemblance"]
            },
            {
                "guideline_ref": "Guideline 3",
                "category": "Public Decency & Morality",
                "title": "Negative Connotations, Obscene & Crime Terms",
                "description": "Titles should be meaningful and clear. Titles with negative connotations with religious sentiments, obscene, absurd or offensive to public sentiments or those that could be misused with words like 'crime', 'corruption' etc. will not be registered.",
                "examples": ["Crime", "Corruption", "Scam", "Extortion", "Vulgar / Obscene words", "Offensive religious terms"]
            },
            {
                "guideline_ref": "Guideline 4",
                "category": "Acronyms & Numerals",
                "title": "Abbreviations, Acronyms and Numerals Requirement",
                "description": "Abbreviations, acronyms or numerals will be considered only if they are meaningfully and appropriately attached with other words. Standalone or arbitrary abbreviations/numbers are not permitted.",
                "examples": ["999", "XYZ", "24x7 standalone", "Meaningful combination required (e.g. 'Mission 2047 Express')"]
            },
            {
                "guideline_ref": "Guideline 5",
                "category": "Combination Titles",
                "title": "Combination or Rearrangement of Registered Titles",
                "description": "Titles that combine existing registered titles whether in full, in part or by rearranging words or inserting non-distinctive terms that do not create a significantly different title will not be registered.",
                "examples": ["Hindu Indian Express", "Dainik Jagran Kesari", "Times of India Herald"]
            },
            {
                "guideline_ref": "Guideline 6",
                "category": "Personal Names",
                "title": "Individual Names of Owner or Publisher Prohibited",
                "description": "Titles denoting the name of an individual should not be the names of the owner or publisher of the proposed periodical to avoid misleading personal attribution.",
                "examples": ["Rajan Times (if owner is Rajan)", "Deepak Samachar (if owner is Deepak)", "Jitendra News"]
            },
            {
                "guideline_ref": "Guideline 7",
                "category": "Special Characters",
                "title": "Signs, Symbols, Emojis and Non-Text Characters",
                "description": "Titles containing non-text characters, or any form of signs, symbols including mathematical symbols (like '+', '*', etc.), pictographs, photographs, hallmarks, logos, monograms, phonograms, emojis, etc. will not be registered.",
                "examples": ["News+Times", "Bharat*Post", "24/7 Daily", "Emojis & pictographs", "Logos / Monograms"]
            },
            {
                "guideline_ref": "Guideline 8",
                "category": "Generic Modifiers",
                "title": "Insignificant Prefixes, Suffixes & Generic Modifiers",
                "description": "Titles formed by insignificantly prefixing or suffixing generic or repetitive terms to an existing title—such as addition names of cities or states, periodicity or language, or addition of articles (A, An, The) prepositions or adjectives to an already existing title—will not be approved.",
                "examples": ["The Times", "Daily Dainik News", "Saptahik Weekly", "Sandhya Evening", "Mumbai Express (if Express registered)"]
            },
            {
                "guideline_ref": "Guideline 9",
                "category": "Legal & Judicial",
                "title": "Judicial Pronouncements, Copyright, Trademark & Defamation",
                "description": "The proposed title shall not be registered if it is found to be in violation of any judicial pronouncement including matters involving copyright, trademark infringement, contempt of court and defamation.",
                "examples": ["Trademarked Brand Clones", "Judicially Restrained Names", "Contemptuous Titles", "Defamatory Labels"]
            },
            {
                "guideline_ref": "Guideline 10",
                "category": "National Security",
                "title": "Sovereignty, Integrity of India & Public Order",
                "description": "Titles containing words which can be construed as affecting the sovereignty and integrity of India, Security of the State, International Relations, Public order, Morality and public decency, incite unrest or disorder etc. will not be registered.",
                "examples": ["Secessionist Terms", "Insurrection / Riot Incitement", "Hostile International Terms", "Public Disorder"]
            },
            {
                "guideline_ref": "Guideline 11",
                "category": "Emblems Act Compliance",
                "title": "National Symbols, Emblems & Emblems Act 1950",
                "description": "Titles similar to any national symbol, national motto, or suggesting misleading association with Central Government/State Governments/Local bodies/Constitutional bodies/Statutory bodies or are violative of 'The Emblems and Names (Prevention of Improper Use) Act, 1950' or any other law in force will not be registered.",
                "examples": ["Ashoka Chakra", "National Emblem", "Bharat Ratna", "President", "Satyameva Jayate", "United Nations"]
            },
            {
                "guideline_ref": "Guideline 12",
                "category": "Official Authority Blacklist",
                "title": "Government Organs, Regulatory Agencies & Public Schemes",
                "description": "Titles containing names of Government Organizations/ Departments, Regulatory/Enforcement Agencies (such as 'Police', 'Bureau', 'Investigation Department', 'Vigilance', 'CID', 'CBI', Commission, Defence Establishment, etc.), Foreign Governments, International Organizations (e.g., UN, WHO, ILO) in any language, or words like Sarkar, Government, Parliament etc. or title containing the names of public welfare schemes of Central/State Governments or its organizations or local bodies which suggest a misleading association with them shall not be registered.",
                "examples": ["Police", "Crime Bureau", "CID", "CBI", "Army", "Vigilance", "Sarkar", "Government", "Parliament", "Public Schemes"]
            },
            {
                "guideline_ref": "Guideline 13",
                "category": "Foreign Association",
                "title": "Misleading Foreign Country or City Association",
                "description": "Titles suggesting any association with a foreign country, city, or place which does not correspond to the State or place of publication of the periodical shall not be registered.",
                "examples": ["South Africa Times", "Canada Times", "New York Mirror", "London Chronicle (published in India)"]
            },
            {
                "guideline_ref": "Guideline 14",
                "category": "National Dignitaries",
                "title": "Names of Prominent National Leaders & Heads of Government",
                "description": "Titles with the names of national leaders or those resembling the names of prominent national leaders, Heads of Government, and functionaries of Central and State governments will not be registered. However, names of recognized national and state political parties will be considered if applied by the concerned organization.",
                "examples": ["Mahatma Gandhi Times", "Prime Minister Gazette", "Chief Minister Post", "Governor Herald"]
            },
            {
                "guideline_ref": "Guideline 15",
                "category": "Broadcast Media",
                "title": "Satellite TV Channels, FM Radio & Broadcast Names (MIB)",
                "description": "Title registered as a Satellite TV Channel/FM Radio/Community Radio Station with the Ministry of Information and Broadcasting shall not be registered unless the application is made by their owner or by their representative on his behalf.",
                "examples": ["News Nation", "News Time", "Aajtak News", "Akaashvani Times", "Dabang News"]
            },
            {
                "guideline_ref": "Guideline 16",
                "category": "Well-Known Periodicals",
                "title": "Protection of Well-Known Periodicals",
                "description": "Titles resembling the titles of well-known periodicals if applied by anyone other than the existing owner of the well-known title shall not be registered. This is to avoid any false/misleading impression of association with the well-known periodical.",
                "examples": ["India Today Lookalikes", "Time Magazine Clones", "Reader's Digest Imitations", "Famous Journal Clones"]
            },
            {
                "guideline_ref": "Guideline 17",
                "category": "Commercial & Non-Periodical",
                "title": "Advertisements, Classifieds, Tenders & Directories",
                "description": "Titles using words like Ad or Advertisement, Classifieds, Tender, Calendar, Panchang, Matrimonial, Yellow pages (generally prefixed with white, pink, etc.), pamphlet, brochure, directory, or any such publication which cannot be treated as a periodical shall not be registered.",
                "examples": ["Ad Express", "Classifieds Weekly", "Tender Gazette", "Panchang Patrika", "Yellow Pages Directory", "Matrimonial News"]
            },
            {
                "guideline_ref": "Guideline 18",
                "category": "Ownership & Editions",
                "title": "Transfer of Ownership & New Edition Restrictions",
                "description": "Registration of new editions and transfer of ownership of an existing periodical with a title falling in the categories specified under points 3 and 9 to 13 of these guidelines will not be considered.",
                "examples": ["Edition expansion blocked for restricted words", "Transfer barred for non-compliant legacy titles", "Strict adherence to Guidelines 3 & 9–13"]
            },
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
        ],
        "total_guidelines_count": 18,
        "effective_date": "01.07.2025",
        "act_reference": "Section 5(3)(C) read with Section 2(g) of the Press and Registration of Periodicals Act 2023",
        "disallowed_words_count": len(DISALLOWED_ENFORCEMENT_WORDS) + len(NATIONAL_EMBLEMS_AND_PROTECTED_NAMES),
        "generic_words_count": len(GENERIC_MODIFIERS)
    }


# -------------------------------------------------------------
# Static Files & Web UI Serving
# -------------------------------------------------------------
FRONTEND_NEXT_OUT = BASE_DIR / "frontend-next" / "out"

if FRONTEND_NEXT_OUT.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_NEXT_OUT)), name="static")
elif FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_next = FRONTEND_NEXT_OUT / "index.html"
    if index_next.exists():
        return FileResponse(str(index_next))
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PRGI Title Verification Engine API is running. Visit /docs for Swagger UI."}
