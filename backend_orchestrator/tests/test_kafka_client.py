import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from src.messaging.kafka_client import KafkaClient

class TestKafkaClient:
    
    @pytest.fixture
    def kafka_client(self):
        """Create a Kafka client for testing"""
        return KafkaClient(bootstrap_servers="localhost:9092")
    
    @pytest.mark.asyncio
    async def test_start_success(self, kafka_client):
        """Test successful Kafka client startup"""
        with patch('backend_orchestrator.src.messaging.kafka_client.KafkaProducer') as mock_producer_class:
            mock_producer = Mock()
            mock_producer_class.return_value = mock_producer
            
            await kafka_client.start()
            
            assert kafka_client.producer == mock_producer
            mock_producer_class.assert_called_once_with(
                bootstrap_servers="localhost:9092",
                value_serializer=kafka_client.producer.value_serializer if kafka_client.producer else None,
                key_serializer=kafka_client.producer.key_serializer if kafka_client.producer else None
            )
    
    @pytest.mark.asyncio
    async def test_start_failure(self, kafka_client):
        """Test Kafka client startup failure"""
        with patch('backend_orchestrator.src.messaging.kafka_client.KafkaProducer', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception) as exc_info:
                await kafka_client.start()
            
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stop(self, kafka_client):
        """Test Kafka client shutdown"""
        mock_producer = Mock()
        mock_consumer1 = Mock()
        mock_consumer2 = Mock()
        
        kafka_client.producer = mock_producer
        kafka_client.consumers = {"topic1": mock_consumer1, "topic2": mock_consumer2}
        
        await kafka_client.stop()
        
        mock_producer.close.assert_called_once()
        mock_consumer1.close.assert_called_once()
        mock_consumer2.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_task_request_success(self, kafka_client):
        """Test successful task request sending"""
        mock_producer = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock()  # Mock record metadata
        mock_producer.send.return_value = mock_future
        
        kafka_client.producer = mock_producer
        
        correlation_id = await kafka_client.send_task_request(
            agent_topic="test-agent-topic",
            task_type="appointment_booking",
            payload={"user_id": "123", "message": "Book appointment"}
        )
        
        assert correlation_id is not None
        assert len(correlation_id) == 36  # UUID length
        
        mock_producer.send.assert_called_once()
        call_args = mock_producer.send.call_args
        
        assert call_args[0][0] == "test-agent-topic"  # topic
        assert call_args[1]["key"] == correlation_id  # key
        
        message = call_args[1]["value"]
        assert message["message_type"] == "TASK_REQUEST"
        assert message["correlation_id"] == correlation_id
        assert message["task_type"] == "appointment_booking"
        assert message["payload"]["user_id"] == "123"
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_send_task_request_with_correlation_id(self, kafka_client):
        """Test task request with provided correlation ID"""
        mock_producer = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock()
        mock_producer.send.return_value = mock_future
        
        kafka_client.producer = mock_producer
        
        provided_correlation_id = "custom-correlation-id"
        returned_correlation_id = await kafka_client.send_task_request(
            agent_topic="test-topic",
            task_type="test_task",
            payload={"data": "test"},
            correlation_id=provided_correlation_id
        )
        
        assert returned_correlation_id == provided_correlation_id
        
        call_args = mock_producer.send.call_args
        message = call_args[1]["value"]
        assert message["correlation_id"] == provided_correlation_id
    
    @pytest.mark.asyncio
    async def test_send_task_response(self, kafka_client):
        """Test sending task response"""
        mock_producer = Mock()
        mock_future = Mock()
        mock_future.get.return_value = Mock()
        mock_producer.send.return_value = mock_future
        
        kafka_client.producer = mock_producer
        
        await kafka_client.send_task_response(
            response_topic="response-topic",
            correlation_id="test-correlation-id",
            status="SUCCESS",
            result={"appointment_id": "12345", "time": "2024-01-15 10:00"}
        )
        
        mock_producer.send.assert_called_once()
        call_args = mock_producer.send.call_args
        
        assert call_args[0][0] == "response-topic"
        assert call_args[1]["key"] == "test-correlation-id"
        
        message = call_args[1]["value"]
        assert message["message_type"] == "TASK_RESPONSE"
        assert message["correlation_id"] == "test-correlation-id"
        assert message["status"] == "SUCCESS"
        assert message["result"]["appointment_id"] == "12345"
        assert "timestamp" in message
    
    def test_subscribe_to_responses(self, kafka_client):
        """Test subscribing to response topic"""
        mock_handler = Mock()
        
        with patch('backend_orchestrator.src.messaging.kafka_client.KafkaConsumer') as mock_consumer_class:
            mock_consumer = Mock()
            mock_consumer_class.return_value = mock_consumer
            
            with patch('asyncio.create_task') as mock_create_task:
                kafka_client.subscribe_to_responses("response-topic", mock_handler)
                
                assert "response-topic" in kafka_client.consumers
                assert kafka_client.consumers["response-topic"] == mock_consumer
                assert kafka_client.message_handlers["response-topic"] == mock_handler
                
                mock_consumer_class.assert_called_once_with(
                    "response-topic",
                    bootstrap_servers="localhost:9092",
                    value_deserializer=kafka_client.consumers["response-topic"].value_deserializer if "response-topic" in kafka_client.consumers else None,
                    key_deserializer=kafka_client.consumers["response-topic"].key_deserializer if "response-topic" in kafka_client.consumers else None,
                    group_id='orchestrator-group'
                )
                
                mock_create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_messages(self, kafka_client):
        """Test message consumption"""
        mock_consumer = Mock()
        mock_handler = AsyncMock()
        
        mock_message1 = Mock()
        mock_message1.value = {"correlation_id": "123", "status": "SUCCESS"}
        mock_message2 = Mock()
        mock_message2.value = {"correlation_id": "456", "status": "ERROR"}
        
        mock_consumer.__iter__ = Mock(return_value=iter([mock_message1, mock_message2]))
        
        kafka_client.consumers["test-topic"] = mock_consumer
        kafka_client.message_handlers["test-topic"] = mock_handler
        
        with patch.object(mock_consumer, '__iter__', return_value=iter([mock_message1, mock_message2])):
            try:
                await kafka_client._consume_messages("test-topic")
            except StopIteration:
                pass  # Expected when iterator is exhausted
        
        assert mock_handler.call_count == 2
        mock_handler.assert_any_call({"correlation_id": "123", "status": "SUCCESS"})
        mock_handler.assert_any_call({"correlation_id": "456", "status": "ERROR"})
    
    @pytest.mark.asyncio
    async def test_send_task_request_failure(self, kafka_client):
        """Test task request sending failure"""
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Send failed")
        
        kafka_client.producer = mock_producer
        
        with pytest.raises(Exception) as exc_info:
            await kafka_client.send_task_request(
                agent_topic="test-topic",
                task_type="test_task",
                payload={"data": "test"}
            )
        
        assert "Send failed" in str(exc_info.value)
