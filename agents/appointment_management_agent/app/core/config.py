#Python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # --- Database Config ---
    DATABASE_URL: str = Field(..., description="Database URL for appointment storage")

    # --- AI Model Config ---
    LLM_MODEL_NAME: str = Field(
        default='gemini-2.5-flash',
        #default='gemini-pro',
        description="The name of the LLM model to use"
    )
    
    GOOGLE_API_KEY: str = Field(
        ...,  # This makes it required
        description="Google API key for Gemini model access",
        min_length=1  # Ensure it's not empty
    )

    # --- Kafka Config ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field(..., description="Kafka bootstrap servers")
    KAFKA_REQUEST_TOPIC: str = Field(..., description="Kafka request topic for this agent")
    KAFKA_RESPONSE_TOPIC: str = Field(..., description="Kafka response topic for this agent")
    KAFKA_GROUP_ID: str = Field(..., description="Kafka consumer group ID for this agent")
    
    # --- Appointment Service Config ---
    MAX_BOOKING_DAYS_AHEAD: int = 60
    MIN_BOOKING_HOURS_NOTICE: int = 24
    WORKING_HOURS_START: int = 9
    WORKING_HOURS_END: int = 17
    APPOINTMENT_DURATION_MINUTES: int = 30

    class Config:
        env_file = ".env"
        # Optional: explicitly ignore extra inputs if you want to allow
        # environment variables not defined in the class without erroring
        # extra = "ignore"

settings = Settings()
