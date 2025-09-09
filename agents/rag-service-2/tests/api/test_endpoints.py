import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

# The FastAPI app instance
from app.main import app
from app.core.dependencies import get_rag_service, get_db, get_llm_client, get_retriever
from app.models.rag import RAGResult

# Create a TestClient instance
client = TestClient(app)

@pytest.fixture
def mock_rag_service():
    """Mocks the RAGService for dependency override."""
    service = MagicMock()
    service.ask.return_value = RAGResult(
        text="This is a mocked answer.",
        sources=["mock_source.pdf"]
    )
    return service

def test_ask_question_success(mock_rag_service):
    """Tests the /v1/ask endpoint for a successful response."""
    # Override the dependency with our mock for this test
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    
    # Act
    response = client.post("/v1/ask", json={"text": "What is the policy?"})
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "This is a mocked answer."
    assert data["sources"] == ["mock_source.pdf"]
    mock_rag_service.ask.assert_called_once_with("What is the policy?")
    
    # Clean up the override to not affect other tests
    app.dependency_overrides.clear()

def test_ask_question_internal_error(mock_rag_service):
    """Tests the /v1/ask endpoint when the service raises an exception."""
    # Configure the mock to raise an error
    mock_rag_service.ask.side_effect = Exception("Something went wrong")
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    
    # Act
    response = client.post("/v1/ask", json={"text": "A problematic question"})
    
    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "An internal error occurred while processing your request."}
    
    # Clean up the override
    app.dependency_overrides.clear()

@patch("app.api.v1.endpoints.KafkaClient")
def test_health_check_success(mock_kafka_client_class):
    """Tests the /v1/health endpoint for a successful response."""
    # Mock the KafkaClient to prevent real network calls
    mock_kafka_instance = MagicMock() # The instance itself can be a regular mock
    mock_kafka_instance.start = AsyncMock() # The async methods must be AsyncMocks
    mock_kafka_instance.stop = AsyncMock()
    mock_kafka_client_class.return_value = mock_kafka_instance

    # Mock the dependencies that FastAPI injects
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_llm_client] = lambda: MagicMock()
    app.dependency_overrides[get_retriever] = lambda: MagicMock()

    # Act
    response = client.get("/v1/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["kafka_status"] == "ok"

    # Clean up overrides
    app.dependency_overrides.clear()