from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    kafka_bootstrap_servers: str

    gemini_api_key: str
    anthropic_api_key: str

    default_llm_provider: str = "gemini"
    fallback_llm_provider: str = "anthropic"
    max_tokens: int = 1000
    temperature: float = 0.7

    log_level: str = "INFO"
    structured_logging: bool = True

    # Added fields to match .env and fix pydantic extra_forbidden errors
    service_name: str = "backend-orchestrator"
    service_version: str = "1.0.0"
    session_timeout_minutes: int = 30
    max_conversation_history: int = 50
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    debug: bool = False
    reload: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
