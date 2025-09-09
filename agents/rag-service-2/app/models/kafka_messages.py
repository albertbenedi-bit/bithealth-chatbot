from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class TaskRequest(BaseModel):
    """Kafka task request message structure"""
    message_type: str = "TASK_REQUEST"
    correlation_id: str
    task_type: str
    payload: Dict[str, Any]
    timestamp: float

    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "TASK_REQUEST",
                "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_type": "general_info",
                "payload": {
                    "message": "What are your opening hours?",
                    "session_id": "session-123",
                    "user_context": {},
                    "conversation_history": []
                },
                "timestamp": 1640995200.0
            }
        }

class TaskResponse(BaseModel):
    """Kafka task response message structure"""
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
                    "response": "Our hospital is open 24/7 for emergency services.",
                    "sources": ["hospital_policy.pdf", "operating_hours.docx"],
                    "requires_human_handoff": False,
                    "suggested_actions": []
                },
                "timestamp": 1640995205.0
            }
        }

class GeneralInfoPayload(BaseModel):
    """Payload structure for general info requests"""
    message: str
    session_id: str
    user_context: Optional[Dict[str, Any]] = {}
    conversation_history: Optional[list] = []

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are your visiting hours?",
                "session_id": "session-456",
                "user_context": {"language": "en"},
                "conversation_history": [
                    {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"}
                ]
            }
        }
