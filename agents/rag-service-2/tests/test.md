# RAG Service - Testing Guide

This document outlines the testing strategy for the `rag-service-2` and provides instructions on how to run the test suite.

## Testing Philosophy

The test suite is designed to follow a bottom-up approach, ensuring that core components are validated before testing the layers that depend on them. The primary goals are:

- **Unit Testing**: Each component (service, handler, endpoint) is tested in isolation.
- **Dependency Mocking**: External dependencies (like databases, LLMs, and Kafka clients) are mocked to ensure tests are fast, deterministic, and do not rely on external systems.
- **Comprehensive Coverage**: Tests cover success paths, error conditions, and edge cases for all major features.

## Test Structure

The `tests/` directory mirrors the application's structure:

- `tests/core/`: Contains unit tests for the core business logic, such as `RAGService` and `PGVectorRetriever`.
- `tests/api/`: Contains unit tests for the FastAPI REST endpoints, validating request/response cycles and dependency injection.
- `tests/handlers/`: Contains unit tests for the `KafkaMessageHandler`, validating asynchronous message processing and error handling.

## Testing Flow

The testing process validates the application in the following order:

1.  **Core Logic (`tests/core/`)**:
    - **`test_retriever.py`**: Verifies that the `PGVectorRetriever` correctly calls the appropriate search methods (`similarity_search`, `mmr`) on its underlying vector store mock.
    - **`test_rag_service.py`**: Verifies that the `RAGService` correctly orchestrates the RAG pipeline. It checks that the retriever is called, context is formatted, and the LLM chain is invoked. It tests both scenarios where documents are found and where they are not.

2.  **API Layer (`tests/api/`)**:
    - **`test_endpoints.py`**:
        - Mocks the `RAGService` using FastAPI's `dependency_overrides`.
        - Simulates a `POST` request to `/v1/ask` to ensure it returns a `200 OK` with the correct data when the service succeeds.
        - Simulates a `POST` request where the mocked service raises an exception to ensure the endpoint correctly returns a `500 Internal Server Error`.
        - Tests the `GET /v1/health` endpoint to confirm it returns a `200 OK` status.

3.  **Messaging Layer (`tests/handlers/`)**:
    - **`test_kafka_handler.py`**:
        - Mocks the `KafkaClient` and `RAGService`.
        - Tests the successful processing of a `general_info` message, ensuring the `RAGService` is called and a "SUCCESS" response is sent via the mocked Kafka client.
        - Tests the scenario where the `RAGService` fails, ensuring an "ERROR" response is sent.
        - Tests the handling of unsupported task types and malformed messages.
        - Verifies that structured logs are emitted with the correct contextual information (`correlation_id`, `task_type`, etc.).

## How to Run Tests

### Prerequisites

1.  Ensure you have installed the project dependencies, including the development dependencies.
    ```bash
    poetry install
    ```

### Running the Full Test Suite

To run all unit tests, navigate to the root of the `rag-service-2` directory and execute the following command:

```bash
poetry run pytest
```

For more detailed output, you can use the verbose flag:

```bash
poetry run pytest -v
```