"""
Kafka message handler for the Appointment Management Agent.
Handles incoming Kafka messages and routes them to the appropriate service.
"""
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.kafka_messages import TaskRequest, TaskResponse
from app.core.appointment_service import AppointmentService
from app.core.dependencies import get_llm_client
from app.core.config import settings

logger = structlog.get_logger()

class KafkaMessageHandler:
    """Handler for processing Kafka messages for Appointment service.
    
    This handler follows a simple pattern:
    1. Receive and validate Kafka message structure
    2. Extract relevant information
    3. Pass to appointment service for processing
    4. Return formatted response
    
    Features:
    - Clean, structured logging
    - Clear error messages
    - Proper message validation
    
    Future Enhancements:
    1. Add detailed validation in service layer
    2. Add appointment conflict detection
    3. Add support for appointment modifications
    4. Add doctor availability checking
    5. Add multi-timezone support
    """
    def __init__(self, kafka_client):
        self.kafka_client = kafka_client
        self.appointment_service: Optional[AppointmentService] = None
        
    async def initialize_dependencies(self):
        """Initialize Appointment service dependencies"""
        try:
            llm_client = get_llm_client()
            if llm_client is None:
                raise RuntimeError("LLM client failed to initialize.")

            # Initialize appointment service with dependencies
            self.appointment_service = AppointmentService(llm_client=llm_client)
            logger.info("kafka_handler_dependencies_initialized")
        except Exception as e:
            logger.error("kafka_handler_dependency_initialization_failed", exc_info=True)
            raise

    async def handle_message(self, message: Dict[str, Any]):
        """Process incoming Kafka messages."""
        correlation_id = message.get("correlation_id", "unknown")
        try:
            # Parse message using the updated model
            request = TaskRequest(
                message_type=message.get("message_type", "TASK_REQUEST"),
                correlation_id=correlation_id,
                task_type=message.get("task_type", "unknown"),
                payload=message.get("payload", {}),
                timestamp=message.get("timestamp", datetime.now().timestamp())
            )

            logger.info("received_appointment_request",
                       correlation_id=correlation_id,
                       task_type=request.task_type,
                       user_message=request.payload.message[:100])

            # Process the appointment request using LLM
            if not self.appointment_service:
                raise RuntimeError("Appointment service not initialized")
            
            user_message = request.payload.message
            
            # Use LLM to understand the appointment request
            prompt = f"""
            Extract appointment booking information from this user message: '{user_message}'
            If no specific date/time is mentioned, ask for the preferred date and time.
            If a date/time is mentioned, validate it and either confirm or suggest alternative times.
            """
            
            llm_response = await self.appointment_service.llm.generate_content(prompt)
            
            # For now, since we don't have complete date parsing, we'll ask for specifics
            response_payload = {
                "response": llm_response.text,
                "requires_human_handoff": False,
                "session_id": request.payload.session_id,
                "suggested_actions": ["select_date", "select_time", "choose_doctor"],
                "agent_context": {
                    "appointment_state": "awaiting_datetime",
                    "last_message": user_message
                }
            }
            
            # Send response
            await self.kafka_client.send_task_response(
                correlation_id=correlation_id,
                status="SUCCESS",
                result=response_payload
            )
            
            logger.info("appointment_response_sent",
                       correlation_id=correlation_id,
                       session_id=request.payload.session_id)

        except Exception as e:
            # Ensure we have a correlation_id for error response
            if not correlation_id:
                correlation_id = message.get("correlation_id", "unknown")
            
            # Get session_id from the original message if possible
            session_id = (message.get("payload", {}) or {}).get("session_id")
            
            logger.error("appointment_request_failed",
                        error=str(e),
                        correlation_id=correlation_id,
                        session_id=session_id,
                        error_type=type(e).__name__)
            
            # Send error response
            error_payload = {
                "response": "I apologize, but I'm having trouble with the appointment system right now. Please try again in a moment.",
                "requires_human_handoff": True,
                "session_id": session_id,
                "suggested_actions": ["retry", "contact_support"],
                "error_type": type(e).__name__
            }
            
            try:
                await self.kafka_client.send_task_response(
                    correlation_id=correlation_id,
                    status="ERROR",
                    result=error_payload
                )
                logger.info("error_response_sent",
                           correlation_id=correlation_id,
                           session_id=session_id)
            except Exception as send_error:
                logger.error("failed_to_send_error_response",
                           original_error=str(e),
                           send_error=str(send_error),
                           correlation_id=correlation_id)

