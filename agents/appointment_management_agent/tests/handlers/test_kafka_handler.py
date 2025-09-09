import pytest
from unittest.mock import MagicMock
from app.handlers.kafka_handler import KafkaMessageHandler
from app.models.appointment import AppointmentRequest, TaskRequest

@pytest.fixture
def kafka_client_mock():
    mock = MagicMock()
    mock.send_response = MagicMock()
    return mock

@pytest.fixture
def llm_client_mock():
    mock = MagicMock()
    mock.generate_content.return_value.text = "Appointment confirmed"
    return mock

@pytest.fixture
async def handler(kafka_client_mock):
    handler = KafkaMessageHandler(kafka_client_mock)
    await handler.initialize_dependencies()
    return handler

async def test_handle_valid_appointment_request(handler):
    message = {
        "session_id": "session123",
        "task_id": "task123",
        "intent": "appointment-booking",
        "payload": {
            "user_id": "user123",
            "requested_date": "2025-08-27T14:00:00",
            "service_type": "general-checkup"
        }
    }
    
    await handler.handle_message(message)
    assert handler.kafka_client.send_response.called

async def test_handle_invalid_appointment_request(handler):
    message = {
        "session_id": "session123",
        "task_id": "task123",
        "intent": "appointment-booking",
        "payload": {
            "user_id": "user123",
            "requested_date": "2025-08-27T23:00:00",  # Outside working hours
            "service_type": "general-checkup"
        }
    }
    
    await handler.handle_message(message)
    assert handler.kafka_client.send_response.called
    # Verify error response was sent
    call_args = handler.kafka_client.send_response.call_args[0][0]
    assert call_args["status"] == "error"
