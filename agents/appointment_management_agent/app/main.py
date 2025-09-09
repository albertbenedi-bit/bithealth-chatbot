import asyncio
import sys
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, HTTPException, Request
from app.core.config import settings
from app.handlers.kafka_handler import KafkaMessageHandler
from app.messaging.kafka_client import KafkaClient

# --- Logging Configuration ---
from app.core.logging_config import configure_logging
configure_logging()
logger = structlog.get_logger("appointment-agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    Initializes Kafka client and handler, manages background tasks.
    """
    logger.info("appointment_agent_starting")
    kafka_consumer_task = None
    
    try:
        # Initialize Kafka client
        app.state.kafka_client = KafkaClient()
        await app.state.kafka_client.start()

        # Initialize Kafka handler with dependencies
        app.state.kafka_handler = KafkaMessageHandler(app.state.kafka_client)
        await app.state.kafka_handler.initialize_dependencies()

        # Subscribe to Kafka topics
        app.state.kafka_client.subscribe_to_requests(app.state.kafka_handler.handle_message)

        # Start Kafka consumer in background
        kafka_consumer_task = asyncio.create_task(app.state.kafka_client.start_consuming())
        logger.info("appointment_agent_started", 
                   kafka_topic=settings.KAFKA_REQUEST_TOPIC)
        yield
        
    except Exception as e:
        logger.error("appointment_agent_startup_failed",
                    error=str(e),
                    exc_info=True)
        raise RuntimeError("Application startup failed") from e
        
    finally:
        logger.info("Appointment Agent is shutting down...")
        if kafka_consumer_task and not kafka_consumer_task.done():
            kafka_consumer_task.cancel()
            try:
                await kafka_consumer_task
            except asyncio.CancelledError:
                logger.info("Kafka consumer task successfully cancelled.")
        
        if hasattr(app.state, 'kafka_client') and app.state.kafka_client:
            await app.state.kafka_client.stop()
        logger.info("Appointment Agent shutdown complete.")

app = FastAPI(
    title="Appointment Management Agent",
    description="A microservice agent to handle booking, modifying, and querying appointments.",
    version="1.0.0",
    lifespan=lifespan
)

# Import and include API routers
from app.api.v1 import endpoints
app.include_router(endpoints.router)

@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint.
    Checks the status of the service and its dependencies (Kafka, LLM).
    Returns 503 if any dependency is unhealthy.
    """
    # Check Kafka status
    kafka_client: KafkaClient = getattr(request.app.state, 'kafka_client', None)
    # Assuming the KafkaClient has an `is_running()` method
    kafka_healthy = kafka_client is not None and kafka_client.is_running()

    # Check LLM service status
    kafka_handler = getattr(request.app.state, 'kafka_handler', None)
    llm_healthy = (kafka_handler is not None and 
                   hasattr(kafka_handler, 'appointment_service') and 
                   kafka_handler.appointment_service is not None)
    
    status = "healthy" if kafka_healthy and llm_healthy else "degraded"

    health_details = {
        "status": status,
        "service": "appointment-management-agent",
        "dependencies": {
            "kafka": "ok" if kafka_healthy else "error",
            "llm": "ok" if llm_healthy else "error"
        }
    }

    if status != "healthy":
        raise HTTPException(status_code=503, detail=health_details)
    
    return health_details
