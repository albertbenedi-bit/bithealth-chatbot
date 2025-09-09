import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.llm_abstraction.provider_interface import LLMRequest, LLMResponse
from src.llm_abstraction.gemini_provider import GeminiProvider
from src.llm_abstraction.anthropic_provider import AnthropicProvider

class TestGeminiProvider:
    
    @pytest.fixture
    def gemini_provider(self):
        return GeminiProvider(api_key="test_key", model_name="gemini-2.5-flash")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, gemini_provider):
        """Test successful response generation from Gemini"""
        request = LLMRequest(
            prompt="Hello, how are you?",
            max_tokens=100,
            temperature=0.7
        )
        
        mock_response = Mock()
        mock_response.text = "I'm doing well, thank you for asking!"
        
        with patch.object(gemini_provider.model, 'generate_content_async', return_value=mock_response):
            response = await gemini_provider.generate_response(request)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "I'm doing well, thank you for asking!"
            assert response.provider == "gemini"
            assert response.model == "gemini-2.5-flash"
            assert "prompt_tokens" in response.usage
            assert "completion_tokens" in response.usage
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, gemini_provider):
        """Test response generation with system prompt"""
        request = LLMRequest(
            prompt="What is the weather?",
            system_prompt="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.5
        )
        
        mock_response = Mock()
        mock_response.text = "I don't have access to current weather data."
        
        with patch.object(gemini_provider.model, 'generate_content_async', return_value=mock_response) as mock_generate:
            response = await gemini_provider.generate_response(request)
            
            call_args = mock_generate.call_args[0][0]
            assert "System: You are a helpful assistant." in call_args
            assert "User: What is the weather?" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, gemini_provider):
        """Test error handling in response generation"""
        request = LLMRequest(prompt="Test prompt")
        
        with patch.object(gemini_provider.model, 'generate_content_async', side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                await gemini_provider.generate_response(request)
            
            assert "Gemini API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, gemini_provider):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.text = "Hello"
        
        with patch.object(gemini_provider.model, 'generate_content_async', return_value=mock_response):
            is_healthy = await gemini_provider.health_check()
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, gemini_provider):
        """Test health check failure"""
        with patch.object(gemini_provider.model, 'generate_content_async', side_effect=Exception("Connection error")):
            is_healthy = await gemini_provider.health_check()
            assert is_healthy is False
    
    def test_get_provider_name(self, gemini_provider):
        """Test provider name"""
        assert gemini_provider.get_provider_name() == "gemini"
    
    def test_get_supported_models(self, gemini_provider):
        """Test supported models list"""
        models = gemini_provider.get_supported_models()
        assert isinstance(models, list)
        assert "gemini-pro" in models
        assert "gemini-pro-vision" in models
        assert "gemini-2.5-flash" in models


class TestAnthropicProvider:
    
    @pytest.fixture
    def anthropic_provider(self):
        return AnthropicProvider(api_key="test_key", model_name="claude-3-sonnet-20240229")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, anthropic_provider):
        """Test successful response generation from Anthropic"""
        request = LLMRequest(
            prompt="Hello, how are you?",
            max_tokens=100,
            temperature=0.7
        )
        
        mock_content = Mock()
        mock_content.text = "I'm doing well, thank you!"
        
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 8
        
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.stop_reason = "end_turn"
        
        with patch.object(anthropic_provider.client.messages, 'create', return_value=mock_response):
            response = await anthropic_provider.generate_response(request)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "I'm doing well, thank you!"
            assert response.provider == "anthropic"
            assert response.model == "claude-3-sonnet-20240229"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 8
            assert response.usage["total_tokens"] == 18
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, anthropic_provider):
        """Test response generation with system prompt"""
        request = LLMRequest(
            prompt="What is AI?",
            system_prompt="You are an AI expert.",
            max_tokens=50
        )
        
        mock_content = Mock()
        mock_content.text = "AI stands for Artificial Intelligence."
        
        mock_usage = Mock()
        mock_usage.input_tokens = 15
        mock_usage.output_tokens = 12
        
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.stop_reason = "end_turn"
        
        with patch.object(anthropic_provider.client.messages, 'create', return_value=mock_response) as mock_create:
            response = await anthropic_provider.generate_response(request)
            
            call_args = mock_create.call_args[1]['messages']
            assert len(call_args) == 2
            assert call_args[0]['role'] == 'system'
            assert call_args[0]['content'] == 'You are an AI expert.'
            assert call_args[1]['role'] == 'user'
            assert call_args[1]['content'] == 'What is AI?'
    
    def test_get_provider_name(self, anthropic_provider):
        """Test provider name"""
        assert anthropic_provider.get_provider_name() == "anthropic"
    
    def test_get_supported_models(self, anthropic_provider):
        """Test supported models list"""
        models = anthropic_provider.get_supported_models()
        assert isinstance(models, list)
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-opus-20240229" in models
        assert "claude-3-haiku-20240307" in models
