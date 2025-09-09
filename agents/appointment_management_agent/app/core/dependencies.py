import structlog
from functools import lru_cache
from app.core.appointment_service import AppointmentService
from app.core.config import settings
from app.core.llm import load_llm_client

logger = structlog.get_logger()

@lru_cache()
def get_llm_client():
    """Get the Gemini Pro model client"""
    try:
        model = load_llm_client(
            model_name=settings.LLM_MODEL_NAME,
            api_key=settings.GOOGLE_API_KEY
        )
        logger.info("llm_client_initialized", model=settings.LLM_MODEL_NAME)
        return model
    except Exception as e:
        logger.error("llm_client_initialization_failed", error=str(e))
        raise

def get_appointment_service():
    """Get the AppointmentService instance"""
    llm_client = get_llm_client()
    return AppointmentService(llm_client=llm_client)
