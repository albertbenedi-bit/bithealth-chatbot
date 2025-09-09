from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

@dataclass
class LLMRequest:
    """Request object for LLM providers"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: Optional[str] = None

@dataclass
class LLMResponse:
    """Response object from LLM providers"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    provider: str

class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM provider
        
        Args:
            request: LLMRequest object containing prompt and parameters
            
        Returns:
            LLMResponse object containing the generated content and metadata
            
        Raises:
            Exception: If the LLM provider encounters an error
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is healthy and accessible
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the LLM provider
        
        Returns:
            str: Provider name (e.g., 'gemini', 'anthropic')
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider
        
        Returns:
            List[str]: List of supported model names
        """
        pass
