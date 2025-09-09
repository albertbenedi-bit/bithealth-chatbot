"""
Logging configuration for the appointment agent.
"""
import structlog
import logging
import sys

def configure_logging():
    """Configure structured logging similar to RAG service."""
    # Set kafka logs to WARNING to reduce noise
    for logger_name in [
        'kafka',
        'kafka.conn',
        'kafka.client',
        'kafka.consumer',
        'kafka.producer',
        'kafka.cluster',
        'kafka.coordinator',
        'kafka.protocol'
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Suppress noisy loggers
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('kafka.conn').setLevel(logging.WARNING)
    logging.getLogger('kafka.client').setLevel(logging.WARNING)
    logging.getLogger('kafka.consumer').setLevel(logging.WARNING)
    logging.getLogger('kafka.producer').setLevel(logging.WARNING)
