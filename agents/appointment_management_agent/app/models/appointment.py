from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from app.core.config import settings

class AppointmentRequest(BaseModel):
    """Model for appointment booking requests"""
    user_id: str = Field(..., min_length=3, max_length=50)
    requested_date: datetime
    service_type: str = Field(..., min_length=3, max_length=100)
    doctor_id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
    notes: Optional[str] = Field(None, max_length=500)
    appointment_id: Optional[str] = None

    @field_validator('requested_date')
    def validate_date(cls, v):
        now = datetime.now()
        min_date = now + timedelta(hours=settings.MIN_BOOKING_HOURS_NOTICE)
        max_date = now + timedelta(days=settings.MAX_BOOKING_DAYS_AHEAD)
        
        if v < min_date:
            raise ValueError(f'Appointment must be at least {settings.MIN_BOOKING_HOURS_NOTICE} hours in advance')
        if v > max_date:
            raise ValueError(f'Appointment cannot be more than {settings.MAX_BOOKING_DAYS_AHEAD} days in advance')
        if v.hour < settings.WORKING_HOURS_START or v.hour >= settings.WORKING_HOURS_END:
            raise ValueError(f'Appointments only available between {settings.WORKING_HOURS_START}:00 and {settings.WORKING_HOURS_END}:00')
        return v

class AppointmentResponse(BaseModel):
    """Model for appointment booking responses"""
    appointment_id: str
    user_id: str
    scheduled_date: datetime
    service_type: str
    status: Literal['confirmed', 'cancelled', 'completed']
    notes: Optional[str] = None

class TaskRequest(BaseModel):
    """Model for incoming Kafka task requests"""
    message_type: str = Field(default="TASK_REQUEST")  # From the orchestrator logs
    correlation_id: str
    task_type: str
    payload: dict  # Contains message, session_id, user_context, conversation_history
    timestamp: Optional[float] = None

class TaskResponse(BaseModel):
    """Model for outgoing Kafka task responses"""
    session_id: str = Field(..., min_length=3, max_length=50)
    task_id: str = Field(..., min_length=3, max_length=50)
    status: Literal['success', 'error']
    response: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
