from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

# Import your dependencies
from app.core.dependencies import (
    get_db,
    get_llm_client,
    get_retriever,
    get_rag_service
)
from app.core.retriever import PGVectorRetriever
from app.core.rag_service import RAGService
from app.models.rag import Question, Answer
from app.messaging.kafka_client import KafkaClient
from app.core.config import settings

router = APIRouter(prefix="/v1", tags=["rag"]) # Use v1 prefix for versioning

# --- /ask Endpoint ---
@router.post("/ask", response_model=Answer) # Specify the response model for docs and validation
def ask_question(
    question: Question,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Receives a user query, performs RAG to find relevant information,
    and returns an AI-generated answer based on internal documents.
    """
    print(f"Received question: {question.text}")
    try:
        rag_result = rag_service.ask(question.text)
        return Answer(text=rag_result.text, sources=rag_result.sources)
    except Exception as e:
        print(f"An error occurred during RAG processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request."
        )

# --- /health Endpoint ---
@router.get("/health")
async def health_check(request: Request):
    """
    Checks the health of the RAG service and its primary dependencies, including Kafka.
    """
    kafka_status = "error"
    kafka_error = "Kafka client not found in application state."
    
    # Check the status of the singleton Kafka client managed by the application's lifespan.
    if hasattr(request.app.state, 'kafka_client') and request.app.state.kafka_client is not None:
        if request.app.state.kafka_client.is_running():
            kafka_status = "ok"
            kafka_error = None
        else:
            kafka_error = "Kafka client is initialized but not running."

    health = {
        "status": "ok" if kafka_status == "ok" else "degraded",
        "message": "RAG service is healthy." if kafka_status == "ok" else "RAG service is running, but Kafka connection failed.",
        "kafka_status": kafka_status,
        "kafka_error": kafka_error
    }

    if health["status"] != "ok":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health)

    return health