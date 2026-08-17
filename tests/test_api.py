"""
API Endpoint Integration Tests
"""

import sys
from pathlib import Path

# Add project root to python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["total_registered_titles"] > 0


def test_api_verify_prohibited_symbols():
    res = client.post("/api/verify", json={"title": "News+"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] == 0.0
    assert data["status"] == "Rejected"
    assert data["decision"] == "REJECTED_PROHIBITED_SYMBOLS"
    assert any("Prohibited Non-Text Characters" in r["rule"] for r in data["reasons"])


def test_api_verify_numeric_only():
    res = client.post("/api/verify", json={"title": "2024"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] == 0.0
    assert data["status"] == "Rejected"
    assert data["decision"] == "REJECTED_PURE_NUMERIC"
    assert any("Numeric-Only" in r["rule"] for r in data["reasons"])


def test_api_verify_disallowed():
    res = client.post("/api/verify", json={"title": "The Crime Investigation Daily"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] == 0.0
    assert data["status"] == "Rejected"
    assert data["decision"] == "REJECTED_STAGE_2"


def test_api_verify_generic():
    res = client.post("/api/verify", json={"title": "The Daily News"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] == 0.0
    assert data["status"] == "Rejected"
    assert data["decision"] == "REJECTED_STAGE_1"


def test_api_verify_already_registered():
    res = client.post("/api/verify", json={"title": "Morning Post"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] == 0.0
    assert data["status"] == "Rejected"
    assert data["decision"] == "REJECTED_ALREADY_REGISTERED"
    assert any("Already Registered Title" in r["rule"] for r in data["reasons"])
    assert len(data["top_matches"]) > 0
    assert data["top_matches"][0]["title"] == "MORNING POST"


def test_api_verify_approved():
    res = client.post("/api/verify", json={"title": "Zylophonic Quantum Astroflora"})
    assert res.status_code == 200
    data = res.json()
    assert data["verification_probability"] >= 60.0
    assert data["status"] == "Approved"


def test_api_batch_verify():
    res = client.post("/api/batch-verify", json={
        "titles": [
            "News+",
            "2024",
            "The Crime Investigation Daily",
            "The Daily News",
            "Zylophonic Quantum Astroflora"
        ]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_processed"] == 5
    assert data["rejected_count"] == 4
    assert data["approved_count"] == 1


def test_api_apply_and_lock():
    unique_title = "Zylophonic Quantum Astroflora"
    # Apply
    res1 = client.post("/api/apply", json={
        "title": unique_title,
        "applicant_id": "TEST_USER_1",
        "applicant_name": "Test User",
        "ttl_seconds": 30
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["success"] is True

    # Check lock collision on second user verification
    res2 = client.post("/api/verify", json={
        "title": unique_title,
        "applicant_id": "TEST_USER_2"
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "Rejected"
    assert d2["decision"] == "REJECTED_PENDING_COLLISION"

    # Release lock
    client.post(f"/api/locks/release?title={unique_title}&applicant_id=TEST_USER_1")


def test_api_titles_search_btree():
    res = client.get("/api/titles/search?query=Times&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "Times"
    assert "titles" in data
    assert len(data["titles"]) > 0
    first = data["titles"][0]
    assert "title" in first
    assert "registration_no" in first
    assert "language" in first

