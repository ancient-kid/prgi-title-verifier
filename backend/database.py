"""
Relational Database Models and Session Management (SQLAlchemy / SQLite / PostgreSQL)
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import DATABASE_URL

# Handle SQLite vs Postgres thread safety
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class RegisteredTitleModel(Base):
    __tablename__ = "registered_titles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    cleaned_title = Column(String(500), nullable=False, index=True)
    anchor_words = Column(String(255), index=True)
    registration_no = Column(String(100), unique=True, index=True)
    language = Column(String(100), default="English")
    state = Column(String(100), default="National")
    periodicity = Column(String(100), default="Daily")
    publisher = Column(String(255), nullable=True)
    phonetic_metaphone = Column(String(255), nullable=True)
    indic_soundex = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TitleApplicationModel(Base):
    __tablename__ = "title_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_no = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    applicant_id = Column(String(100), nullable=False, index=True)
    applicant_name = Column(String(255), nullable=True)
    applicant_email = Column(String(255), nullable=True)
    language = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    periodicity = Column(String(100), nullable=True)
    verification_probability = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, index=True)  # Approved, Rejected, Review Needed, Pending
    decision_code = Column(String(100), nullable=True)
    diagnostics_json = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class PRGIGuidelineModel(Base):
    __tablename__ = "prgi_guidelines"

    id = Column(Integer, primary_key=True, index=True)
    guideline_ref = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    act_reference = Column(String(255), default="Press and Registration of Periodicals Act, 2023")
    severity = Column(String(50), default="HARD_REJECT")


def init_db():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
