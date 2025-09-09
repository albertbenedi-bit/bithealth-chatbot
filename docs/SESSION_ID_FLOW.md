# WebSocket Session ID Flow Documentation

## Overview

This document describes the complete session_id flow implementation that enables consistent WebSocket message routing from frontend through the backend orchestrator, Kafka messaging system, RAG service, and back to the correct WebSocket connection.

## Architecture Flow

```
Frontend WebSocket → Backend Orchestrator → Kafka → RAG Service → Kafka Response → Backend Orchestrator → WebSocket Delivery
```

## Message Flow Details

### 1. Frontend to Backend Orchestrator

**WebSocket Connection:**
- Frontend establishes WebSocket connection: `ws://localhost:8000/ws/{session_id}`
- Session ID is embedded in the WebSocket URL path
- WebSocketManager maintains active connections indexed by session_id

**Chat Request:**
```json
{
  "user_id": "user-123",
  "message": "What are your opening hours?",
  "session_id": "session-abc-123",
  "context": {}
}
```

### 2. Backend Orchestrator to Kafka

**TaskRequest Message Format:**
```json
{
  "message_type": "task_request",
  "correlation_id": "corr-123-456",
  "task_type": "general_info",
  "payload": {
    "message": "What are your opening hours?",
    "session_id": "session-abc-123",
    "user_context": {},
    "conversation_history": []
  },
  "timestamp": "2025-07-20T16:50:45Z"
}
```

**Key Components:**
- `conversation_engine.py` extracts session_id from HTTP request
- Session_id is included in the TaskRequest payload
- Message is sent to appropriate Kafka topic based on intent classification

### 3. RAG Service Processing

**Session ID Extraction:**
```python
# In kafka_handler.py
payload = GeneralInfoPayload(**task_request.payload)
session_id = payload.session_id  # Extract from payload
```

**Response Result Format:**
```json
{
  "response": "Our opening hours are Monday-Friday 9AM-5PM",
  "sources": ["doc1.pdf", "doc2.pdf"],
  "requires_human_handoff": false,
  "suggested_actions": [],
  "session_id": "session-abc-123"  // ← Added in implementation
}
```

### 4. Kafka Response to Backend Orchestrator

**TaskResponse Message Format:**
```json
{
  "correlation_id": "corr-123-456",
  "status": "SUCCESS",
  "result": {
    "response": "Our opening hours are Monday-Friday 9AM-5PM",
    "sources": ["doc1.pdf", "doc2.pdf"],
    "requires_human_handoff": false,
    "suggested_actions": [],
    "session_id": "session-abc-123"
  }
}
```

### 5. Backend Orchestrator to WebSocket

**Session ID Mapping:**
```python
# In conversation_engine.py
session_id = result.get("session_id")  # Extract from result
if session_id:
    # Send to correct WebSocket connection
    await self.websocket_manager.send_message_to_session(
        session_id, 
        websocket_message
    )
```

**WebSocket Message Format:**
```json
{
  "type": "agent_response",
  "data": {
    "session_id": "session-abc-123",
    "response": "Our opening hours are Monday-Friday 9AM-5PM",
    "requires_human_handoff": false,
    "suggested_actions": []
  }
}
```

## Implementation Changes

### Modified Files

#### 1. `agents/rag-service-2/app/handlers/kafka_handler.py`

**Changes Made:**
- Extract `session_id` from TaskRequest payload
- Include `session_id` in all result dictionaries (success, error, no-docs cases)
- Update `_send_error_response` method to accept optional session_id parameter
- Preserve session_id in error handling when possible

**Key Code Changes:**
```python
# Extract session_id from payload
payload = GeneralInfoPayload(**task_request.payload)
session_id = payload.session_id

# Include in success result
result = {
    "response": answer_text,
    "sources": unique_sources,
    "requires_human_handoff": False,
    "suggested_actions": [],
    "session_id": session_id  # ← Added
}

# Include in error result
async def _send_error_response(self, correlation_id: str, error_message: str, session_id: Optional[str] = None):
    result = {
        "response": "I'm sorry, I'm having trouble processing your request right now.",
        "sources": [],
        "requires_human_handoff": True,
        "suggested_actions": ["try_again_later"],
        "error": error_message,
        "session_id": session_id  # ← Added
    }
```

### Existing Infrastructure (No Changes Required)

#### 1. `backend_orchestrator/src/workflow/conversation_engine.py`
- Already correctly extracts session_id: `session_id = result.get("session_id")`
- Already handles WebSocket message delivery based on session_id

#### 2. `backend_orchestrator/src/websocket/websocket_manager.py`
- Already maintains WebSocket connections indexed by session_id
- Already provides `send_message_to_session()` method

#### 3. `agents/rag-service-2/app/models/kafka_messages.py`
- TaskRequest already includes session_id in payload
- No structural changes needed

## Error Handling

### Session ID Preservation

**Success Cases:**
- Session_id extracted from payload and included in result

**Error Cases:**
- Session_id preserved when payload extraction succeeds
- Session_id set to None when payload extraction fails
- Error responses still include session_id field for consistency

**Example Error Response:**
```json
{
  "response": "I'm sorry, I'm having trouble processing your request right now.",
  "sources": [],
  "requires_human_handoff": true,
  "suggested_actions": ["try_again_later"],
  "error": "An internal error occurred while processing your request.",
  "session_id": "session-abc-123"  // ← Preserved when possible
}
```

## Testing Strategy

### Manual Testing Steps

1. **Single Session Test:**
   - Connect WebSocket with session_id
   - Send chat message via HTTP API
   - Verify WebSocket receives response with matching session_id

2. **Multiple Concurrent Sessions:**
   - Connect multiple WebSocket sessions with different session_ids
   - Send messages from each session
   - Verify each session receives only its own responses

3. **Error Scenarios:**
   - Test with invalid payloads
   - Verify session_id preserved in error responses
   - Test WebSocket reconnection scenarios

### Automated Testing

**Test Script:** `test_session_id_flow.py`
- Tests complete WebSocket session flow
- Verifies session_id consistency
- Tests concurrent session isolation
- Includes health checks and error handling

## Message Format Standards

### TaskRequest Payload
```typescript
interface GeneralInfoPayload {
  message: string;
  session_id: string;
  user_context: object;
  conversation_history: Array<object>;
}
```

### TaskResponse Result
```typescript
interface TaskResult {
  response: string;
  sources: Array<string>;
  requires_human_handoff: boolean;
  suggested_actions: Array<string>;
  session_id: string;  // ← Required for session mapping
  error?: string;      // ← Optional, present in error cases
}
```

### WebSocket Message
```typescript
interface WebSocketMessage {
  type: "agent_response";
  data: {
    session_id: string;
    response: string;
    requires_human_handoff: boolean;
    suggested_actions: Array<string>;
  };
}
```

## Architectural Principles

### 1. Session Isolation
- Each WebSocket session has unique session_id
- Messages are routed based on session_id throughout pipeline
- No cross-contamination between sessions

### 2. Backward Compatibility
- Changes are additive (session_id field added to existing structures)
- Existing message formats preserved
- No breaking changes to APIs

### 3. Error Resilience
- Session_id preserved in error scenarios when possible
- Graceful degradation when session_id extraction fails
- Consistent error response format

### 4. Minimal Changes
- Leverages existing WebSocket and Kafka infrastructure
- Focused changes only where session_id propagation was missing
- No architectural modifications required

## Monitoring and Debugging

### Log Messages
- Session_id included in all relevant log messages
- Correlation_id tracking throughout pipeline
- Error logging with session context

### Key Metrics
- WebSocket connection count by session_id
- Message delivery success rate by session
- Error rate with session_id preservation

### Debugging Tips
- Check session_id consistency in logs across services
- Verify WebSocket connection mapping in WebSocketManager
- Monitor Kafka message correlation_id and session_id pairing

## Future Enhancements

### Potential Improvements
1. **Session Persistence:** Store session state in Redis for reconnection scenarios
2. **Session Analytics:** Track session duration and message patterns
3. **Load Balancing:** Distribute sessions across multiple backend instances
4. **Session Cleanup:** Automatic cleanup of inactive sessions

### Scalability Considerations
- WebSocket session management across multiple backend instances
- Kafka partition strategy for session-based routing
- Session state synchronization in distributed deployments
