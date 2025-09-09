import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# The class to be tested
from app.handlers.kafka_handler import KafkaMessageHandler
from app.models.rag import RAGResult

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_kafka_client():
    """Mocks the KafkaClient."""
    client = MagicMock()
    # Mock the async method send_task_response
    client.send_task_response = AsyncMock()
    return client

@pytest.fixture
def mock_rag_service():
    """Mocks the RAGService."""
    service = MagicMock()
    service.ask.return_value = RAGResult(
        text="Mocked RAG answer",
        sources=["mock_source.txt"]
    )
    return service

@pytest.fixture
def handler(mock_kafka_client, mock_rag_service):
    """Creates a KafkaMessageHandler instance with mocked dependencies."""
    h = KafkaMessageHandler(mock_kafka_client)
    # Manually set the initialized service, as we are not testing initialize_dependencies here
    h.rag_service = mock_rag_service
    return h

async def test_handle_general_info_request_success(handler, mock_kafka_client, mock_rag_service):
    """Tests the handler for a successful general_info request."""
    # Arrange
    correlation_id = "test-corr-id-123"
    session_id = "test-session-id-456"
    message = {
        "message_type": "TASK_REQUEST",
        "correlation_id": correlation_id,
        "task_type": "general_info",
        "payload": {
            "message": "What is the policy?",
            "session_id": session_id
        },
        "timestamp": 12345.678
    }

    # Act
    await handler.handle_message(message)

    # Assert
    # Verify RAGService was called correctly
    mock_rag_service.ask.assert_called_once_with(question="What is the policy?")
    
    # Verify the success response was sent via Kafka
    mock_kafka_client.send_task_response.assert_called_once()
    call_args = mock_kafka_client.send_task_response.call_args
    
    assert call_args.kwargs['correlation_id'] == correlation_id
    assert call_args.kwargs['status'] == "SUCCESS"
    
    result_payload = call_args.kwargs['result']
    assert result_payload['response'] == "Mocked RAG answer"
    assert result_payload['sources'] == ["mock_source.txt"]
    assert result_payload['session_id'] == session_id
    assert result_payload['requires_human_handoff'] is False

async def test_handle_general_info_request_rag_error(handler, mock_kafka_client, mock_rag_service):
    """Tests the handler when the RAGService raises an exception."""
    # Arrange
    mock_rag_service.ask.side_effect = Exception("RAG pipeline failed")
    correlation_id = "test-corr-id-err"
    session_id = "test-session-id-err"
    message = {
        "message_type": "TASK_REQUEST",
        "correlation_id": correlation_id,
        "task_type": "general_info",
        "payload": {
            "message": "A question that causes an error",
            "session_id": session_id
        },
        "timestamp": 12345.678
    }

    # Act
    await handler.handle_message(message)

    # Assert
    mock_rag_service.ask.assert_called_once_with(question="A question that causes an error")
    
    # Verify the error response was sent via Kafka
    mock_kafka_client.send_task_response.assert_called_once()
    call_args = mock_kafka_client.send_task_response.call_args
    
    assert call_args.kwargs['correlation_id'] == correlation_id
    assert call_args.kwargs['status'] == "ERROR"
    
    result_payload = call_args.kwargs['result']
    assert "I'm sorry" in result_payload['response']
    assert result_payload['session_id'] == session_id
    assert result_payload['requires_human_handoff'] is True

async def test_handle_unsupported_task_type(handler, mock_kafka_client, mock_rag_service):
    """Tests the handler for an unsupported task type."""
    # Arrange
    correlation_id = "test-corr-id-unsupported"
    message = {
        "message_type": "TASK_REQUEST",
        "correlation_id": correlation_id,
        "task_type": "unsupported_task",
        "payload": {},
        "timestamp": 12345.678
    }

    # Act
    await handler.handle_message(message)

    # Assert
    # RAG service should not be called
    mock_rag_service.ask.assert_not_called()
    
    # Verify the error response was sent
    mock_kafka_client.send_task_response.assert_called_once()
    call_args = mock_kafka_client.send_task_response.call_args
    
    assert call_args.kwargs['correlation_id'] == correlation_id
    assert call_args.kwargs['status'] == "ERROR"
    assert "Unsupported task type: unsupported_task" in call_args.kwargs['result']['error']

async def test_handle_message_parsing_error(handler, mock_kafka_client, mock_rag_service):
    """Tests the handler when the incoming message is malformed."""
    # Arrange
    # Message is missing 'task_type' which is required by TaskRequest model
    malformed_message = {
        "correlation_id": "test-corr-id-malformed",
        "payload": {}
    }

    # Act
    await handler.handle_message(malformed_message)

    # Assert
    mock_rag_service.ask.assert_not_called()
    
    # Verify the error response was sent
    mock_kafka_client.send_task_response.assert_called_once()
    call_args = mock_kafka_client.send_task_response.call_args
    
    assert call_args.kwargs['correlation_id'] == "test-corr-id-malformed"
    assert call_args.kwargs['status'] == "ERROR"
    # The error message will be from Pydantic's validation
    assert "validation error" in call_args.kwargs['result']['error']

@patch('app.handlers.kafka_handler.logger')
async def test_handle_message_structured_logging(mock_logger, handler):
    """Tests that structured logs are emitted with correct context during a successful request."""
    # Arrange
    correlation_id = "log-corr-id-789"
    session_id = "log-session-id-101"
    task_type = "general_info"
    message = {
        "message_type": "TASK_REQUEST",
        "correlation_id": correlation_id,
        "task_type": task_type,
        "payload": {
            "message": "This is a test for logging.",
            "session_id": session_id
        },
        "timestamp": 12345.678
    }

    # Act
    await handler.handle_message(message)

    # Assert
    # Check the sequence and content of logging calls
    # 1. Message received
    mock_logger.info.assert_any_call("kafka_message_received", message=message)

    # 2. Processing request
    mock_logger.info.assert_any_call(
        "processing_kafka_task_request",
        correlation_id=correlation_id,
        task_type=task_type
    )

    # 3. Request processed successfully
    mock_logger.info.assert_any_call(
        "general_info_request_processed_successfully",
        correlation_id=correlation_id
    )

    # 4. Sending success response
    mock_logger.info.assert_any_call("sending_success_response", correlation_id=correlation_id)

    # Ensure no error logs were made
    mock_logger.error.assert_not_called()