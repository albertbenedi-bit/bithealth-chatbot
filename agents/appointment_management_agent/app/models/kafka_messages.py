"""
Message models for Kafka communication.
Matches exactly what the backend orchestrator sends.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class MessagePayload(BaseModel):
    """Payload structure that comes from the backend_orchestrator"""
    message: str
    session_id: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)

class TaskRequest(BaseModel):
    """Matches the exact structure the backend_orchestrator sends"""
    message_type: str = "TASK_REQUEST"
    correlation_id: str
    task_type: str
    payload: MessagePayload
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "TASK_REQUEST",
                "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_type": "appointment_booking",
                "payload": {
                    "message": "I would like to book an appointment",
                    "session_id": "session-123",
                    "user_context": {},
                    "conversation_history": []
                },
                "timestamp": 1640995200.0
            }
        }

class TaskResponse(BaseModel):
    """Simple Kafka task response message structure"""
    message_type: str = "TASK_RESPONSE"
    correlation_id: str
    status: str  # "SUCCESS" or "ERROR"
    result: Dict[str, Any]
    timestamp: float

    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "TASK_RESPONSE",
                "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "SUCCESS",
                "result": {
                    "response": "I can help you book an appointment.",
                    "requires_human_handoff": False,
                    "suggested_actions": ["confirm_date", "select_doctor"],
                    "agent_context": {
                        "appointment_params": {
                            "requested_date": "2025-09-01T10:00:00",
                            "service_type": "general_checkup"
                        }
                    }
                },
                "timestamp": 1640995205.0
            }
        }

# Future Enhancements:
# 1. Add AppointmentRequest model for service layer validation
# 2. Add AppointmentResponse model for confirmed bookings
# 3. Add rich validation rules for appointment parameters
# 4. Add conflict checking logic
# 5. Add support for recurring appointments

