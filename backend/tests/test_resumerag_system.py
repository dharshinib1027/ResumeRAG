"""Integration tests for ResumeRAG AI-Powered Resume Intelligence System."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "llm_available" in data


def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_resumes" in data
    assert "total_vector_chunks" in data


def test_search_empty():
    response = client.post("/api/search", json={"query": "Machine Learning"})
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data


def test_candidate_not_found():
    response = client.get("/api/candidate/nonexistent_id")
    assert response.status_code == 404
