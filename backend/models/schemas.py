"""
Pydantic Schemas for Request/Response Models
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TitleVerificationRequest(BaseModel):
    title: str = Field(..., description="Title to verify", min_length=1, max_length=300)
    language: Optional[str] = Field("English", description="Target language of publication")
    state: Optional[str] = Field("National", description="Target state/territory of publication")
    periodicity: Optional[str] = Field("Daily", description="Periodicity (Daily, Weekly, Monthly, etc.)")
    applicant_id: Optional[str] = Field("USER_WEB_001", description="ID of applicant checking title")


class MatchItem(BaseModel):
    title: str
    registration_no: str
    language: str
    state: str
    periodicity: str
    orthographic_similarity: float
    phonetic_similarity: float
    semantic_similarity: float
    highest_similarity: float
    semantic_pairs: Optional[List[str]] = []


class ReasonItem(BaseModel):
    stage: str
    rule: str
    guideline_ref: str
    explanation: str


class TitleVerificationResponse(BaseModel):
    raw_title: str
    cleaned_title: Optional[str] = ""
    anchor_words: Optional[str] = ""
    verification_probability: float
    status: str  # Approved, Rejected, Review Needed
    decision: str
    highest_similarity_score: Optional[float] = 0.0
    max_scores: Optional[Dict[str, float]] = None
    execution_time_ms: float
    reasons: List[ReasonItem]
    top_matches: Optional[List[MatchItem]] = []
    stage_results: Optional[Dict[str, Any]] = None
    suggestions: List[str]
    ai_suggestions: Optional[List[Dict[str, Any]]] = []


class BatchVerificationRequest(BaseModel):
    titles: List[str] = Field(..., min_length=1, max_length=500)
    language: Optional[str] = "English"
    state: Optional[str] = "National"
    periodicity: Optional[str] = "Daily"


class BatchVerificationResponse(BaseModel):
    total_processed: int
    approved_count: int
    rejected_count: int
    review_needed_count: int
    execution_time_ms: float
    results: List[TitleVerificationResponse]


class LockApplicationRequest(BaseModel):
    title: str = Field(..., min_length=1)
    applicant_id: str = Field(..., min_length=1)
    applicant_name: Optional[str] = "Anonymous"
    applicant_email: Optional[str] = ""
    language: Optional[str] = "English"
    state: Optional[str] = "National"
    periodicity: Optional[str] = "Daily"
    ttl_seconds: Optional[int] = 600


class LockApplicationResponse(BaseModel):
    success: bool
    message: str
    lock_info: Optional[Dict[str, Any]] = None
    application_no: Optional[str] = None


class ActiveLockItem(BaseModel):
    title: str
    cleaned_title: str
    applicant_id: str
    applicant_name: str
    created_at: float
    expires_at: float
    ttl_seconds: int
    ttl_remaining: int


class GuidelineItem(BaseModel):
    guideline_ref: str
    category: str
    title: str
    description: str
    act_reference: str
    severity: str


class SystemHealthResponse(BaseModel):
    status: str
    database_connected: bool
    total_registered_titles: int
    active_locks_count: int
    models_loaded: Dict[str, bool]
    version: str
