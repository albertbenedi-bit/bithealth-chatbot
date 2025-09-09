# Backend AI Orchestrator Service

## Overview

The Backend AI Orchestrator is the central coordination service for the healthcare chatbot system. It manages conversation flow, routes requests to specialized AI agents, handles session state, and provides a unified API interface for client applications.

## Quick Start

### Prerequisites

- Python 3.12+
- Redis server
- Kafka cluster
- PostgreSQL database

### Installation
# macOS/Linux
# You may need to run `sudo apt-get install python3-venv` first on Debian-based OSs
```bash
# Create a virtual environment
python3 -m venv .venv
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Basic Usage

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Chat interaction
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "patient_123",
    "message": "I want to book an appointment"
  }'
```

## Architecture

The service implements a microservices architecture with:

- **FastAPI Application** - REST API endpoints
- **LLM Abstraction Layer** - Provider-agnostic LLM interface (Gemini/Anthropic)
- **Session Manager** - Redis-based conversation state
- **Conversation Engine** - Intent classification and response orchestration
- **Kafka Client** - Agent-to-Agent communication protocol
- **Prompt Manager** - External prompt template management

## Key Features

- **Provider Agnostic**: Easy switching between LLM providers
- **Fault Tolerant**: Automatic fallback between primary/secondary providers
- **Stateful Conversations**: Persistent session management
- **Event-Driven**: Kafka-based async communication with agents
- **Observable**: Comprehensive logging and metrics

## Documentation

- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Architecture Guide](docs/ARCHITECTURE.md) - Detailed architecture documentation

## Configuration

### Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=postgresql://user:pass@postgres.data.svc.cluster.local:5432/chatbot_db
REDIS_URL=redis://redis.data.svc.cluster.local:6379
KAFKA_BOOTSTRAP_SERVERS=kafka.data.svc.cluster.local:9092
DEFAULT_LLM_PROVIDER=gemini
FALLBACK_LLM_PROVIDER=anthropic
```

### LLM Configuration

Edit `config/llm_config.yaml` to configure:
- Provider settings (Gemini/Anthropic)
- Model parameters
- Intent classification settings
- Emergency detection keywords

### Orchestration Rules

Edit `config/orchestration_rules.yaml` to configure:
- Agent routing
- Workflow definitions
- Human handoff triggers
- Rate limiting

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_conversation_engine.py -v
```

## API Endpoints

- `POST /chat` - Main conversation endpoint
- `GET /health` - Service health check
- `GET /session/{id}` - Session retrieval
- `DELETE /session/{id}` - Session cleanup
- `GET /metrics` - Service metrics

## Intent Classifications

- `appointment_booking` - Schedule new appointment
- `appointment_modify` - Change existing appointment
- `general_info` - General inquiries
- `medical_emergency` - Urgent medical situations
- `pre_admission` - Pre-procedure information
- `post_discharge` - Post-care instructions

## Message Formats

### Chat Request
```json
{
  "user_id": "string",
  "message": "string",
  "session_id": "string",
  "context": {}
}
```

### Chat Response
```json
{
  "response": "string",
  "session_id": "string",
  "intent": "string",
  "requires_human_handoff": boolean,
  "suggested_actions": ["string"]
}
```

### Kafka A2A Messages
```json
{
  "message_type": "TASK_REQUEST|TASK_RESPONSE",
  "correlation_id": "uuid",
  "timestamp": "iso8601",
  "task_type": "string",
  "payload": {},
  "status": "SUCCESS|ERROR"
}
```

## Development

### Project Structure

```
backend_orchestrator/
├── src/
│   ├── config/           # Configuration management
│   ├── llm_abstraction/  # LLM provider interface
│   ├── messaging/        # Kafka client
│   ├── session/          # Session management
│   ├── workflow/         # Conversation engine
│   ├── prompts/          # Prompt templates
│   └── main.py           # FastAPI application
├── tests/                # Unit tests
├── config/               # YAML configurations
└── docs/                 # Documentation
```

### Adding New LLM Providers

1. Implement `LLMProviderInterface`
2. Add provider configuration to `llm_config.yaml`
3. Update provider factory in `__init__.py`
4. Add unit tests

### Adding New Intents

1. Add intent patterns to `conversation_engine.py`
2. Create prompt templates in `prompts/`
3. Update routing logic
4. Add test cases

## Monitoring

### Health Checks
- `/health` - Service health status
- `/metrics` - Performance metrics

### Logging
Structured logging with correlation IDs:
```python
logger.info("Message processed", 
           user_id=user_id, 
           session_id=session_id, 
           intent=intent)
```

### Metrics
- Active session count
- Response time percentiles
- Error rates by component
- LLM provider usage

## Troubleshooting

### Common Issues

1. **LLM Provider Errors**: Check API keys and rate limits
2. **Session Issues**: Verify Redis connectivity
3. **Kafka Problems**: Check cluster health and topics
4. **High Latency**: Monitor LLM provider response times

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
```

## Contributing

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Run linting: `flake8 src/`
5. Run tests: `pytest tests/`

## License

[Add license information]
