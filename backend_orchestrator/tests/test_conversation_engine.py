import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.workflow.conversation_engine import ConversationEngine
from src.llm_abstraction.provider_interface import LLMRequest, LLMResponse

class TestConversationEngine:
    
    @pytest.fixture
    def conversation_engine(self):
        """Create conversation engine with mocked dependencies"""
        mock_llm_provider = AsyncMock()
        mock_fallback_provider = AsyncMock()
        mock_prompt_manager = Mock()
        mock_kafka_client = AsyncMock()
        mock_session_manager = AsyncMock()
        
        engine = ConversationEngine(
            llm_provider=mock_llm_provider,
            fallback_provider=mock_fallback_provider,
            prompt_manager=mock_prompt_manager,
            kafka_client=mock_kafka_client,
            session_manager=mock_session_manager
        )
        
        return engine, {
            "llm_provider": mock_llm_provider,
            "fallback_provider": mock_fallback_provider,
            "prompt_manager": mock_prompt_manager,
            "kafka_client": mock_kafka_client,
            "session_manager": mock_session_manager
        }
    
    @pytest.mark.asyncio
    async def test_process_message_new_session(self, conversation_engine):
        """Test processing message with new session creation"""
        engine, mocks = conversation_engine
        
        mocks["session_manager"].create_session.return_value = "new-session-id"
        mocks["session_manager"].get_session.return_value = {
            "session_id": "new-session-id",
            "user_id": "user123",
            "conversation_history": [],
            "context": {},
            "current_intent": None
        }
        
        mock_llm_response = LLMResponse(
            content="general_info",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            model="gemini-2.5-flash",
            finish_reason="stop",
            provider="gemini"
        )
        mocks["llm_provider"].generate_response.return_value = mock_llm_response
        
        mocks["prompt_manager"].get_prompt.return_value = "Classify this intent: {message}"
        
        response = await engine.process_message(
            user_id="user123",
            message="What are your opening hours?",
            session_id=None
        )
        
        mocks["session_manager"].create_session.assert_called_once_with("user123", {})
        
        assert response["session_id"] == "new-session-id"
        assert "response" in response
        assert "intent" in response
        assert "requires_human_handoff" in response
        assert "suggested_actions" in response
    
    @pytest.mark.asyncio
    async def test_process_message_existing_session(self, conversation_engine):
        """Test processing message with existing session"""
        engine, mocks = conversation_engine
        
        existing_session = {
            "session_id": "existing-session",
            "user_id": "user123",
            "conversation_history": [
                {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"}
            ],
            "context": {"language": "en"},
            "current_intent": "greeting"
        }
        
        mocks["session_manager"].get_session.return_value = existing_session
        
        mock_llm_response = LLMResponse(
            content="appointment_booking",
            usage={"prompt_tokens": 15, "completion_tokens": 8, "total_tokens": 23},
            model="gemini-2.5-flash",
            finish_reason="stop",
            provider="gemini"
        )
        mocks["llm_provider"].generate_response.return_value = mock_llm_response
        mocks["prompt_manager"].get_prompt.return_value = "Classify intent: {message}"
        
        mocks["kafka_client"].send_task_request.return_value = "correlation-123"
        
        response = await engine.process_message(
            user_id="user123",
            message="I want to book an appointment",
            session_id="existing-session"
        )
        
        mocks["session_manager"].get_session.assert_called_with("existing-session")
        mocks["session_manager"].create_session.assert_not_called()
        
        mocks["kafka_client"].send_task_request.assert_called_once()
        call_args = mocks["kafka_client"].send_task_request.call_args
        assert call_args[1]["agent_topic"] == "appointment-agent-requests"
        assert call_args[1]["task_type"] == "appointment_booking"
        
        assert response["session_id"] == "existing-session"
        assert response["intent"] == "appointment_booking"
    
    @pytest.mark.asyncio
    async def test_classify_intent_pattern_matching(self, conversation_engine):
        """Test intent classification using pattern matching"""
        engine, mocks = conversation_engine
        
        session_data = {"conversation_history": [], "context": {}}
        
        intent = await engine._classify_intent("I want to book an appointment", session_data)
        assert intent == "appointment_booking"
        
        intent = await engine._classify_intent("Schedule me with a doctor", session_data)
        assert intent == "appointment_booking"
        
        intent = await engine._classify_intent("I need to reschedule my appointment", session_data)
        assert intent == "appointment_modify"
        
        intent = await engine._classify_intent("Cancel my booking", session_data)
        assert intent == "appointment_modify"
        
        intent = await engine._classify_intent("I have chest pain", session_data)
        assert intent == "medical_emergency"
        
        intent = await engine._classify_intent("This is an emergency", session_data)
        assert intent == "medical_emergency"
    
    @pytest.mark.asyncio
    async def test_classify_intent_llm_fallback(self, conversation_engine):
        """Test intent classification using LLM when patterns don't match"""
        engine, mocks = conversation_engine
        
        session_data = {"conversation_history": [], "context": {}}
        
        mock_llm_response = LLMResponse(
            content="pre_admission",
            usage={"prompt_tokens": 20, "completion_tokens": 3, "total_tokens": 23},
            model="gemini-2.5-flash",
            finish_reason="stop",
            provider="gemini"
        )
        mocks["llm_provider"].generate_response.return_value = mock_llm_response
        mocks["prompt_manager"].get_prompt.return_value = "Classify: {message}"
        
        intent = await engine._classify_intent("What should I prepare for surgery?", session_data)
        
        assert intent == "pre_admission"
        mocks["llm_provider"].generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_intent_llm_with_fallback_provider(self, conversation_engine):
        """Test intent classification with fallback to secondary LLM provider"""
        engine, mocks = conversation_engine
        
        session_data = {"conversation_history": [], "context": {}}
        
        mocks["llm_provider"].generate_response.side_effect = Exception("Primary LLM failed")
        
        mock_fallback_response = LLMResponse(
            content="post_discharge",
            usage={"prompt_tokens": 18, "completion_tokens": 4, "total_tokens": 22},
            model="claude-3-sonnet",
            finish_reason="end_turn",
            provider="anthropic"
        )
        mocks["fallback_provider"].generate_response.return_value = mock_fallback_response
        mocks["prompt_manager"].get_prompt.return_value = "Classify: {message}"
        
        intent = await engine._classify_intent("What medications should I take after discharge?", session_data)
        
        assert intent == "post_discharge"
        mocks["llm_provider"].generate_response.assert_called_once()
        mocks["fallback_provider"].generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_emergency(self, conversation_engine):
        """Test emergency handling"""
        engine, mocks = conversation_engine
        
        response = await engine._handle_emergency("session-123", "I'm having chest pain")
        
        assert response["requires_human_handoff"] is True
        assert "MEDICAL EMERGENCY DETECTED" in response["response"]
        assert "emergency_escalation" in response["suggested_actions"]
        assert "call_emergency_services" in response["suggested_actions"]
    
    @pytest.mark.asyncio
    async def test_handle_appointment_request(self, conversation_engine):
        """Test appointment request handling"""
        engine, mocks = conversation_engine
        
        session_data = {
            "context": {"user_id": "123"},
            "conversation_history": [{"role": "user", "content": "Hello"}]
        }
        
        mocks["kafka_client"].send_task_request.return_value = "correlation-456"
        
        response = await engine._handle_appointment_request(
            "session-123", 
            "Book me an appointment", 
            "appointment_booking", 
            session_data
        )
        
        mocks["kafka_client"].send_task_request.assert_called_once_with(
            agent_topic="appointment-agent-requests",
            task_type="appointment_booking",
            payload={
                "message": "Book me an appointment",
                "session_id": "session-123",
                "user_context": {"user_id": "123"},
                "conversation_history": [{"role": "user", "content": "Hello"}]
            }
        )
        
        assert response["correlation_id"] == "correlation-456"
        assert response["requires_human_handoff"] is False
        assert "wait_for_agent_response" in response["suggested_actions"]
    
    @pytest.mark.asyncio
    async def test_handle_general_info(self, conversation_engine):
        """Test general information handling"""
        engine, mocks = conversation_engine
        
        session_data = {
            "conversation_history": [],
            "context": {}
        }
        
        mock_llm_response = LLMResponse(
            content="Our hospital is open 24/7 for emergency services. Regular outpatient hours are 8 AM to 6 PM.",
            usage={"prompt_tokens": 25, "completion_tokens": 20, "total_tokens": 45},
            model="gemini-2.5-flash",
            finish_reason="stop",
            provider="gemini"
        )
        mocks["llm_provider"].generate_response.return_value = mock_llm_response
        mocks["prompt_manager"].get_prompt.return_value = "Answer: {message}"
        
        response = await engine._handle_general_info("session-123", "What are your hours?", session_data)
        
        assert "Our hospital is open 24/7" in response["response"]
        assert response["requires_human_handoff"] is False
        assert response["suggested_actions"] == []
        
        mocks["llm_provider"].generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_general_info_with_fallback(self, conversation_engine):
        """Test general info handling with fallback provider"""
        engine, mocks = conversation_engine
        
        session_data = {"conversation_history": [], "context": {}}
        
        mocks["llm_provider"].generate_response.side_effect = Exception("Primary failed")
        
        mock_fallback_response = LLMResponse(
            content="I can help you with general information about our services.",
            usage={"prompt_tokens": 15, "completion_tokens": 12, "total_tokens": 27},
            model="claude-3-sonnet",
            finish_reason="end_turn",
            provider="anthropic"
        )
        mocks["fallback_provider"].generate_response.return_value = mock_fallback_response
        mocks["prompt_manager"].get_prompt.return_value = "Answer: {message}"
        
        response = await engine._handle_general_info("session-123", "Can you help me?", session_data)
        
        assert "I can help you with general information" in response["response"]
        mocks["llm_provider"].generate_response.assert_called_once()
        mocks["fallback_provider"].generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, conversation_engine):
        """Test error handling in message processing"""
        engine, mocks = conversation_engine
        
        mocks["session_manager"].create_session.side_effect = Exception("Database error")
        
        response = await engine.process_message(
            user_id="user123",
            message="Hello",
            session_id=None
        )
        
        assert "technical difficulties" in response["response"]
        assert response["intent"] == "error"
        assert response["requires_human_handoff"] is True
        assert "contact_support" in response["suggested_actions"]
