# Backend AI Orchestrator - API Reference

## Authentication

Currently using simple user:db authentication. Future integration with Google Workspace planned.

## Base URL

```
http://localhost:8000
```

## Content Type

All requests and responses use `application/json` content type.

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Resource not found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

## Endpoints

### Health Check

Check service health and status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "backend-orchestrator",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**Status Values:**
- `healthy` - Service is operational
- `degraded` - Service running with limited functionality
- `unhealthy` - Service experiencing issues

---

### Chat Interaction

Process user messages and return AI-generated responses.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "user_id": "string",           // Required: Unique user identifier
  "message": "string",           // Required: User's message (max 2000 chars)
  "session_id": "string",        // Optional: Existing session ID (UUID format)
  "context": {                   // Optional: Additional context object
    "language": "en|id",         // Language preference
    "user_type": "patient|staff", // User type
    "department": "string",      // Hospital department
    "priority": "low|normal|high" // Message priority
  }
}
```

**Response:**
```json
{
  "response": "string",                    // AI-generated response
  "session_id": "string",                  // Session identifier (UUID)
  "intent": "string",                      // Classified intent
  "requires_human_handoff": boolean,       // Whether human intervention needed
  "suggested_actions": ["string"],         // Suggested follow-up actions
  "confidence_score": 0.95,               // Intent classification confidence (0-1)
  "processing_time_ms": 1250              // Response processing time
}
```

**Intent Classifications:**

| Intent | Description | Example Messages |
|--------|-------------|------------------|
| `appointment_booking` | Schedule new appointment | "I want to book an appointment", "Schedule me with a doctor" |
| `appointment_modify` | Change existing appointment | "Reschedule my appointment", "Cancel my booking" |
| `general_info` | General inquiries | "What are your hours?", "Where is the parking?" |
| `medical_emergency` | Urgent medical situations | "I have chest pain", "This is an emergency" |
| `pre_admission` | Pre-procedure information | "What should I prepare for surgery?" |
| `post_discharge` | Post-care instructions | "What medications should I take?" |

**Suggested Actions:**

| Action | Description |
|--------|-------------|
| `wait_for_agent_response` | Agent is processing request |
| `select_appointment_slot` | Choose from available appointments |
| `provide_patient_id` | Patient identification required |
| `contact_support` | Escalate to human support |
| `call_emergency_services` | Call emergency number immediately |
| `rephrase` | Rephrase the question |

**Example Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "patient_123",
    "message": "I want to book an appointment with a cardiologist",
    "context": {
      "language": "en",
      "user_type": "patient"
    }
  }'
```

**Example Response:**
```json
{
  "response": "I'll help you book a cardiology appointment. Let me check available slots for you.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "appointment_booking",
  "requires_human_handoff": false,
  "suggested_actions": ["wait_for_agent_response"],
  "confidence_score": 0.98,
  "processing_time_ms": 1150
}
```

---

### Session Management

#### Get Session

Retrieve session data and conversation history.

**Endpoint:** `GET /session/{session_id}`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Response:**
```json
{
  "session_id": "string",
  "user_id": "string",
  "created_at": "2024-01-15T10:00:00Z",
  "last_activity": "2024-01-15T10:30:00Z",
  "conversation_history": [
    {
      "timestamp": "2024-01-15T10:29:00Z",
      "role": "user|assistant|system",
      "content": "string",
      "metadata": {
        "intent": "string",
        "confidence": 0.95
      }
    }
  ],
  "context": {
    "language": "en",
    "current_intent": "appointment_booking",
    "workflow_state": "awaiting_confirmation"
  },
  "pending_tasks": [
    {
      "task_id": "string",
      "task_type": "appointment_booking",
      "status": "pending|processing|completed|failed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Error Responses:**
- `404` - Session not found
- `500` - Internal server error

#### Clear Session

Delete session and all associated data.

**Endpoint:** `DELETE /session/{session_id}`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Response:**
```json
{
  "message": "Session cleared successfully",
  "session_id": "string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Metrics

Get service metrics and statistics.

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  "active_sessions": 42,
  "total_messages_processed": 15420,
  "llm_provider": "gemini",
  "fallback_provider": "anthropic",
  "uptime_seconds": 86400,
  "intent_distribution": {
    "appointment_booking": 35,
    "general_info": 40,
    "appointment_modify": 15,
    "medical_emergency": 2,
    "pre_admission": 5,
    "post_discharge": 3
  },
  "response_times": {
    "avg_ms": 1250,
    "p95_ms": 2100,
    "p99_ms": 3500
  },
  "error_rates": {
    "llm_provider_errors": 0.02,
    "session_errors": 0.001,
    "agent_timeouts": 0.05
  }
}
```

## Rate Limiting

Default rate limits (configurable):
- 60 requests per minute per user
- 1000 requests per hour per user
- Burst limit: 10 requests

Rate limit headers included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

## WebSocket Support (Future)

Real-time chat interface will be available via WebSocket:

**Endpoint:** `ws://localhost:8000/ws/{session_id}`

**Message Format:**
```json
{
  "type": "message|typing|status",
  "data": {
    "message": "string",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## SDK Examples

### Python

```python
import requests

class ChatbotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def chat(self, user_id, message, context=None):
        payload = {
            "user_id": user_id,
            "message": message,
            "context": context or {}
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        response = requests.post(f"{self.base_url}/chat", json=payload)
        response.raise_for_status()
        
        data = response.json()
        self.session_id = data["session_id"]
        return data

# Usage
client = ChatbotClient()
response = client.chat(
    user_id="patient_123",
    message="I need to book an appointment",
    context={"language": "en"}
)
print(response["response"])
```

### JavaScript

```javascript
class ChatbotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }
    
    async chat(userId, message, context = {}) {
        const payload = {
            user_id: userId,
            message: message,
            context: context
        };
        
        if (this.sessionId) {
            payload.session_id = this.sessionId;
        }
        
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.sessionId = data.session_id;
        return data;
    }
}

// Usage
const client = new ChatbotClient();
const response = await client.chat(
    'patient_123',
    'I need to book an appointment',
    { language: 'en' }
);
console.log(response.response);
```

## Testing

### Health Check Test

```bash
curl -X GET "http://localhost:8000/health"
```

### Chat Test

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello, I need help"
  }'
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -T application/json -p chat_payload.json http://localhost:8000/chat

# Using wrk
wrk -t12 -c400 -d30s -s chat_script.lua http://localhost:8000/chat
```

## Changelog

### v1.0.0 (Current)
- Initial release
- Basic chat functionality
- Session management
- Intent classification
- LLM provider abstraction
- Kafka integration

### Planned Features
- WebSocket support for real-time chat
- Multi-language support
- Advanced analytics
- Custom intent training
- Voice message support
