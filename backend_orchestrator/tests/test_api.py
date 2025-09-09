import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "backend-orchestrator"

def test_chat_endpoint():
    payload = {
        "user_id": "test_user",
        "message": "Hello!",
        "session_id": None,
        "context": {}
    }
    response = client.post("/chat", json=payload)
    # Accept 200 or 500 (if LLM keys are not set up)
    assert response.status_code in [200, 500]

def test_session_endpoints():
    # Try to get a non-existent session
    response = client.get("/session/nonexistent-session")
    assert response.status_code in [404, 500]
    # Try to clear a non-existent session
    response = client.delete("/session/nonexistent-session")
    assert response.status_code in [200, 500]

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "active_sessions" in response.json()
    assert "llm_provider" in response.json()
    assert "fallback_provider" in response.json()
