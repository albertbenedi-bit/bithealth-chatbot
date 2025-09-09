
# rag-service/app/core/dependencies.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base # Used for model definition if done here

# Import your custom Retriever class
from app.core.retriever import PGVectorRetriever # <<< ADD THIS IMPORT
from app.core.rag_service import RAGService

# Imports for RAG components
# from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import Ollama
from langchain_huggingface import HuggingFaceEmbeddings # Modern, recommended Embeddings import for Hugging Face models
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings # Import if using Google models
from langchain_community.vectorstores.pgvector import PGVector

from .config import settings # Import your settings object
from typing import Generator

# --- Database Dependency ---
# Import FastAPI components, including Depends
from fastapi import Depends # <<< THIS LINE MUST BE HERE


# SQLAlchemy Database URL
DATABASE_URL = settings.DATABASE_URL

# Create a SQLAlchemy engine
# The engine is typically a singleton for the application
# pool_pre_ping=True helps reconnect if the database connection is lost
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session
# This is not a singleton; you need a new session for each request/unit of work
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models (can also be defined in models.py)
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency that provides a new database session per request.
    The session is closed automatically after the request is finished.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# --- Embedding Model Dependency ---

# Initialize the embedding model once when the application starts
# This is a singleton dependency

print(f"Initializing embedding model: {settings.EMBEDDING_MODEL_NAME}")
try:
    # Example for Sentence Transformers
    if settings.EMBEDDING_MODEL_NAME == "all-MiniLM-L6-v2": # Or check based on a prefix/config
         # embedding_model_instance = SentenceTransformerEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
         #print("Sentence Transformers model initialized.")
         embedding_model_instance = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
         print("Hugging Face model initialized.")
    # Example for Google Generative AI Embeddings (if configured)
    elif settings.GOOGLE_API_KEY and settings.EMBEDDING_MODEL_NAME == "models/embedding-001":
         print("Initializing Google Generative AI Embeddings...")
         embedding_model_instance = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY)
         print("Google Generative AI Embeddings initialized.")
    else:
         raise ValueError(f"Unsupported or misconfigured embedding model: {settings.EMBEDDING_MODEL_NAME}")

except Exception as e:
     print(f"FATAL ERROR: Failed to initialize embedding model '{settings.EMBEDDING_MODEL_NAME}'.")
     print(f"Details: {e}")
     # Depending on your error handling strategy, you might want to exit or mark the service as unhealthy
     # For now, we'll just set it to None, but this service won't function.
     embedding_model_instance = None


# def get_embedding_model() -> SentenceTransformerEmbeddings | GoogleGenerativeAIEmbeddings: # Adjust return type based on potential models
def get_embedding_model() -> HuggingFaceEmbeddings | GoogleGenerativeAIEmbeddings: # Adjust return type based on potential models
     """
     Dependency that provides the singleton embedding model instance.
     """
     # In a real application, you might add a check here to ensure the model was initialized successfully
     # if embedding_model_instance is None:
     #     raise HTTPException(status_code=500, detail="Embedding model not initialized")
     return embedding_model_instance

# --- LLM Client Dependency ---

# Initialize the LLM client once when the application starts
# This is a singleton dependency

print(f"Initializing LLM client: {settings.LLM_MODEL_NAME}")
try:
    # Example for Ollama
    if not settings.GOOGLE_API_KEY and settings.LLM_MODEL_NAME.lower() == "llama2": # Or other Ollama models
        llm_client_instance = Ollama(model=settings.LLM_MODEL_NAME)
        print(f"Ollama client initialized for model: {settings.LLM_MODEL_NAME}")
    # Example for Google Generative AI LLM (if configured)
    elif settings.GOOGLE_API_KEY and settings.LLM_MODEL_NAME.startswith("gemini"):
        print(f"Initializing Google Generative AI client for model: {settings.LLM_MODEL_NAME}")
        llm_client_instance = ChatGoogleGenerativeAI(model=settings.LLM_MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY)
        print(f"Google Generative AI client initialized for model: {settings.LLM_MODEL_NAME}")
    else:
        raise ValueError(f"Unsupported or misconfigured LLM model: {settings.LLM_MODEL_NAME}")

except Exception as e:
    print(f"FATAL ERROR: Failed to initialize LLM client '{settings.LLM_MODEL_NAME}'.")
    print(f"Details: {e}")
    # Depending on your error handling strategy, handle this fatal error.
    llm_client_instance = None


def get_llm_client() -> Ollama | ChatGoogleGenerativeAI: # Adjust return type
    """
    Dependency that provides the singleton LLM client instance.
    """
    # In a real application, you might add a check here to ensure the client was initialized successfully
    # if llm_client_instance is None:
    #     raise HTTPException(status_code=500, detail="LLM client not initialized")
    return llm_client_instance

# --- PGVector Retriever Dependency ---
# This dependency combines the DB session and embedding model
# It needs a DB session (per request) and the embedding model (singleton)

def get_vector_store_retriever(
    db_session: SessionLocal = Depends(get_db), # Inject the DB session
    embeddings = Depends(get_embedding_model) # Inject the embedding model
) -> PGVector:
    """
    Dependency that provides a configured PGVector retriever instance per request.
    """
    # You need to recreate the PGVector instance per request because it depends on the session.
    # However, it reuses the singleton embedding model and engine.
    vector_store = PGVector(
        connection_string=settings.DATABASE_URL, # PGVector internal needs the connection string too, adjust if pooling is managed differently
        embedding_function=embeddings,
        collection_name=settings.COLLECTION_NAME, # Use the same collection name as in your indexing script
        # session=db_session # Sometimes PGVector allows passing session directly, check library version
    )
    print("PGVector store instance initialized.")
    # Get the retriever instance from the vector store
    retriever = vector_store.as_retriever(
        search_kwargs={"k": settings.RETRIEVAL_K}, # RETRIEVAL_K should be in settings
        search_type=settings.SEARCH_TYPE # SEARCH_TYPE should be in settings
    )
    return retriever

# --- PGVector Retriever Dependency ---
# This dependency provides an instance of our custom PGVectorRetriever class.
# It needs the PGVector store instance which itself requires dependencies.

# We'll define a dependency that gets the raw PGVector instance first
# This requires the database session and the embedding model
def get_pgvector_store_instance(
    db_session = Depends(get_db), # Inject the DB session
    embeddings = Depends(get_embedding_model) # Inject the embedding model
): # No return type hint here yet, as PGVector might not be fully typed externally
    """
    Dependency that provides a configured Langchain PGVector store instance.
    """
    # You need to recreate the PGVector instance per request because it depends on the session.
    # However, it reuses the singleton embedding model and engine.
    print("Initializing PGVector store instance...")
    vector_store = PGVector(
        connection_string=settings.DATABASE_URL,
        embedding_function=embeddings,
        collection_name=settings.COLLECTION_NAME,
        # Optional: Pass session directly if your langchain-pgvector version supports it
        # session=db_session
    )
    print("PGVector store instance initialized.")
    return vector_store # This returns a Langchain PGVector object


# Now, define the dependency that provides our custom retriever instance
# It depends on getting the PGVector store instance first
def get_retriever(
    pgvector_store_instance: PGVector = Depends(get_pgvector_store_instance) # Inject the PGVector instance
) -> PGVectorRetriever: # <<< Set the return type to your custom class
    """
    Dependency that provides a configured PGVectorRetriever instance.
    """
    print("Initializing custom PGVectorRetriever instance...")
    # Create an instance of our custom retriever class, passing the PGVector store
    retriever = PGVectorRetriever(pgvector_store=pgvector_store_instance)
    print("Custom PGVectorRetriever instance initialized.")
    return retriever # Return the custom retriever instance


# --- RAG Service Dependency ---
def get_rag_service(
    retriever: PGVectorRetriever = Depends(get_retriever),
    llm_client = Depends(get_llm_client)
) -> RAGService:
    """
    Dependency that provides a configured RAGService instance.
    """
    return RAGService(retriever=retriever, llm_client=llm_client)

# Note: You will need to adjust the import in your endpoints.py
# to correctly import 'get_retriever' from app.core.dependencies.
# Your endpoints.py should already be trying to import 'get_retriever'.