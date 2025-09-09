# Intent Category and Agent Integration Guide

## Overview

This guide provides a comprehensive walkthrough for adding new intent categories and connecting them to new agents in the healthcare chatbot system. It covers both Kafka-based messaging agents and REST API agents, using the RAG service integration as a practical example.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding New Intent Categories](#adding-new-intent-categories)
3. [Creating Kafka-Based Agents](#creating-kafka-based-agents)
4. [Creating REST API Agents](#creating-rest-api-agents)
5. [Integration Patterns](#integration-patterns)
6. [Testing and Validation](#testing-and-validation)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

The chatbot system follows a microservices architecture with the Backend Orchestrator as the central hub:

```
┌─────────────────┐    Intent Classification    ┌─────────────────┐
│ User Input      │──────────────────────────►│ Backend         │
│ (Telegram/etc)  │                            │ Orchestrator    │
└─────────────────┘                            └─────────────────┘
                                                        │
                                                        │ Route by Intent
                                                        ▼
                                               ┌─────────────────┐
                                               │ Intent Router   │
                                               └─────────────────┘
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                            │ Kafka Agent │    │ REST Agent  │    │ Direct LLM  │
                            │ (RAG)       │    │ (Future)    │    │ (Fallback)  │
                            └─────────────┘    └─────────────┘    └─────────────┘
```

### Communication Patterns

1. **Kafka Messaging**: Asynchronous agent-to-agent communication
2. **REST API**: Synchronous HTTP-based communication
3. **Direct LLM**: Fallback for simple queries

## Adding New Intent Categories

### Step 1: Define the Intent

First, identify the new intent category and its characteristics:

```python
# Example: Adding "prescription_refill" intent
INTENT_CHARACTERISTICS = {
    "prescription_refill": {
        "keywords": ["refill", "prescription", "medication", "pharmacy"],
        "patterns": ["I need to refill", "prescription refill", "medication refill"],
        "agent_type": "kafka",  # or "rest" or "direct"
        "priority": "medium",
        "requires_auth": True
    }
}
```

### Step 2: Update Intent Classification

Modify the conversation engine's intent classification logic:

```python
# backend_orchestrator/src/workflow/conversation_engine.py

async def _classify_intent(self, message: str, session_data: Dict[str, Any]) -> str:
    """Classify user intent from message"""
    
    # Add new intent classification logic
    if any(keyword in message.lower() for keyword in ["refill", "prescription", "medication"]):
        return "prescription_refill"
    
    # Existing classification logic...
    if any(keyword in message.lower() for keyword in ["appointment", "schedule", "book"]):
        return "appointment_request"
    
    # Continue with existing patterns...
```

### Step 3: Add Intent Routing

Update the message routing function:

```python
# backend_orchestrator/src/workflow/conversation_engine.py

async def _route_message(self, session_id: str, message: str, intent: str, 
                        session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route message based on classified intent"""
    
    if intent == "prescription_refill":
        return await self._handle_prescription_refill(session_id, message, session_data)
    elif intent == "appointment_request":
        return await self._handle_appointment_request(session_id, message, session_data)
    elif intent == "general_info":
        return await self._handle_general_info(session_id, message, session_data)
    # Add other intents...
    else:
        return await self._handle_general_info(session_id, message, session_data)
```

## Creating Kafka-Based Agents

### Example: RAG Service Integration

The RAG service demonstrates the complete Kafka integration pattern:

#### Step 1: Configure Kafka Topics

Update orchestration rules:

```yaml
# backend_orchestrator/config/orchestration_rules.yaml
agent_topics:
  prescription-refill-requests: "prescription_refill_agent"
  prescription-refill-responses: "prescription_refill_agent"
  general-info-requests: "rag_service"
  general-info-responses: "rag_service"
```

#### Step 2: Create Agent Service Structure

```
agents/prescription-refill-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app with Kafka integration
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Configuration settings
│   ├── messaging/
│   │   ├── __init__.py
│   │   └── kafka_client.py       # Kafka producer/consumer
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── kafka_handler.py      # Message processing logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── kafka_messages.py     # Pydantic models for messages
│   │   └── domain_models.py      # Business logic models
│   └── api/
│       └── v1/
│           └── endpoints.py      # REST endpoints (optional)
├── docs/
│   ├── INTEGRATION_GUIDE.md
│   └── API_REFERENCE.md
├── tests/
├── pyproject.toml
├── .env.example
├── .env
└── README.md
```

#### Step 3: Implement Kafka Client

```python
# agents/prescription-refill-agent/app/messaging/kafka_client.py

import asyncio
from confluent_kafka import Producer, Consumer
import json
from typing import Dict, Any, Optional, Callable
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class KafkaClient:
    """Kafka client for prescription refill agent"""
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self.consumer = None
        self.message_handler = None
        self.running = False
        
    async def start(self):
        """Initialize Kafka producer and consumer"""
        try:
            self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
            
            self.consumer = Consumer({
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': settings.KAFKA_GROUP_ID,
                'auto.offset.reset': 'earliest'
            })
            
            logger.info("Kafka client started", servers=self.bootstrap_servers)
        except Exception as e:
            logger.error("Failed to start Kafka client", error=str(e))
            raise
    
    async def send_task_response(self, correlation_id: str, status: str, result: Dict[str, Any]):
        """Send task response back to orchestrator"""
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
            self.producer.produce(
                settings.KAFKA_RESPONSE_TOPIC,
                value=json.dumps(message).encode('utf-8'),
                key=correlation_id.encode('utf-8')
            )
            self.producer.flush()
            logger.info("Task response sent", 
                       topic=settings.KAFKA_RESPONSE_TOPIC, 
                       correlation_id=correlation_id)
        except Exception as e:
            logger.error("Failed to send task response", error=str(e))
            raise
```

#### Step 4: Implement Message Handler

```python
# agents/prescription-refill-agent/app/handlers/kafka_handler.py

import asyncio
from typing import Dict, Any
import structlog
from app.models.kafka_messages import TaskRequest, TaskResponse

logger = structlog.get_logger()

class KafkaMessageHandler:
    """Handler for processing Kafka messages"""
    
    def __init__(self, kafka_client):
        self.kafka_client = kafka_client
        
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming Kafka message"""
        try:
            task_request = TaskRequest(**message)
            logger.info("Processing task request", 
                       correlation_id=task_request.correlation_id,
                       task_type=task_request.task_type)
            
            if task_request.task_type == "prescription_refill":
                await self._handle_prescription_refill_request(task_request)
            else:
                await self._send_error_response(
                    task_request.correlation_id,
                    f"Unsupported task type: {task_request.task_type}"
                )
                
        except Exception as e:
            logger.error("Error handling Kafka message", error=str(e))
            correlation_id = message.get("correlation_id", "unknown")
            await self._send_error_response(correlation_id, str(e))
    
    async def _handle_prescription_refill_request(self, task_request: TaskRequest):
        """Handle prescription refill request"""
        try:
            # Extract payload
            payload = task_request.payload
            patient_id = payload.get("patient_id")
            medication_name = payload.get("medication_name")
            
            # Process refill request (business logic here)
            result = await self._process_refill(patient_id, medication_name)
            
            await self._send_success_response(task_request.correlation_id, result)
            
        except Exception as e:
            logger.error("Error processing prescription refill", 
                        correlation_id=task_request.correlation_id, 
                        error=str(e))
            await self._send_error_response(
                task_request.correlation_id,
                "Unable to process prescription refill request"
            )
```

#### Step 5: Add Backend Orchestrator Handler

```python
# backend_orchestrator/src/workflow/conversation_engine.py

async def _handle_prescription_refill(self, session_id: str, message: str, 
                                    session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle prescription refill requests via Kafka"""
    try:
        correlation_id = await self.kafka_client.send_task_request(
            agent_topic="prescription-refill-requests",
            task_type="prescription_refill",
            payload={
                "message": message,
                "session_id": session_id,
                "user_context": session_data.get("context", {}),
                "patient_id": session_data.get("patient_id"),
                "conversation_history": session_data.get("conversation_history", [])[-3:]
            }
        )
        
        return {
            "response": "I'm processing your prescription refill request. Please wait a moment.",
            "requires_human_handoff": False,
            "suggested_actions": ["wait_for_agent_response"],
            "correlation_id": correlation_id
        }
        
    except Exception as e:
        logger.error("Error handling prescription refill via agent", error=str(e))
        return await self._handle_prescription_refill_fallback(session_id, message, session_data)
```

## Creating REST API Agents

### Example: External Pharmacy Integration

For agents that need to integrate with external REST APIs:

#### Step 1: Create REST Client

```python
# agents/pharmacy-integration-agent/app/clients/pharmacy_client.py

import httpx
import asyncio
from typing import Dict, Any, Optional
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class PharmacyAPIClient:
    """Client for external pharmacy API integration"""
    
    def __init__(self):
        self.base_url = settings.PHARMACY_API_BASE_URL
        self.api_key = settings.PHARMACY_API_KEY
        self.timeout = httpx.Timeout(30.0)
        
    async def check_prescription_status(self, prescription_id: str) -> Dict[str, Any]:
        """Check prescription status via external API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/prescriptions/{prescription_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error("Pharmacy API request failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error calling pharmacy API", error=str(e))
            raise
```

#### Step 2: Implement REST Handler

```python
# agents/pharmacy-integration-agent/app/handlers/rest_handler.py

from typing import Dict, Any
import structlog
from app.clients.pharmacy_client import PharmacyAPIClient

logger = structlog.get_logger()

class RESTHandler:
    """Handler for REST API operations"""
    
    def __init__(self):
        self.pharmacy_client = PharmacyAPIClient()
        
    async def handle_prescription_check(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prescription status check"""
        try:
            prescription_id = request_data.get("prescription_id")
            if not prescription_id:
                return {
                    "status": "error",
                    "message": "Prescription ID is required"
                }
            
            # Call external pharmacy API
            pharmacy_response = await self.pharmacy_client.check_prescription_status(prescription_id)
            
            # Transform response for our system
            result = {
                "status": "success",
                "prescription_status": pharmacy_response.get("status"),
                "ready_for_pickup": pharmacy_response.get("ready", False),
                "pharmacy_location": pharmacy_response.get("location"),
                "estimated_ready_time": pharmacy_response.get("estimated_time")
            }
            
            return result
            
        except Exception as e:
            logger.error("Error handling prescription check", error=str(e))
            return {
                "status": "error",
                "message": "Unable to check prescription status"
            }
```

#### Step 3: Backend Orchestrator Integration

```python
# backend_orchestrator/src/workflow/conversation_engine.py

async def _handle_prescription_status(self, session_id: str, message: str, 
                                    session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle prescription status queries via REST API"""
    try:
        # Extract prescription ID from message or session data
        prescription_id = self._extract_prescription_id(message, session_data)
        
        if not prescription_id:
            return {
                "response": "I need your prescription ID to check the status. Can you provide it?",
                "requires_human_handoff": False,
                "suggested_actions": ["request_prescription_id"]
            }
        
        # Call REST API agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PHARMACY_AGENT_URL}/check-prescription",
                json={
                    "prescription_id": prescription_id,
                    "session_id": session_id
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        if result["status"] == "success":
            if result["ready_for_pickup"]:
                response_text = f"Your prescription is ready for pickup at {result['pharmacy_location']}!"
            else:
                response_text = f"Your prescription is being prepared. Estimated ready time: {result['estimated_ready_time']}"
        else:
            response_text = "I couldn't check your prescription status right now. Please try again later."
        
        return {
            "response": response_text,
            "requires_human_handoff": False,
            "suggested_actions": []
        }
        
    except Exception as e:
        logger.error("Error handling prescription status via REST", error=str(e))
        return {
            "response": "I'm having trouble checking prescription status. Please contact the pharmacy directly.",
            "requires_human_handoff": True,
            "suggested_actions": ["contact_pharmacy"]
        }
```

## Integration Patterns

### Message Flow Patterns

#### 1. Kafka Request-Response Pattern

```
Backend Orchestrator → Kafka Topic (Request) → Agent → Kafka Topic (Response) → Backend Orchestrator
```

**Message Structure:**
```json
{
  "message_type": "TASK_REQUEST",
  "correlation_id": "uuid",
  "task_type": "intent_name",
  "payload": { "user_data": "..." },
  "timestamp": 1234567890.0
}
```

#### 2. REST Synchronous Pattern

```
Backend Orchestrator → HTTP Request → Agent → HTTP Response → Backend Orchestrator
```

**Request Structure:**
```json
{
  "session_id": "session-123",
  "message": "user input",
  "context": { "user_data": "..." }
}
```

#### 3. Hybrid Pattern

Some agents may support both Kafka and REST interfaces:

```python
# Agent supports both interfaces
app.include_router(rest_endpoints.router)  # REST API
kafka_task = asyncio.create_task(kafka_client.start_consuming())  # Kafka
```

### Error Handling Patterns

#### 1. Graceful Degradation

```python
async def _handle_intent_with_fallback(self, session_id: str, message: str, 
                                     session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle intent with fallback to direct LLM"""
    try:
        # Try agent first
        return await self._handle_via_agent(session_id, message, session_data)
    except Exception as e:
        logger.error("Agent failed, using fallback", error=str(e))
        return await self._handle_via_direct_llm(session_id, message, session_data)
```

#### 2. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

### Configuration Management

#### Environment Variables Pattern

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "prescription-refill-agent"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka.data.svc.cluster.local:9092"
    KAFKA_REQUEST_TOPIC: str = "prescription-refill-requests"
    KAFKA_RESPONSE_TOPIC: str = "prescription-refill-responses"
    KAFKA_GROUP_ID: str = "prescription-refill-group"
    
    # External API Configuration
    PHARMACY_API_BASE_URL: str
    PHARMACY_API_KEY: str
    
    # LLM Configuration (if needed)
    LLM_MODEL_NAME: str = "gemini-2.5-flash-preview-04-17"
    GOOGLE_API_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Testing and Validation

### Unit Testing

```python
# tests/test_kafka_handler.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.handlers.kafka_handler import KafkaMessageHandler

@pytest.fixture
def kafka_client_mock():
    return AsyncMock()

@pytest.fixture
def handler(kafka_client_mock):
    return KafkaMessageHandler(kafka_client_mock)

@pytest.mark.asyncio
async def test_handle_prescription_refill_success(handler, kafka_client_mock):
    message = {
        "message_type": "TASK_REQUEST",
        "correlation_id": "test-123",
        "task_type": "prescription_refill",
        "payload": {
            "patient_id": "patient-456",
            "medication_name": "Aspirin"
        },
        "timestamp": 1234567890.0
    }
    
    await handler.handle_message(message)
    
    kafka_client_mock.send_task_response.assert_called_once()
    args = kafka_client_mock.send_task_response.call_args
    assert args[1]["correlation_id"] == "test-123"
    assert args[1]["status"] == "SUCCESS"
```

### Integration Testing

```python
# tests/integration/test_end_to_end.py
import pytest
import asyncio
from backend_orchestrator.src.workflow.conversation_engine import ConversationEngine

@pytest.mark.asyncio
async def test_prescription_refill_flow():
    engine = ConversationEngine()
    
    # Test intent classification
    intent = await engine._classify_intent("I need to refill my prescription", {})
    assert intent == "prescription_refill"
    
    # Test message routing
    response = await engine.process_message(
        session_id="test-session",
        message="I need to refill my Aspirin prescription",
        context={"patient_id": "patient-123"}
    )
    
    assert "processing your prescription refill" in response["response"].lower()
    assert response["requires_human_handoff"] is False
```

### Manual Testing

```bash
# Test Kafka integration
kafka-console-producer --bootstrap-server kafka.data.svc.cluster.local:9092 --topic prescription-refill-requests
# Send test message:
{"message_type":"TASK_REQUEST","correlation_id":"test-123","task_type":"prescription_refill","payload":{"patient_id":"123","medication":"Aspirin"},"timestamp":1234567890.0}

# Monitor responses
kafka-console-consumer --bootstrap-server kafka.data.svc.cluster.local:9092 --topic prescription-refill-responses --from-beginning

# Test REST API
curl -X POST "http://localhost:8001/check-prescription" \
  -H "Content-Type: application/json" \
  -d '{"prescription_id": "RX123456", "session_id": "test-session"}'
```

## Best Practices

### 1. Service Design

- **Single Responsibility**: Each agent handles one specific domain
- **Stateless Design**: Agents should not maintain session state
- **Idempotent Operations**: Handle duplicate messages gracefully
- **Graceful Degradation**: Always provide fallback mechanisms

### 2. Message Design

- **Correlation IDs**: Always include correlation IDs for request tracking
- **Structured Payloads**: Use Pydantic models for message validation
- **Versioning**: Include message version for future compatibility
- **Timestamps**: Include timestamps for debugging and monitoring

### 3. Error Handling

- **Structured Errors**: Use consistent error response formats
- **Logging**: Include correlation IDs in all log messages
- **Circuit Breakers**: Implement circuit breakers for external dependencies
- **Timeouts**: Set appropriate timeouts for all operations

### 4. Configuration

- **Environment Variables**: Use environment variables for all configuration
- **Validation**: Validate configuration at startup
- **Secrets Management**: Never commit secrets to version control
- **Documentation**: Document all configuration options

### 5. Testing

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end message flows
- **Contract Tests**: Verify message format compatibility
- **Load Tests**: Test performance under expected load

### 6. Monitoring

- **Health Checks**: Implement comprehensive health checks
- **Metrics**: Collect performance and business metrics
- **Alerting**: Set up alerts for critical failures
- **Tracing**: Use correlation IDs for distributed tracing

## Troubleshooting

### Common Issues

#### 1. Kafka Connection Issues

**Symptoms:**
- Agent fails to start
- Messages not being consumed
- Connection timeouts

**Solutions:**
```bash
# Check Kafka broker status
kafka-broker-api-versions --bootstrap-server kafka.data.svc.cluster.local:9092

# Verify topic exists
kafka-topics --bootstrap-server kafka.data.svc.cluster.local:9092 --list

# Check consumer group
kafka-consumer-groups --bootstrap-server kafka.data.svc.cluster.local:9092 --describe --group your-group-id
```

#### 2. Message Format Errors

**Symptoms:**
- Pydantic validation errors
- Messages being rejected
- Unexpected response formats

**Solutions:**
```python
# Add message validation logging
try:
    task_request = TaskRequest(**message)
except ValidationError as e:
    logger.error("Message validation failed", error=str(e), message=message)
    raise
```

#### 3. Agent Timeout Issues

**Symptoms:**
- Requests timing out
- No responses received
- Backend orchestrator fallback triggered

**Solutions:**
```python
# Increase timeouts
KAFKA_CONSUMER_TIMEOUT = 30.0
HTTP_CLIENT_TIMEOUT = 60.0

# Add timeout monitoring
start_time = time.time()
# ... process request ...
processing_time = time.time() - start_time
logger.info("Request processed", processing_time=processing_time)
```

#### 4. Intent Classification Issues

**Symptoms:**
- Wrong intent detected
- Messages routed to wrong agent
- Fallback triggered unnecessarily

**Solutions:**
```python
# Add intent classification logging
intent = await self._classify_intent(message, session_data)
logger.info("Intent classified", message=message, intent=intent, confidence=confidence)

# Improve classification logic
def _classify_intent_with_confidence(self, message: str) -> Tuple[str, float]:
    # Return both intent and confidence score
    # Use confidence threshold for routing decisions
```

### Debugging Tools

#### 1. Message Tracing

```python
# Add correlation ID to all logs
logger = structlog.get_logger().bind(correlation_id=correlation_id)

# Trace message flow
logger.info("Message received", topic=topic, message_type=message_type)
logger.info("Processing started", task_type=task_type)
logger.info("Processing completed", status=status, processing_time=duration)
```

#### 2. Health Monitoring

```python
# Comprehensive health check
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "kafka": await check_kafka_connection(),
        "external_api": await check_external_api(),
        "llm_provider": await check_llm_provider()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

#### 3. Performance Monitoring

```python
# Add performance metrics
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info("Function completed", 
                       function=func.__name__, 
                       duration=duration, 
                       status="success")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Function failed", 
                        function=func.__name__, 
                        duration=duration, 
                        status="error", 
                        error=str(e))
            raise
    return wrapper
```

## Conclusion

This guide provides a comprehensive framework for adding new intent categories and connecting them to agents in the healthcare chatbot system. The RAG service integration serves as a practical example of implementing both Kafka messaging and REST API patterns.

Key takeaways:
1. Follow the established patterns for consistency
2. Implement comprehensive error handling and fallbacks
3. Use structured logging with correlation IDs
4. Create thorough documentation and tests
5. Monitor performance and health metrics

For specific implementation questions or issues not covered in this guide, refer to the existing agent implementations or consult the development team.
