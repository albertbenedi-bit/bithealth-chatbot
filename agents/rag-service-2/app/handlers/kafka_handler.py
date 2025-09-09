from typing import Dict, Any, Optional
import structlog
from app.models.kafka_messages import TaskRequest, TaskResponse, GeneralInfoPayload
from app.models.rag import Question
from app.core.retriever import PGVectorRetriever
from app.core.dependencies import get_embedding_model, get_llm_client
from app.core.rag_service import RAGService
from langchain_community.vectorstores.pgvector import PGVector
from app.core.config import settings

logger = structlog.get_logger()

class KafkaMessageHandler:
    """Handler for processing Kafka messages for RAG service"""
    def __init__(self, kafka_client):
        self.kafka_client = kafka_client
        # The RAGService instance will be created during the startup lifecycle.
        self.rag_service: Optional[RAGService] = None
        
    async def initialize_dependencies(self):
        """Initialize RAG dependencies"""
        # try:
        #     self.retriever = get_retriever()
        #     self.llm_client = get_llm_client()
        #     logger.info("RAG dependencies initialized for Kafka handler")
        # except Exception as e:
        #     logger.error("Failed to initialize RAG dependencies", error=str(e))
        #     raise
        try:
            # Manually create dependencies since we are outside FastAPI's request cycle
            embeddings = get_embedding_model()
            if embeddings is None:
                raise RuntimeError("Embedding model failed to initialize.")

            llm_client = get_llm_client()
            if llm_client is None:
                raise RuntimeError("LLM client failed to initialize.")

            pgvector_store_instance = PGVector(
                connection_string=settings.DATABASE_URL,
                embedding_function=embeddings,
                collection_name=settings.COLLECTION_NAME,
            )
            retriever = PGVectorRetriever(pgvector_store=pgvector_store_instance)
            # Create and store a single RAGService instance for the handler's lifetime.
            self.rag_service = RAGService(retriever=retriever, llm_client=llm_client)
            logger.info("kafka_handler_dependencies_initialized")
        except Exception as e:
            logger.error("kafka_handler_dependency_initialization_failed", exc_info=True)
            raise
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming Kafka message"""
        logger.info("kafka_message_received", message=message)
        try:
            task_request = TaskRequest(**message)
            logger.info("processing_kafka_task_request", correlation_id=task_request.correlation_id, task_type=task_request.task_type)
            
            if task_request.task_type == "general_info":
                await self._handle_general_info_request(task_request)
            else:
                logger.warning("unsupported_task_type_received", task_type=task_request.task_type, correlation_id=task_request.correlation_id)
                await self._send_error_response(
                    task_request.correlation_id,
                    f"Unsupported task type: {task_request.task_type}"
                )
                
        except Exception as e:
            logger.error("kafka_message_handling_error", error=str(e), message=message, exc_info=True)
            correlation_id = message.get("correlation_id", "unknown")
            # Try to extract session_id from message payload if available
            session_id = None
            try:
                if "payload" in message and "session_id" in message["payload"]:
                    session_id = message["payload"]["session_id"]
            except (KeyError, TypeError):
                pass
            await self._send_error_response(correlation_id, str(e), session_id)
    
    async def _handle_general_info_request(self, task_request: TaskRequest):
        """Handle general info request using the centralized RAGService."""
        try:
            payload = GeneralInfoPayload(**task_request.payload)
            session_id = payload.session_id
            
            if not self.rag_service:
                raise RuntimeError("RAGService not initialized for Kafka handler.")
                
            # Delegate the entire RAG process to the RAGService.
            rag_result = self.rag_service.ask(question=payload.message)
            
            result = {
                "response": rag_result.text,
                "sources": rag_result.sources,
                "requires_human_handoff": False,
                "suggested_actions": [],
                "session_id": session_id
            }
            
            await self._send_success_response(task_request.correlation_id, result)
            logger.info("general_info_request_processed_successfully", 
                       correlation_id=task_request.correlation_id)
            
        except Exception as e:
            logger.error("general_info_request_processing_failed", 
                        correlation_id=task_request.correlation_id, 
                        error=str(e),
                        exc_info=True)
            session_id = task_request.payload.get("session_id")
            await self._send_error_response(
                task_request.correlation_id,
                "An internal error occurred while processing your request.",
                session_id=session_id
            )
    
    async def _send_success_response(self, correlation_id: str, result: Dict[str, Any]):
        """Send successful response via Kafka"""
        logger.info("sending_success_response", correlation_id=correlation_id)
        await self.kafka_client.send_task_response(
            correlation_id=correlation_id,
            status="SUCCESS",
            result=result
        )
    
    async def _send_error_response(self, correlation_id: str, error_message: str, session_id: Optional[str] = None):
        """Send error response via Kafka"""
        logger.error("sending_error_response", correlation_id=correlation_id, error=error_message, session_id=session_id)
        result = {
            "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            "sources": [],
            "requires_human_handoff": True,
            "suggested_actions": ["try_again_later"],
            "error": error_message,
            "session_id": session_id
        }
        await self.kafka_client.send_task_response(
            correlation_id=correlation_id,
            status="ERROR",
            result=result
        )
