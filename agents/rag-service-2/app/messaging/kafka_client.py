import asyncio
from confluent_kafka import Producer, Consumer
import json
import uuid
from typing import Dict, Any, Optional, Callable
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class KafkaClient:
    """Kafka client for RAG service A2A communication"""
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self.consumer = None
        self.message_handler = None
        self._running = False
        
    async def start(self):
        """Initialize Kafka producer and consumer"""
        try:
            self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
            logger.info(f"Kafka producer initialized for servers: {self.bootstrap_servers}")
            self.consumer = Consumer({
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': settings.KAFKA_GROUP_ID,
                'auto.offset.reset': 'earliest'
            })
            logger.info(f"Kafka consumer initialized for servers: {self.bootstrap_servers}, group: {settings.KAFKA_GROUP_ID}")
            self._running = True # Set the running flag to true on successful start
            logger.info("Kafka client started", servers=self.bootstrap_servers)
        except Exception as e:
            logger.error("Failed to start Kafka client", error=str(e))
            raise
    
    def is_running(self) -> bool:
        """Check if the Kafka client is running."""
        return self._running and self.producer is not None and self.consumer is not None

    async def stop(self):
        """Stop Kafka producer and consumer"""
        try:
            self._running = False
            if self.producer:
                self.producer.flush()
            if self.consumer:
                self.consumer.close()
            logger.info("Kafka client stopped")
        except Exception as e:
            logger.error("Error stopping Kafka client", error=str(e))
    
    async def send_task_response(self, correlation_id: str, status: str, result: Dict[str, Any]):
        """Send a task response back to orchestrator"""
        try:
            if not self.producer:
                raise RuntimeError("Kafka producer not initialized")
                
            message = {
                "message_type": "TASK_RESPONSE",
                "correlation_id": correlation_id,
                "status": status,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            }
            logger.info(f"Sending Kafka task response: {message}", topic=settings.KAFKA_RESPONSE_TOPIC)
            self.producer.produce(
                settings.KAFKA_RESPONSE_TOPIC,
                value=json.dumps(message).encode('utf-8'),
                key=correlation_id.encode('utf-8')
            )
            self.producer.flush()
            logger.info(f"Task response sent to Kafka topic: {settings.KAFKA_RESPONSE_TOPIC}", correlation_id=correlation_id, status=status)
        except Exception as e:
            logger.error(f"Failed to send Kafka task response: {e}", topic=settings.KAFKA_RESPONSE_TOPIC)
            raise
    
    def subscribe_to_requests(self, handler: Callable):
        """Subscribe to task requests from orchestrator"""
        try:
            if not self.consumer:
                raise RuntimeError("Kafka consumer not initialized")
            self.consumer.subscribe([settings.KAFKA_REQUEST_TOPIC])
            self.message_handler = handler
            logger.info(f"Subscribed to Kafka topic: {settings.KAFKA_REQUEST_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to subscribe to Kafka topic: {settings.KAFKA_REQUEST_TOPIC}", error=str(e))
            raise
    
    async def start_consuming(self):
        """Start consuming messages from request topic"""
        self._running = True
        logger.info(f"Starting Kafka message consumption on topic: {settings.KAFKA_REQUEST_TOPIC}")
        try:
            while self._running:
                if not self.consumer:
                    logger.error("Kafka consumer not initialized during consumption loop")
                    break
                msg = self.consumer.poll(1.0)
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                if msg.error():
                    logger.error(f"Kafka message error: {msg.error()}", topic=settings.KAFKA_REQUEST_TOPIC)
                    continue
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    logger.info(f"Kafka message received: {value}", topic=settings.KAFKA_REQUEST_TOPIC)
                    if self.message_handler:
                        await self.message_handler(value)
                except Exception as e:
                    logger.error(f"Error handling Kafka message: {e}", topic=settings.KAFKA_REQUEST_TOPIC, message=msg.value())
        except Exception as e:
            logger.error(f"Error in Kafka consumption loop: {e}", topic=settings.KAFKA_REQUEST_TOPIC)
