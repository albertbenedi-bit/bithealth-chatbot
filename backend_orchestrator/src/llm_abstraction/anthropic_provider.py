import anthropic
from typing import Dict, Any, Optional, List
import structlog
from .provider_interface import LLMProviderInterface, LLMRequest, LLMResponse

logger = structlog.get_logger()

class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude LLM Provider"""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = anthropic.Anthropic(api_key=api_key)
        
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        try:
            logger.info("Generating Anthropic response", model=self.model_name)
            
            messages = []
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": request.prompt
            })
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=messages
            )
            
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=response.content[0].text,
                usage=usage,
                model=self.model_name,
                finish_reason=response.stop_reason,
                provider="anthropic"
            )
            
        except Exception as e:
            logger.error("Error generating Anthropic response", error=str(e))
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def health_check(self) -> bool:
        try:
            test_request = LLMRequest(
                prompt="Hello",
                max_tokens=10,
                temperature=0.1
            )
            await self.generate_response(test_request)
            return True
        except Exception as e:
            logger.error("Anthropic health check failed", error=str(e))
            return False
    
    def get_provider_name(self) -> str:
        return "anthropic"
    
    def get_supported_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307"
        ]
