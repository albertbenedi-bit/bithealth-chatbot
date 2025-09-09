import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.session.session_manager import SessionManager

class TestSessionManager:
    
    @pytest.fixture
    async def session_manager(self):
        """Create a session manager with mocked Redis"""
        manager = SessionManager(redis_url="redis://localhost:6379", session_ttl=3600)
        
        mock_redis = AsyncMock()
        manager.redis_client = mock_redis
        
        return manager, mock_redis
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test session creation"""
        manager, mock_redis = session_manager
        
        session_id = await manager.create_session("user123", {"preference": "english"})
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID length
        
        mock_redis.setex.assert_called_once()
        mock_redis.sadd.assert_called_once()
        mock_redis.expire.assert_called_once()
        
        call_args = mock_redis.setex.call_args[0]
        session_key = call_args[0]
        ttl = call_args[1]
        session_data_json = call_args[2]
        
        assert session_key == f"session:{session_id}"
        assert ttl == 3600
        
        session_data = json.loads(session_data_json)
        assert session_data["session_id"] == session_id
        assert session_data["user_id"] == "user123"
        assert session_data["context"]["preference"] == "english"
        assert session_data["conversation_history"] == []
        assert session_data["workflow_state"] == "initial"
    
    @pytest.mark.asyncio
    async def test_get_session_exists(self, session_manager):
        """Test retrieving existing session"""
        manager, mock_redis = session_manager
        
        session_data = {
            "session_id": "test-session-id",
            "user_id": "user123",
            "conversation_history": [{"role": "user", "content": "Hello"}]
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        
        result = await manager.get_session("test-session-id")
        
        assert result == session_data
        mock_redis.get.assert_called_once_with("session:test-session-id")
    
    @pytest.mark.asyncio
    async def test_get_session_not_exists(self, session_manager):
        """Test retrieving non-existent session"""
        manager, mock_redis = session_manager
        
        mock_redis.get.return_value = None
        
        result = await manager.get_session("non-existent-session")
        
        assert result is None
        mock_redis.get.assert_called_once_with("session:non-existent-session")
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_manager):
        """Test session update"""
        manager, mock_redis = session_manager
        
        existing_session = {
            "session_id": "test-session",
            "user_id": "user123",
            "context": {"lang": "en"},
            "conversation_history": []
        }
        
        mock_redis.get.return_value = json.dumps(existing_session)
        
        updates = {"current_intent": "appointment_booking", "context": {"lang": "id"}}
        await manager.update_session("test-session", updates)
        
        mock_redis.get.assert_called_once_with("session:test-session")
        mock_redis.setex.assert_called_once()
        
        call_args = mock_redis.setex.call_args[0]
        updated_data = json.loads(call_args[2])
        
        assert updated_data["current_intent"] == "appointment_booking"
        assert updated_data["context"]["lang"] == "id"
        assert "last_activity" in updated_data
    
    @pytest.mark.asyncio
    async def test_add_message_to_history(self, session_manager):
        """Test adding message to conversation history"""
        manager, mock_redis = session_manager
        
        existing_session = {
            "session_id": "test-session",
            "user_id": "user123",
            "conversation_history": [
                {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_redis.get.return_value = json.dumps(existing_session)
        
        await manager.add_message_to_history(
            "test-session", 
            "assistant", 
            "Hi there! How can I help you?",
            {"intent": "greeting"}
        )
        
        mock_redis.setex.assert_called_once()
        
        call_args = mock_redis.setex.call_args[0]
        updated_data = json.loads(call_args[2])
        
        assert len(updated_data["conversation_history"]) == 2
        new_message = updated_data["conversation_history"][1]
        assert new_message["role"] == "assistant"
        assert new_message["content"] == "Hi there! How can I help you?"
        assert new_message["metadata"]["intent"] == "greeting"
        assert "timestamp" in new_message
    
    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, session_manager):
        """Test conversation history is limited to 50 messages"""
        manager, mock_redis = session_manager
        
        conversation_history = [
            {"role": "user", "content": f"Message {i}", "timestamp": "2024-01-01T00:00:00"}
            for i in range(50)
        ]
        
        existing_session = {
            "session_id": "test-session",
            "user_id": "user123",
            "conversation_history": conversation_history
        }
        
        mock_redis.get.return_value = json.dumps(existing_session)
        
        await manager.add_message_to_history("test-session", "assistant", "New message")
        
        call_args = mock_redis.setex.call_args[0]
        updated_data = json.loads(call_args[2])
        
        assert len(updated_data["conversation_history"]) == 50
        assert updated_data["conversation_history"][-1]["content"] == "New message"
        assert updated_data["conversation_history"][0]["content"] == "Message 1"  # Message 0 removed
    
    @pytest.mark.asyncio
    async def test_clear_session(self, session_manager):
        """Test session clearing"""
        manager, mock_redis = session_manager
        
        session_data = {
            "session_id": "test-session",
            "user_id": "user123"
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        
        await manager.clear_session("test-session")
        
        mock_redis.get.assert_called_once_with("session:test-session")
        mock_redis.srem.assert_called_once_with("user_sessions:user123", "test-session")
        mock_redis.delete.assert_called_once_with("session:test-session")
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_manager):
        """Test getting user sessions"""
        manager, mock_redis = session_manager
        
        mock_redis.smembers.return_value = [b"session1", b"session2", b"session3"]
        
        sessions = await manager.get_user_sessions("user123")
        
        assert sessions == ["session1", "session2", "session3"]
        mock_redis.smembers.assert_called_once_with("user_sessions:user123")
    
    @pytest.mark.asyncio
    async def test_get_active_session_count(self, session_manager):
        """Test getting active session count"""
        manager, mock_redis = session_manager
        
        mock_redis.keys.return_value = ["session:1", "session:2", "session:3"]
        
        count = await manager.get_active_session_count()
        
        assert count == 3
        mock_redis.keys.assert_called_once_with("session:*")
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, session_manager):
        """Test getting conversation history"""
        manager, mock_redis = session_manager
        
        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        session_data = {
            "session_id": "test-session",
            "conversation_history": conversation_history
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        
        history = await manager.get_conversation_history("test-session")
        assert len(history) == 3
        assert history == conversation_history
        
        history_limited = await manager.get_conversation_history("test-session", limit=2)
        assert len(history_limited) == 2
        assert history_limited == conversation_history[-2:]
