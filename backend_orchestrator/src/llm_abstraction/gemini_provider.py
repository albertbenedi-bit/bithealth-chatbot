import google.generativeai as genai
from typing import Dict, Any, Optional, List
import structlog
from .provider_interface import LLMProviderInterface, LLMRequest, LLMResponse

logger = structlog.get_logger()

class GeminiProvider(LLMProviderInterface):
    """Google Gemini LLM Provider"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        try:
            logger.info("Generating Gemini response", model=self.model_name)
            
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"System: {request.system_prompt}\n\nUser: {request.prompt}"
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            usage = {
                "prompt_tokens": len(full_prompt.split()),  # Rough estimation
                "completion_tokens": len(response.text.split()),  # Rough estimation
                "total_tokens": len(full_prompt.split()) + len(response.text.split())
            }
            
            return LLMResponse(
                content=response.text,
                usage=usage,
                model=self.model_name,
                finish_reason="stop",
                provider="gemini"
            )
            
        except Exception as e:
            logger.error("Error generating Gemini response", error=str(e))
            raise Exception(f"Gemini API error: {str(e)}")
    
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
            logger.error("Gemini health check failed", error=str(e))
            return False
    
    def get_provider_name(self) -> str:
        return "gemini"
    
    def get_supported_models(self) -> List[str]:
        return ["gemini-2.5-flash","gemini-pro", "gemini-pro-vision"]
