
from fastapi import FastAPI
from app.api.v1 import endpoints
from app.messaging.kafka_client import KafkaClient
from app.handlers.kafka_handler import KafkaMessageHandler
from app.core.config import settings
import asyncio
from contextlib import asynccontextmanager
import structlog

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    This is the recommended way to manage resources like Kafka clients.
    """
    logger.info("RAG Service starting up...")
    # --- Startup ---
    kafka_consumer_task = None
    try:
        # Store singletons on the app.state object
        app.state.kafka_client = KafkaClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await app.state.kafka_client.start()

        app.state.kafka_handler = KafkaMessageHandler(app.state.kafka_client)
        await app.state.kafka_handler.initialize_dependencies()

        app.state.kafka_client.subscribe_to_requests(app.state.kafka_handler.handle_message)

        # Start the consumer loop as a background task
        kafka_consumer_task = asyncio.create_task(app.state.kafka_client.start_consuming())
        logger.info("service_startup_kafka_integration_complete")

        yield

    except Exception as e:
        logger.error("Failed to start RAG service due to an exception.", exc_info=True)
        # Re-raise to prevent the application from starting in a broken state.
        raise RuntimeError("Application startup failed") from e
    finally:
        # --- Shutdown ---
        logger.info("RAG Service shutting down...")
        if kafka_consumer_task and not kafka_consumer_task.done():
            kafka_consumer_task.cancel()
            try:
                await kafka_consumer_task
            except asyncio.CancelledError:
                logger.info("Kafka consumer task cancelled.")
        if hasattr(app.state, 'kafka_client') and app.state.kafka_client:
            await app.state.kafka_client.stop()
        logger.info("service_shutdown_complete")

# Create the FastAPI application instance
# You can add metadata here that appears in the OpenAPI docs (Swagger UI)
app = FastAPI(
    title="RAG Service",
    description="Service for performing Retrieval Augmented Generation on internal documents.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Include the API router ---
# This adds all the routes defined in app/api/v1/endpoints.py to the app
app.include_router(endpoints.router)

# --- Optional: Add Middleware ---
# Middleware runs for every request. Common uses: logging, authentication, CORS, tracing.

from fastapi.middleware.cors import CORSMiddleware
#Add CORS middleware if your frontend is on a different origin (port, domain, protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Replace with the actual origin(s) of your frontend in production!
    allow_credentials=True,
    allow_methods=["*"], # Or specify allowed methods like ["GET", "POST"]
    allow_headers=["*"], # Or specify allowed headers
)

# --- Optional: Configure Logging ---
# Basic logging can be configured here or ideally in a separate logging.py file
import logging
import sys
import structlog

# Configure standard logging to be handled by structlog
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structlog for structured, context-aware logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Use ConsoleRenderer for development for pretty, colored output.
        # In production, swap this for structlog.processors.JSONRenderer()
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger("rag-service")
