#Python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # --- Database Config ---
    DATABASE_URL: str

    # --- AI Model Config ---

    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    LLM_MODEL_NAME: str = 'gemini-2.5-flash' # e.g., "llama2", "gpt-4o"
    LLM_API_KEY: str = 'AIzaSyBsErNvPHekr4z2meNLLek9z1sMUC-TeU8' # If using API-based LLM
    GOOGLE_API_KEY: Optional[str] = 'AIzaSyBsErNvPHekr4z2meNLLek9z1sMUC-TeU8' # Include this

     # --- RAG Specific Config ---
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_K: int # <<< Ensure this is here
    SEARCH_TYPE: str # <<< Ensure this is here
    COLLECTION_NAME: str # <<< Add this line to read from environment

    # --- Add other settings if needed ---
    # OPENAI_API_KEY: Optional[str] = None
    KAFKA_REQUEST_TOPIC: str = Field(..., description="Kafka request topic")
    KAFKA_RESPONSE_TOPIC: str = Field(..., description="Kafka response topic")
    KAFKA_GROUP_ID: str = Field(..., description="Kafka group id")
    KAFKA_BOOTSTRAP_SERVERS: str = Field(..., description="Kafka bootstrap servers")


    class Config:
        env_file = ".env"
        # Optional: explicitly ignore extra inputs if you want to allow
        # environment variables not defined in the class without erroring
        # extra = "ignore"
    

settings = Settings()
