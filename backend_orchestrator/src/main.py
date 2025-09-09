from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import structlog
import asyncio
from contextlib import asynccontextmanager

from .llm_abstraction.provider_interface import LLMProviderInterface
from .llm_abstraction.gemini_provider import GeminiProvider
from .llm_abstraction.anthropic_provider import AnthropicProvider
from .llm_abstraction.prompt_manager import PromptManager
from .messaging.kafka_client import KafkaClient
from .session.session_manager import SessionManager
from .workflow.conversation_engine import ConversationEngine
from .websocket.websocket_manager import WebSocketManager
from .config.settings import Settings
import logging

# Initialize structlog and settings
logger = structlog.get_logger()
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    app.state.settings = settings

    # --- STRUCTLOG CONFIGURATION ---
    log_level_numeric = getattr(logging, app.state.settings.log_level.upper(), logging.DEBUG)

    logging.basicConfig(
        format="%(message)s",
        level=log_level_numeric,
        handlers=[logging.StreamHandler()]
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if app.state.settings.debug else structlog.processors.JSONRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            # If you have something like process_kafka_message_for_logging, review it
            structlog.processors.JSONRenderer(), # or console renderer
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level_numeric)
    )
    # --- END STRUCTLOG CONFIGURATION ---
    
    logger.info("Starting Backend AI Orchestrator", log_level=app.state.settings.log_level)

    app.state.llm_provider = GeminiProvider(settings.gemini_api_key)
    app.state.fallback_llm_provider = AnthropicProvider(settings.anthropic_api_key)
    app.state.prompt_manager = PromptManager()
    app.state.websocket_manager = WebSocketManager()
    
    # Initialize Kafka client
    app.state.kafka_client = KafkaClient(settings.kafka_bootstrap_servers)
    
    # --- START KAFKA CLIENT HERE ---
    try:
        logger.info("Attempting to start Kafka client...")
        await app.state.kafka_client.start() # <-- Call the start method
        logger.info("Kafka client started successfully.")
    except Exception as e:
        logger.critical(f"FATAL ERROR: Failed to start Kafka client during lifespan: {e}", exc_info=True)
        # Re-raise the exception to prevent the app from starting if Kafka is crucial
        raise RuntimeError("Application startup failed due to Kafka client initialization error.") from e
    # --- END KAFKA CLIENT START ---

    # Initialize session manager with fallback
    try:
        app.state.session_manager = SessionManager(settings.redis_url)
        await app.state.session_manager.initialize()
        logger.info("Session manager initialized successfully")
    except Exception as e:
        logger.critical("FATAL ERROR: Failed to initialize session manager. Application cannot start.", error=str(e), exc_info=True)
        raise RuntimeError("Application startup failed due to Session Manager initialization error.") from e
    
    # Initialize conversation engine
    app.state.conversation_engine = ConversationEngine(
        llm_provider=app.state.llm_provider,
        fallback_provider=app.state.fallback_llm_provider,
        prompt_manager=app.state.prompt_manager,
        kafka_client=app.state.kafka_client, # Now kafka_client.producer will be initialized
        session_manager=app.state.session_manager,
        websocket_manager=app.state.websocket_manager
    )
    
    # Removed: logger.info("Skipping Kafka startup for WebSocket testing - server ready for connections")
    
    yield
    
    logger.info("Shutting down Backend AI Orchestrator")
    await app.state.kafka_client.stop()

app = FastAPI(
    title="Healthcare Chatbot - Backend AI Orchestrator",
    description="Central orchestration service for healthcare chatbot AI agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    requires_human_handoff: bool = False
    suggested_actions: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    correlation_id: Optional[str] = None

@app.get("/health")
async def health_check():
    try:
        health_status = {"status": "healthy", "service": "backend-orchestrator", "checks": {}}
        
        try:
            await app.state.session_manager.get_active_session_count()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Now this check should correctly reflect Kafka producer status after startup
        try:
            if app.state.kafka_client.producer: # Directly check if producer object exists
                health_status["checks"]["kafka"] = "healthy"
            else:
                health_status["checks"]["kafka"] = "not_initialized" # If for some reason it's still None
        except Exception as e: # Catch any other errors (e.g., if app.state.kafka_client itself is None, though it shouldn't be)
            health_status["checks"]["kafka"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        try:
            if app.state.llm_provider:
                health_status["checks"]["llm_provider"] = "healthy"
            else:
                health_status["checks"]["llm_provider"] = "not_initialized"
        except Exception as e:
            health_status["checks"]["llm_provider"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        if health_status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_status)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "service": "backend-orchestrator", "error": str(e)})

@app.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    try:
        logger.info(
            "Processing chat request", 
            user_id=request.user_id, 
            message_preview=request.message[:50],
            received_session_id=request.session_id
        )
        
        import time
        start_time = time.time()
        
        response = await app.state.conversation_engine.process_message(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            context=request.context or {}
        )
        
        return {
            "response": response.get("response", "I'm here to help!"),
            "session_id": response.get("session_id"),
            "intent": response.get("intent", "general_info"),
            "requires_human_handoff": response.get("requires_human_handoff", False),
            "suggested_actions": response.get("suggested_actions", []),
            "confidence_score": response.get("confidence_score", 0.8),
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "correlation_id": response.get("correlation_id")
        }
        
    except Exception as e:
        logger.error("Error processing chat request", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    try:
        if not app.state.session_manager:
            raise HTTPException(status_code=503, detail="Session service is unavailable")
            
        session_data = await app.state.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving session", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    try:
        await app.state.session_manager.clear_session(session_id)
        return {"message": "Session cleared successfully"}
    except Exception as e:
        logger.error("Error clearing session", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await app.state.websocket_manager.connect(session_id, websocket)
    logger.info("WebSocket connected", session_id=session_id) # ADD THIS
    try:
        while True:
            data = await websocket.receive_text() # This will block until a message is received
            logger.info("WebSocket received message (but not processing here)", session_id=session_id, message_data=data[:50]) # ADD THIS
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id) # ADD THIS
        app.state.websocket_manager.disconnect(session_id)
    except Exception as e:
        logger.error("WebSocket error", session_id=session_id, error=str(e), exc_info=True) # ADD THIS

@app.get("/metrics")
async def get_metrics():
    return {
        "active_sessions": await app.state.session_manager.get_active_session_count(),
        "active_websocket_connections": app.state.websocket_manager.get_active_connections_count(),
        "llm_provider": "gemini",
        "fallback_provider": "anthropic"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)