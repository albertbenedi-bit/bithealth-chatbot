import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from confluent_kafka import Producer, Consumer, KafkaException
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class KafkaClient:
    """
    Kafka client for Agent-to-Agent (A2A) communication using confluent-kafka.
    Mirrors the structure of other agents in the system.
    """
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self.consumer = None
        self.message_handler = None
        self._running = False

    async def start(self):
        """Initialize Kafka producer and consumer."""
        try:
            logger.debug("kafka_client_starting",
                        bootstrap_servers=self.bootstrap_servers)
            
            producer_conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'message.max.bytes': 5000000  # 5MB max message size
            }
            self.producer = Producer(producer_conf)
            
            consumer_conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': settings.KAFKA_GROUP_ID,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False,  # We'll commit manually after processing
                'session.timeout.ms': 45000,  # 45 seconds session timeout
                'max.poll.interval.ms': 300000  # 5 minutes max between polls
            }
            self.consumer = Consumer(consumer_conf)
            logger.debug(f"Kafka consumer initialized with group.id: {settings.KAFKA_GROUP_ID}")
            
            self._running = True
            logger.info("Kafka client started successfully", 
                       servers=self.bootstrap_servers,
                       group_id=settings.KAFKA_GROUP_ID,
                       request_topic=settings.KAFKA_REQUEST_TOPIC)
        except Exception as e:
            logger.error("Failed to start Kafka client", error=str(e), exc_info=True)
            raise

    def is_running(self) -> bool:
        return self._running and self.producer is not None and self.consumer is not None

    async def stop(self):
        """Stop Kafka producer and consumer."""
        self._running = False
        if self.producer:
            self.producer.flush()
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka client stopped.")

    async def send_task_response(self, correlation_id: str, status: str, result: Dict[str, Any]):
        """Send a task response back to the orchestrator."""
        if not self.producer:
            logger.error("no_producer")
            return
            
        try:
            # Create response with timestamp
            message = {
                "message_type": "TASK_RESPONSE",
                "correlation_id": correlation_id,
                "status": status,
                "result": result,
                "timestamp": datetime.now().timestamp()
            }
            
            # Send it
            self.producer.produce(
                settings.KAFKA_RESPONSE_TOPIC,
                value=json.dumps(message).encode('utf-8'),
                key=correlation_id.encode('utf-8')
            )
            self.producer.flush()
            
            logger.info("response_sent",
                       correlation_id=correlation_id)
                       
        except Exception as e:
            logger.error("send_failed",
                        error=str(e),
                        correlation_id=correlation_id)

    def subscribe_to_requests(self, handler: Callable):
        """Subscribe to task requests from the orchestrator."""
        if not self.consumer:
            logger.error("kafka_subscription_failed", reason="consumer_not_initialized")
            raise RuntimeError("Kafka consumer not initialized")
        
        try:
            self.message_handler = handler
            self.consumer.subscribe(
                [settings.KAFKA_REQUEST_TOPIC],
                on_assign=lambda consumer, partitions: logger.info(
                    "kafka_partitions_assigned",
                    partitions=str(partitions)
                ),
                on_revoke=lambda consumer, partitions: logger.info(
                    "kafka_partitions_revoked",
                    partitions=str(partitions)
                )
            )
            logger.info("kafka_subscription_successful",
                       topic=settings.KAFKA_REQUEST_TOPIC,
                       consumer_group=settings.KAFKA_GROUP_ID)
        except Exception as e:
            logger.error("kafka_subscription_failed",
                        topic=settings.KAFKA_REQUEST_TOPIC,
                        error=str(e))
            raise

    async def start_consuming(self):
        """Start consuming messages from the request topic."""
        if not self.consumer or not self.message_handler:
            logger.error("kafka_consumption_failed", 
                        reason="consumer_or_handler_not_initialized")
            return
        
        logger.info("kafka_consumer_starting",
                   topic=settings.KAFKA_REQUEST_TOPIC)
        
        while self._running:
            try:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue

                if msg.error():
                    logger.error("kafka_message_error",
                               error=str(msg.error()))
                    continue

                value = json.loads(msg.value().decode('utf-8'))
                correlation_id = value.get("correlation_id", "unknown")
                
                logger.info("kafka_message_processing",
                          topic=settings.KAFKA_REQUEST_TOPIC,
                          correlation_id=correlation_id,
                          task_type=value.get("task_type"))

                if self.message_handler:
                    await self.message_handler(value)
                    # Commit offset only after successful processing
                    self.consumer.commit(msg)
                    logger.info("kafka_message_processed",
                              correlation_id=correlation_id)
                else:
                    logger.warning("kafka_no_handler",
                                 correlation_id=correlation_id)
            except json.JSONDecodeError as e:
                logger.error("kafka_message_decode_failed",
                           error=str(e),
                           raw_message=msg.value().decode('utf-8', errors='ignore') if msg else "")
            except Exception as e:
                logger.error("kafka_message_processing_failed",
                           error=str(e),
                           error_type=type(e).__name__,
                           correlation_id=value.get("correlation_id", "unknown") if 'value' in locals() else "unknown")

