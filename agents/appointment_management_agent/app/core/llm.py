"""
LLM client module for appointment management agent.
Following the same architecture as rag-service-2 for consistency.
"""
from google.generativeai import GenerativeModel
import google.generativeai as genai
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

def load_llm_client(model_name: str, api_key: Optional[str] = None):
    """
    Load and initialize Google Generative AI client.
    
    Args:
        model_name: The name of the Gemini model to use
        api_key: Google API key for authentication
        
    Returns:
        An instance of GenerativeModel
        
    Raises:
        ValueError: If API key is missing or invalid
    """
    if not api_key:
        logger.error("No API key provided")
        raise ValueError("Google API key is required for Gemini models")
    
    if not isinstance(api_key, str):
        logger.error(f"Invalid API key type: {type(api_key)}")
        raise ValueError("API key must be a string")
    
    if len(api_key.strip()) == 0:
        logger.error("Empty API key provided")
        raise ValueError("API key cannot be empty")

    # Log partial key for debugging (first 8 chars only)
    key_preview = api_key[:8] + "..." if len(api_key) > 8 else "invalid"
    logger.info(f"Attempting to initialize with API key starting with: {key_preview}")
        
    try:
        logger.info(f"Configuring Google Generative AI client")
        genai.configure(api_key=api_key)
        
        logger.info(f"Creating model instance for: {model_name}")
        # model = GenerativeModel(model_name)
        model = GenerativeModel(
            model_name=f"models/{model_name}",
            generation_config={"temperature": 0.1}
        )

        # Validate the API key with a test call
        logger.info("Validating API key with test request")
        try:
            generation_config = {"temperature": 0.1, "max_output_tokens": 10}
            response = model.generate_content(
                "test connection",
                generation_config=generation_config
            )
            
            # Properly handle multi-part responses
            if not response or not response.candidates or not response.candidates[0].content.parts:
                raise ValueError("Model returned empty response")
                
            # Get the text from the first part of the first candidate
            response_text = response.candidates[0].content.parts[0].text
            if not response_text:
                raise ValueError("Model returned empty text")
                
            logger.info("API key validation successful")
            
        except Exception as key_error:
            logger.error(f"API key validation failed with error: {str(key_error)}")
            raise ValueError(f"API key validation failed: {str(key_error)}")
            
        logger.info(f"Google Generative AI client successfully initialized for model: {model_name}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {str(e)}", exc_info=True)
        raise ValueError(f"LLM initialization failed: {str(e)}")
