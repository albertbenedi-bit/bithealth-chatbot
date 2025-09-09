import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from backend_orchestrator.src.main import app

class TestMainAPI:
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_app_state(self):
        """Mock app state with all dependencies"""
        mock_state = Mock()
        mock_state.llm_provider = AsyncMock()
        mock_state.fallback_llm_provider = AsyncMock()
        mock_state.prompt_manager = Mock()
        mock_state.kafka_client = AsyncMock()
        mock_state.session_manager = AsyncMock()
        mock_state.conversation_engine = AsyncMock()
        mock_state.settings = Mock()
        
        return mock_state
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "backend-orchestrator"
    
    def test_chat_endpoint_success(self, client, mock_app_state):
        """Test successful chat request"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.conversation_engine.process_message.return_value = {
                "response": "Hello! How can I help you today?",
                "session_id": "test-session-123",
                "intent": "greeting",
                "requires_human_handoff": False,
                "suggested_actions": []
            }
            
            chat_request = {
                "user_id": "user123",
                "message": "Hello",
                "session_id": "test-session-123",
                "context": {"language": "en"}
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["response"] == "Hello! How can I help you today?"
            assert data["session_id"] == "test-session-123"
            assert data["intent"] == "greeting"
            assert data["requires_human_handoff"] is False
            assert data["suggested_actions"] == []
            
            mock_app_state.conversation_engine.process_message.assert_called_once_with(
                user_id="user123",
                message="Hello",
                session_id="test-session-123",
                context={"language": "en"}
            )
    
    def test_chat_endpoint_without_session_id(self, client, mock_app_state):
        """Test chat request without session ID"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.conversation_engine.process_message.return_value = {
                "response": "I've created a new session for you.",
                "session_id": "new-session-456",
                "intent": "general_info",
                "requires_human_handoff": False,
                "suggested_actions": []
            }
            
            chat_request = {
                "user_id": "user456",
                "message": "I need help"
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["session_id"] == "new-session-456"
            
            mock_app_state.conversation_engine.process_message.assert_called_once_with(
                user_id="user456",
                message="I need help",
                session_id=None,
                context={}
            )
    
    def test_chat_endpoint_error_handling(self, client, mock_app_state):
        """Test chat endpoint error handling"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.conversation_engine.process_message.side_effect = Exception("Processing error")
            
            chat_request = {
                "user_id": "user789",
                "message": "Test message"
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 500
            
            data = response.json()
            assert data["detail"] == "Internal server error"
    
    def test_chat_endpoint_validation_error(self, client):
        """Test chat endpoint with invalid request data"""
        invalid_request = {
            "message": "Hello"
        }
        
        response = client.post("/chat", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_get_session_success(self, client, mock_app_state):
        """Test successful session retrieval"""
        with patch.object(app, 'state', mock_app_state):
            mock_session_data = {
                "session_id": "test-session-123",
                "user_id": "user123",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ],
                "context": {"language": "en"}
            }
            
            mock_app_state.session_manager.get_session.return_value = mock_session_data
            
            response = client.get("/session/test-session-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data == mock_session_data
            
            mock_app_state.session_manager.get_session.assert_called_once_with("test-session-123")
    
    def test_get_session_not_found(self, client, mock_app_state):
        """Test session retrieval when session doesn't exist"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.session_manager.get_session.return_value = None
            
            response = client.get("/session/nonexistent-session")
            assert response.status_code == 404
            
            data = response.json()
            assert data["detail"] == "Session not found"
    
    def test_get_session_error(self, client, mock_app_state):
        """Test session retrieval error handling"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.session_manager.get_session.side_effect = Exception("Database error")
            
            response = client.get("/session/test-session")
            assert response.status_code == 500
            
            data = response.json()
            assert data["detail"] == "Internal server error"
    
    def test_clear_session_success(self, client, mock_app_state):
        """Test successful session clearing"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.session_manager.clear_session.return_value = None
            
            response = client.delete("/session/test-session-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Session cleared successfully"
            
            mock_app_state.session_manager.clear_session.assert_called_once_with("test-session-123")
    
    def test_clear_session_error(self, client, mock_app_state):
        """Test session clearing error handling"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.session_manager.clear_session.side_effect = Exception("Clear error")
            
            response = client.delete("/session/test-session")
            assert response.status_code == 500
            
            data = response.json()
            assert data["detail"] == "Internal server error"
    
    def test_metrics_endpoint(self, client, mock_app_state):
        """Test metrics endpoint"""
        with patch.object(app, 'state', mock_app_state):
            mock_app_state.session_manager.get_active_session_count.return_value = 42
            
            response = client.get("/metrics")
            assert response.status_code == 200
            
            data = response.json()
            assert data["active_sessions"] == 42
            assert data["llm_provider"] == "gemini"
            assert data["fallback_provider"] == "anthropic"
            
            mock_app_state.session_manager.get_active_session_count.assert_called_once()
    
    def test_chat_request_model_validation(self, client):
        """Test ChatRequest model validation"""
        full_request = {
            "user_id": "user123",
            "message": "Hello world",
            "session_id": "session-456",
            "context": {"key": "value"}
        }
        
        with patch.object(app, 'state') as mock_state:
            mock_state.conversation_engine.process_message.return_value = {
                "response": "Test response",
                "session_id": "session-456",
                "intent": "test",
                "requires_human_handoff": False,
                "suggested_actions": []
            }
            
            response = client.post("/chat", json=full_request)
            assert response.status_code == 200
    
    def test_chat_response_model_structure(self, client, mock_app_state):
        """Test ChatResponse model structure"""
        with patch.object(app, 'state', mock_app_state):
            mock_response = {
                "response": "Test response",
                "session_id": "test-session",
                "intent": "test_intent",
                "requires_human_handoff": True,
                "suggested_actions": ["action1", "action2"]
            }
            
            mock_app_state.conversation_engine.process_message.return_value = mock_response
            
            chat_request = {
                "user_id": "user123",
                "message": "Test message"
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            
            assert "response" in data
            assert "session_id" in data
            assert "intent" in data
            assert "requires_human_handoff" in data
            assert "suggested_actions" in data
            
            assert isinstance(data["response"], str)
            assert isinstance(data["session_id"], str)
            assert isinstance(data["requires_human_handoff"], bool)
            assert isinstance(data["suggested_actions"], list)
