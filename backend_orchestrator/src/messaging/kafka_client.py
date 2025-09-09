import asyncio
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError
import json
import uuid
from typing import Dict, Any, Optional, Callable
import structlog
from datetime import datetime
import time # Import the time module for numerical timestamps
#import sys
#import traceback

logger = structlog.get_logger()

class KafkaClient:
    """Kafka client for A2A communication protocol"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[Producer] = None
        self.consumers: Dict[str, Consumer] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {} 

    async def start(self):
        """Initialize Kafka producer"""
        loop = asyncio.get_running_loop()
        try:
            self.producer = await loop.run_in_executor(
                None, 
                lambda: Producer({'bootstrap.servers': self.bootstrap_servers})
            )
            logger.info("Kafka producer started", servers=self.bootstrap_servers)
        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e), exc_info=True)
            self.producer = None 
            raise 
    
    async def stop(self):
        """Stop Kafka producer and consumers"""
        loop = asyncio.get_running_loop()
        try:
            if self.producer:
                await loop.run_in_executor(None, self.producer.flush)
                self.producer = None 
                logger.info("Kafka producer flushed.")

            for topic, task in self.consumer_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task 
                    except asyncio.CancelledError:
                        pass
                logger.info(f"Kafka consumer task for topic {topic} cancelled.")
            self.consumer_tasks.clear()

            for consumer in self.consumers.values():
                await loop.run_in_executor(None, consumer.close)
            self.consumers.clear()
            self.message_handlers.clear()
            
            logger.info("Kafka client stopped")
        except Exception as e:
            logger.error("Error stopping Kafka client", error=str(e), exc_info=True)
    
    async def send_task_request(self, agent_topic: str, task_type: str, payload: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        """Send a task request to an agent"""
        loop = asyncio.get_running_loop()
        try:
            if not self.producer:
                logger.error(f"Kafka producer is not initialized for topic {agent_topic}")
                raise RuntimeError("Kafka producer is not initialized.")

            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            message = {
                "message_type": "TASK_REQUEST",
                "correlation_id": correlation_id,
                "task_type": task_type,
                "payload": payload,
                "timestamp": time.time() # <-- FIX: Use numerical timestamp for the agent's Pydantic model
            }
            
            value = json.dumps(message).encode('utf-8')
            key = correlation_id.encode('utf-8')

            await loop.run_in_executor(
                None, 
                lambda: self.producer.produce(agent_topic, value=value, key=key)
            )
            await loop.run_in_executor(None, self.producer.flush, 0.5) 

            logger.info("Task request sent", topic=agent_topic, correlation_id=correlation_id, task_type=task_type)
            return correlation_id
        except Exception as e:
            logger.error("Failed to send task request", topic=agent_topic, error=str(e), exc_info=True)
            raise 
    
    async def send_task_response(self, response_topic: str, correlation_id: str, status: str, result: Dict[str, Any]):
        """Send a task response back to orchestrator"""
        loop = asyncio.get_running_loop()
        try:
            if not self.producer:
                logger.error(f"Kafka producer is not initialized for topic {response_topic}")
                raise RuntimeError("Kafka producer is not initialized.")

            message = {
                "message_type": "TASK_RESPONSE",
                "correlation_id": correlation_id,
                "status": status,
                "result": result,
                "timestamp": time.time() # <-- FIX: Use numerical timestamp
            }
            
            value = json.dumps(message).encode('utf-8')
            key = correlation_id.encode('utf-8')

            await loop.run_in_executor(
                None,
                lambda: self.producer.produce(response_topic, value=value, key=key)
            )
            await loop.run_in_executor(None, self.producer.flush, 0.5)

            logger.info("Task response sent", topic=response_topic, correlation_id=correlation_id, status=status)
        except Exception as e:
            logger.error("Failed to send task response", topic=response_topic, error=str(e), exc_info=True)
            raise
    
    def subscribe_to_responses(self, topic: str, handler: Callable):
        """Subscribe to task responses from agents"""
        if topic in self.consumers:
            logger.warning(f"Already subscribed to {topic}. Skipping.")
            return

        loop = asyncio.get_running_loop()
        try:
            consumer = Consumer({
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': 'orchestrator-group',
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False 
            })
            
            loop.run_in_executor(None, consumer.subscribe, [topic])
            
            self.consumers[topic] = consumer
            self.message_handlers[topic] = handler
            self.consumer_tasks[topic] = asyncio.create_task(self._consume_messages(topic))
            logger.info("Subscribed to topic", topic=topic)
        except Exception as e:
            logger.error("Failed to subscribe to topic", topic=topic, error=str(e), exc_info=True)
            raise
    
    async def _consume_messages(self, topic: str):
        """Background task to consume messages from a topic"""
        consumer = self.consumers[topic]
        handler = self.message_handlers[topic]
        loop = asyncio.get_running_loop() 

        try:
            while True:
                msg = await loop.run_in_executor(None, consumer.poll, 1.0)
                
                if msg is None:
                    await asyncio.sleep(0.1) 
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition reached for {msg.topic()} [{msg.partition()}]")
                    else:
                        logger.error("Error consuming messages", topic=topic, error=str(msg.error()))
                    await asyncio.sleep(0.1) 
                    continue

                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    await handler(value) 
                    # FIX IS HERE: Explicitly pass 'message=msg' to consumer.commit
                    await loop.run_in_executor(None, lambda: consumer.commit(message=msg)) 
                except Exception as e:
                    logger.error("Error handling message or committing offset", topic=topic, error=str(e), message=msg.value(), exc_info=True)
                    # Capture traceback manually
                    #exc_type, exc_value, exc_traceback = sys.exc_info()
                    #formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

                    # Remove exc_info=True and pass traceback as a regular field
                    # Also, explicitly pass the Kafka message details, not the Message object itself
                    # logger.error(
                    #     "Error handling message or committing offset",
                    #     topic=topic,
                    #     error=str(e),
                    #     raw_kafka_message_value=msg.value().decode('utf-8', errors='ignore'), # Original bytes decoded
                    #     kafka_message_topic=msg.topic(),
                    #     kafka_message_partition=msg.partition(),
                    #     kafka_message_offset=msg.offset(),
                    #     stack_trace=formatted_traceback, # Pass the formatted traceback
                    #     # exc_info=True # <-- REMOVE THIS LINE
                    # )
        except asyncio.CancelledError:
            logger.info(f"Consumer task for {topic} cancelled.")
        except Exception as e:
            logger.error(f"Critical error in Kafka consumer for {topic}: {e}", exc_info=True)
        finally:
            pass