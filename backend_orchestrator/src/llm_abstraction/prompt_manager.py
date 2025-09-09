import yaml
import os
from typing import Dict, Any, Optional
import structlog
from pathlib import Path

logger = structlog.get_logger()

class PromptManager:
    """Manages prompt templates for different agents and use cases"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(__file__).parent.parent / prompts_dir
        self.prompts_cache: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates from files"""
        try:
            if not self.prompts_dir.exists():
                logger.warning("Prompts directory not found", path=str(self.prompts_dir))
                return
            
            for prompt_file in self.prompts_dir.glob("*.txt"):
                prompt_name = prompt_file.stem
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts_cache[prompt_name] = f.read().strip()
                    
            logger.info("Loaded prompts", count=len(self.prompts_cache))
            
        except Exception as e:
            logger.error("Error loading prompts", error=str(e))
    
    def get_prompt(self, prompt_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt template with optional variable substitution"""
        try:
            if prompt_name not in self.prompts_cache:
                logger.error("Prompt template not found in cache", prompt_name=prompt_name)
                raise FileNotFoundError(f"Prompt template '{prompt_name}' not found in prompts directory.")
            
            prompt = self.prompts_cache[prompt_name]
            
            if variables:
                prompt = prompt.format(**variables)
            
            return prompt
            
        except Exception as e:
            logger.error("Error getting prompt", prompt_name=prompt_name, error=str(e))
            raise
    
    def list_prompts(self) -> list:
        """List all available prompt names"""
        return list(self.prompts_cache.keys())
    
    def reload_prompts(self):
        """Reload all prompts from files"""
        self.prompts_cache.clear()
        self._load_prompts()
