# High-Level Design Document: Chatbot Assistant for Healthcare

## 1\. Introduction

### 1.1 Background

[cite\_start]Vibe Coding leverages Artificial Intelligence to generate codebase from high-level intent[cite: 362]. [cite\_start]This document extends that philosophy to design a healthcare chatbot focusing on patient interactions for appointment management, pre-admission information, post-discharge instructions, and general information dissemination[cite: 363]. [cite\_start]The system aims to enhance patient experience through automated, timely, and personalized communication, while offloading common queries from human staff and strictly avoiding medical recommendations[cite: 364].

### 1.2 Scope

[cite\_start]This high-level design covers the architectural blueprint for the Vibe Chatbot Assistant, outlining its functional and technical components[cite: 365]. [cite\_start]It defines the core microservices, their responsibilities, communication patterns, and data storage strategies[cite: 366]. [cite\_start]This document does not delve into low-level implementation details, specific API contracts (beyond high-level definitions), or detailed security protocols, which will be addressed in subsequent design phases[cite: 367].

### 1.3 Understanding of Requirements

The core functional requirements for the chatbot are:

  * [cite\_start]**Appointment Management**: Enable patients to schedule, reschedule, and cancel appointments, and receive automated reminders[cite: 368]. [cite\_start]This includes detailed parameters for booking (clinic, specialty, doctor, date/time), scheduling windows, and cancellation policies[cite: 369]. [cite\_start]Identity verification and explicit consent are critical for these secure interactions[cite: 370].
  * **Information Dissemination**:
      * [cite\_start]**Pre-admission Information**: Provide necessary instructions and information before scheduled procedures, personalized based on procedure and doctor's instructions[cite: 371].
      * [cite\_start]**Post-Discharge Instructions**: Deliver personalized post-discharge instructions, medication reminders, and follow-up care plans, integrating with EHR/e-prescribing systems[cite: 372]. [cite\_start]This includes tracking adherence and escalating adverse reactions to human agents[cite: 373].
  * [cite\_start]**General Information & L1 Receptionist**: Answer FAQs about hospital operations, departments, services, visiting hours, and administrative processes[cite: 374]. [cite\_start]Critically, the chatbot must never provide medical advice and must escalate queries suggesting medical advice to human agents or recommend appropriate specialists[cite: 375].
  * [cite\_start]**Communication Channels**: Support SMS, WhatsApp, and hospital application in-app notifications for reminders and information dissemination[cite: 376].
  * [cite\_start]**Administrative Interface**: Healthcare administrators/staff must be able to configure appointment slots, update information, and manage the general information knowledge base[cite: 377].

Key non-functional requirements include:

  * [cite\_start]**Security**: Secure identity verification (patient ID, DOB, OTP) and data handling are paramount[cite: 378].
  * [cite\_start]**Personalization**: Information and services must be personalized based on patient context[cite: 379].
  * [cite\_start]**Reliability & Availability**: The system must be highly available to ensure timely communication and appointment services[cite: 380].
  * [cite\_start]**Scalability**: The system should scale to handle a large volume of patient interactions and data[cite: 381].
  * [cite\_start]**Usability**: The chatbot interface should be intuitive for patients[cite: 382].
  * [cite\_start]**Maintainability**: The system should be easy to update and maintain by the IT/Development Team[cite: 383].

### 1.4 Assumptions

  * [cite\_start]An existing Electronic Health Record (EHR) system is available and provides APIs for patient identification, appointment management (checking availability, booking, rescheduling, cancelling), and e-prescribing data[cite: 384].
  * [cite\_start]Integration with third-party communication channels (SMS, WhatsApp gateway) will be handled via dedicated API modules[cite: 385].
  * [cite\_start]Initial deployment will focus on core features, with iterative development for advanced functionalities (e.g., handling consent revocation)[cite: 386].
  * [cite\_start]Hospital staff will manage general information and pre-admission data via a secure web portal[cite: 387].
  * [cite\_start]Authentication and Authorization for internal services will be managed by a robust Identity and Access Management (IAM) solution[cite: 388].

### 1.5 Constraints

  * [cite\_start]**No Medical Recommendations**: The chatbot must strictly avoid providing medical diagnoses, treatment recommendations, or advice[cite: 389]. [cite\_start]All medical advice-seeking queries must be escalated[cite: 390].
  * [cite\_start]**Data Privacy & Compliance**: Strict adherence to healthcare data privacy regulations (e.g., HIPAA, GDPR equivalents) is required[cite: 390].
  * [cite\_start]**Real-time Interaction (for certain functions)**: Appointment booking and identity verification require near real-time responses[cite: 391].
  * [cite\_start]**Existing Infrastructure**: Where possible, leverage existing hospital IT infrastructure and security policies[cite: 392].

## 2\. Technical Overview

### 2.1 Core Architectural Principles

This design adheres to the following foundational principles:

  * [cite\_start]**Microservices Architecture**: The system is decomposed into small, independent, and loosely coupled services, each with a single responsibility[cite: 393]. [cite\_start]This promotes modularity, independent deployment, and scalability[cite: 394].
  * [cite\_start]**Cloud-Native & Kubernetes-First**: Services are designed for containerization (Docker) and deployment on Kubernetes, ensuring portability, scalability, and automated management[cite: 394]. [cite\_start]This aligns with modern best practices for distributed systems[cite: 395].
  * [cite\_start]**Clean Code & SOLID Principles**: Each service and its internal components will be developed following Clean Code practices and SOLID principles (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) to ensure maintainability, testability, and extensibility[cite: 395].
  * [cite\_start]**Agent-to-Agent (A2A) Communication Protocol**: Internal communication between AI agents and the orchestrator will follow a standardized A2A protocol[cite: 396]. [cite\_start]This ensures interoperability, clear message structures, and efficient task delegation within the AI ecosystem[cite: 397].
  * [cite\_start]**Configurability**: Emphasize externalized configuration for LLM models, prompt templates, business rules (e.g., reminder intervals, cancellation policies), and integration endpoints[cite: 398]. [cite\_start]This allows for dynamic adjustments without code changes[cite: 399].
  * [cite\_start]**Cost-Efficiency**: Design for optimal resource utilization, leveraging serverless components where appropriate, intelligent caching, and efficient RAG strategies to minimize operational costs[cite: 399].
  * [cite\_start]**Resilience & Fault Tolerance**: Implement patterns like circuit breakers, retries with backoff, and asynchronous communication to ensure the system remains available even when individual components fail[cite: 400].
  * [cite\_start]**Event-Driven Architecture (EDA)**: For non-real-time processes like appointment reminders and information dissemination, an event-driven approach will be used to achieve loose coupling and scalability[cite: 401].

### 2.2 LLM Integration Philosophy

The overarching strategy for integrating LLMs is built on flexibility and configurability:

  * [cite\_start]**LLM Abstraction Layer**: All services interacting with LLMs will utilize a common abstraction layer[cite: 402]. [cite\_start]This layer encapsulates the specifics of different LLM providers (e.g., Ollama, Gemini, SageMaker AI) and their APIs, allowing easy swapping of models via configuration without impacting business logic[cite: 403].
  * [cite\_start]**Externalized Prompt Templates**: Prompt templates will not be hardcoded[cite: 404]. [cite\_start]They will be stored in easily accessible configuration files (e.g., YAML, .txt files) or a dedicated database, enabling rapid iteration and A/B testing of prompts[cite: 405]. [cite\_start]Each agent will have its own set of prompt templates relevant to its tasks[cite: 406].
  * [cite\_start]**Common API Usage Pattern**: A standardized pattern will be enforced for all LLM API calls, including parameter passing (temperature, top-k, top-p), input/output parsing, and error handling[cite: 407]. [cite\_start]This consistency simplifies development, testing, and debugging across agents[cite: 408].
  * [cite\_start]**Context Management**: The LLM integration will manage conversation history and relevant retrieved context from RAG, ensuring continuity and informed responses[cite: 408].

## 3\. High-Level Blueprint / Architecture (AI-Assisted - Chain of Thought)

### Thought Process

[cite\_start]To design a modular, scalable, and AI-agentic system for healthcare chatbot requirements, the system is decomposed into distinct, independently deployable microservices[cite: 409]. [cite\_start]The core components are the user interface, a central orchestrator, specialized AI agents, and integration points with external hospital systems[cite: 410].

  * [cite\_start]**Front-end/Chatbot Interface**: This is the primary user interaction point[cite: 411]. [cite\_start]It needs to be lightweight and accessible across various channels (web, SMS, WhatsApp)[cite: 412]. [cite\_start]Its main role is to capture user input and display AI-generated responses[cite: 413].
  * [cite\_start]**Backend AI Orchestrator**: This is the brain of the operation[cite: 414]. [cite\_start]It must handle routing user requests to appropriate agents, managing conversation state, enforcing business rules (like consent, identity verification), and coordinating responses from multiple agents[cite: 415]. [cite\_start]It's also the central point for LLM configuration and the multi-layered RAG implementation[cite: 416]. [cite\_start]This service will translate the "vibe" into actionable tasks[cite: 417].
  * [cite\_start]**Backend AI Agents**: Each agent should be specialized for a specific function as identified in the requirements (Appointment, Pre-admission, Post-discharge, General Info)[cite: 417]. [cite\_start]This ensures the Single Responsibility Principle, allows independent scaling, and reduces complexity within each service[cite: 418]. [cite\_start]These agents will perform the actual AI-driven tasks and interact with external systems[cite: 419].
  * [cite\_start]**Integration Modules**: Direct interaction with external critical systems like EHR/EMR or communication gateways should be encapsulated in dedicated integration services to maintain loose coupling and provide a clear API boundary[cite: 420].
  * [cite\_start]**Data Storage**: PostgreSQL with pgvector is mandated for RAG due to its relational capabilities and vector search functionality[cite: 421]. [cite\_start]Other data storage (e.g., for operational data, auditing) will be specific to service needs, but a centralized RAG is appropriate[cite: 422].

### Inter-Service Communication

  * [cite\_start]**Front-end to Orchestrator**: RESTful APIs (HTTPS) for synchronous request-response[cite: 428]. [cite\_start]An API Gateway will secure and manage these external interactions[cite: 429]. [cite\_start]WebSockets (or SSE) are used for real-time updates to the user's browser, maintaining a persistent connection to push data without the client needing to poll[cite: 429].
      * **Architecture to achieve**:
          * [cite\_start]Frontend (Browser) sends message: The user types a message and sends it via an HTTP POST request to the FastAPI backend (`/chat` endpoint)[cite: 430].
          * [cite\_start]FastAPI Backend sends "Temporary Response": The FastAPI backend immediately returns an "I'm processing..." message via the HTTP response to the frontend[cite: 431].
          * [cite\_start]FastAPI Backend publishes task to Kafka: In the background (after sending the HTTP response), the FastAPI backend publishes the actual request to a Kafka topic (e.g., `appointment-agent-requests`, `general-info-requests`)[cite: 432].
          * [cite\_start]Kafka Agent processes request: A separate Kafka consumer service (e.g., the `appointment-agent`) picks up the message from Kafka, processes it, and then publishes its result back to a Kafka response topic (e.g., `appointment-agent-responses`)[cite: 433].
          * [cite\_start]FastAPI Backend consumes final response from Kafka: The FastAPI backend also has a Kafka consumer running (`_handle_agent_response`) that listens to these response topics[cite: 434].
          * [cite\_start]FastAPI Backend pushes final response to Frontend: When `_handle_agent_response` receives the final result from Kafka, it then uses an active WebSocket connection (which the frontend should have established with the backend specifically for real-time updates) to push that final response to the user's browser[cite: 435].
          * [cite\_start]Kafka is crucial for the internal, asynchronous flow of the backend, while WebSockets remain the standard and necessary way to deliver real-time, unsolicited updates from the backend to the user's browser[cite: 436].
  * [cite\_start]**Orchestrator to Agents (A2A)**: Asynchronous message queues (e.g., Kafka or RabbitMQ) for task delegation and result collection[cite: 437]. [cite\_start]This enables loose coupling, handles back pressure, and supports long-running agent tasks[cite: 438]. [cite\_start]A synchronous fallback (e.g., gRPC) might be considered for very high-priority, low-latency agent calls if strict real-time guarantees are needed, but asynchronous is generally preferred for agentic workflows[cite: 439]. [cite\_start]The A2A protocol will define the message schema (e.g., `task_id`, `agent_id`, `input_payload`, `context_data`, `callback_topic`)[cite: 440]. [cite\_start]Kafka is an excellent backend-to-backend (B2B) communication bus, perfect for: decoupling services (e.g., Conversation Engine from Appointment Agent), handling asynchronous tasks reliably, and building scalable, fault-tolerant data pipelines[cite: 441].
  * [cite\_start]**Orchestrator/Agents to Integration Modules**: RESTful APIs or gRPC for synchronous interactions (e.g., booking appointments in EHR)[cite: 442].
  * [cite\_start]**Event Bus (Kafka)**: A central event bus (e.g., Kafka) will be used for publishing events (e.g., "Appointment Booked," "Discharge Instructions Ready") that trigger asynchronous processes (e.g., sending reminders, delivering pre-admission info)[cite: 443].

### Modular Storage

  * [cite\_start]**RAG Knowledge Base**: A dedicated PostgreSQL database with pgvector extension will serve as the primary knowledge store for RAG[cite: 444].
      * [cite\_start]**Data Types**: It will store embeddings for general FAQs, pre-admission guides, post-discharge instructions, and any other relevant contextual documents[cite: 445].
      * **Multi-layered RAG**: Different indexes or tables within pgvector can be used to store embeddings for:
          * [cite\_start]**Intent Recognition**: High-level semantic vectors for mapping user queries to broad categories or tasks (e.g., "booking," "information," "escalation")[cite: 446, 489].
          * [cite\_start]**Relevancy Retrieval**: Detailed vectors for specific document chunks or passages, allowing precise retrieval of contextual information for LLMs[cite: 447, 490].
  * **Operational Data**:
      * [cite\_start]**Orchestrator**: Small, ephemeral database (e.g., Redis for session state, or a lightweight PostgreSQL) for active conversation sessions, workflow state, and pending tasks[cite: 491].
      * [cite\_start]**Appointment Management Agent**: May have a localized PostgreSQL instance for transient booking states or audit logs before committing to EHR[cite: 492].
      * [cite\_start]**Knowledge Base Service**: PostgreSQL for structured general information and metadata related to RAG documents[cite: 493].
      * [cite\_start]**Auditing/Logging**: Centralized logging system (e.g., ELK stack, Splunk) for all service logs and audit trails[cite: 494].

### ASCII Art Diagram (Overall Architecture Topology)

```
+-----------------------+           +----------------------+
|                       |           |                      |
|  User Interface       |           |  Admin Dashboard     |
|  (Web/Mobile App)     |           |  (Staff/Admin UI)    |
|                       |           |                      |
+-----------+-----------+           +-----------+----------+
            | REST/HTTPS                         | REST/HTTPS
            |                                    |
            v                                    v
+-------------------------------------------------------------+
|                     API Gateway                             |
| (Authentication, Rate Limiting, Routing)                    |
+--------------------------+----------------------------------+
            |
            | REST/HTTPS
            v
+----------------------------------+
|    Backend AI Orchestrator       |
|----------------------------------|
| - Intent Recognition             |
| - Conversation State Management  |
| - Agent Coordination             |
| - Workflow Engine                |
| - LLM Abstraction Layer          |
| - RAG Orchestration              |
| - Security & Policy Enforcement  |
| - Event Publisher                |
+-----------+----------+-----------+
            | Kafka/A2A |
            |           |
+---------------------v-----------v---------------------+
|                                                       |
|                   Kafka Event Bus                     |
|                                                       |
+---------------------^-----------^---------------------+
            | Kafka/A2A | Events
            |           |
+----------+----------+-----------+---------+-----------+
|          |          |                     |           |
v          v          v                     v           v
+-----------------+ +-----------------+ +-----------------+ +-----------------+
| Appointment     | | Info Dissem.    | | General Info    | | Auth/Identity   |
| Management Agent| | Agent (Pre/Post)| | Agent (L1 Rep.) | | Service         |
|-----------------| |-----------------| |-----------------| |-----------------|
| - Book/Resched  | | - Pre-Admis Info| | - FAQ Retrieval | | - Patient ID/DOB|
| - Cancel Appt   | | - Post-Disch Ins| | - NLU/Query Und.| | - OTP Validation|
| - Reminders     | | - Med Reminders | | - Human Handoff | | - Consent Mgmt. |
+--------+--------+ +--------+--------+ +--------+--------+ +--------+--------+
         | REST/gRPC         | REST/gRPC         | REST/gRPC         | REST/gRPC
         |                   |                   |                   |
         v                   v                   v                   v
+-----------------+ +-------------------+ +-----------------+ +-----------------+
| EHR/EMR         | | Communication     | | Knowledge Base  | | External        |
| Integration     | | Gateway Service   | | Service (RAG)   | | Databases/APIs  |
| Service         | | (SMS/WhatsApp)    | | (PostgreSQL/pgV)| | (e.g., CMS)     |
|-----------------| |-------------------| |-----------------| |-----------------|
| - Patient Data  | | - Send Messages   | | - Gen. Info KB  | | - Content Mgmt. |
| - Appt. Slots   | | - Status Tracking | | - Pre-Admis DB  | | - Policy Mgmt.  |
| - e-Prescribing | |                   | | - Vector Store  | |                 |
+-----------------+ +-------------------+ +-----------------+ +-----------------+
```

[cite\_start][cite: 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513]

## 4\. Module Breakdown (AI-Assisted)

[cite\_start]This section details the granular breakdown of key services, their responsibilities, dependencies, testability, and proposed mono-repo structure with LLM configurability[cite: 514].

### Mono-Repo Structure Example

```
/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── README.md
├── backend_orchestrator/
│   ├── src/
│   │   ├── main.py
│   |   ├── prompts/
│   │   |   ├── system_prompt.txt
│   │   |   ├── intent_recognition.txt
│   │   |   └── conversation_summarization.txt
│   │   ├── llm_abstraction/
│   │   ├── conversation_manager/
│   │   ├── workflow_engine/
│   │   └── agent_router/
│   ├── config/
│   │   ├── llm_config.yaml  # Global LLM settings
│   │   └── orchestration_rules.yaml
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── agents/
│   ├── appointment_management_agent/
│   │   ├── src/
│   │   │   ├── main.py
|   │   │   ├── prompts/
│   |   │   │   ├── booking_confirmation.txt
│   │   |   │   ├── reminder_template.txt
│   │   │   |   └── cancellation_policy_explain.txt
│   │   │   ├── appointment_logic/
│   │   │   └── communication_handlers/
│   │   ├── config/
│   │   │   ├── llm_config.yaml  # Agent-specific LLM settings
│   │   │   └── agent_config.yaml
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── info_dissemination_agent/
│   │   ├── src/
│   │   ├── config/
│   │   ├── prompts/
│   │   │   ├── pre_admission_summary.txt
│   │   │   ├── post_discharge_meds.txt
│   │   │   └── adverse_reaction_escalation.txt
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   └── general_info_agent/
│       ├── src/
│       |   ├── prompts/
│       |   │   ├── faq_query.txt
│       |   │   ├── medical_advice_disclaimer.txt
│       |   │   └── human_handoff_reason.txt
│       ├── config/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── README.md
├── integrations/
│   ├── ehr_integration_service/
│   │   ├── src/
│   │   ├── config/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── communication_gateway_service/
│   │   ├── src/
│   │   ├── config/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   └── knowledge_base_service/
│       ├── src/
│       │   ├── main.py
│       │   ├── vector_db_connector/
│       │   └── content_manager/
│       ├── config/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── README.md
├── auth_identity_service/
│   ├── src/
│   ├── config/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
└── README.md # Main mono-repo README
```

[cite\_start][cite: 515, 516, 517, 518]

### Service Breakdown

#### 4.1 Backend AI Orchestrator Service

**High-Level Responsibilities**: The central intelligence and coordination hub. [cite\_start]It receives user requests, determines intent, manages the multi-turn conversation flow, selects and delegates tasks to appropriate AI agents, aggregates agent responses, and formats the final reply[cite: 518]. [cite\_start]It also enforces security policies (identity, consent) and integrates RAG for contextual understanding[cite: 520].

**Frontend - Backend AI Orchestrator Logic with WebSockets**:

  * [cite\_start]When a user starts a session, it opens an HTTP POST to `/chat` to get the initial `session_id`[cite: 521].
  * [cite\_start]Once `session_id` is received, it immediately opens a WebSocket connection to `ws://your-backend/ws/{session_id}`[cite: 522].
  * [cite\_start]When the user sends a message, it makes another HTTP POST to `/chat`[cite: 523].
  * [cite\_start]It immediately displays the response from this HTTP POST (the "temporary message")[cite: 524].
  * [cite\_start]It then listens on the WebSocket for a message with `type: "final_response"` that matches the `session_id` (and potentially `correlation_id` if you track multiple pending requests per session)[cite: 525].
  * [cite\_start]When the final response arrives via WebSocket, it updates the chat UI[cite: 526].

**Core Functionalities**:

  * [cite\_start]User input parsing and intent classification[cite: 527].
  * [cite\_start]State machine for managing complex conversations (e.g., multi-step booking)[cite: 527].
  * [cite\_start]Agent discovery and dynamic routing[cite: 528].
  * [cite\_start]Response synthesis from multiple agents[cite: 528].
  * [cite\_start]LLM calls for general conversation and high-level reasoning[cite: 528].
  * [cite\_start]RAG query generation and context injection into prompts[cite: 529].
  * [cite\_start]Publishing system events[cite: 529].

[cite\_start]**Dependencies**: Front-end Service (via API Gateway), all Backend AI Agent Services (via Kafka), Auth/Identity Service (REST/gRPC), Knowledge Base Service (for RAG context), Kafka Event Bus[cite: 530].

[cite\_start]**Testability**: Can be tested independently by mocking agent responses, external API calls, and Kafka messages[cite: 531]. Unit tests for internal modules (workflow engine, agent router, LLM abstraction). [cite\_start]Integration tests simulating end-to-end flows with mocked dependencies[cite: 532].

[cite\_start]**Data Storage Needs**: Lightweight, in-memory cache (Redis) for active conversation state and transient data[cite: 533]. [cite\_start]Potentially a small database (e.g., PostgreSQL) for workflow definitions or audit logs[cite: 534].

[cite\_start]**Primary Inter-Service Communication**: Receives REST from API Gateway[cite: 535]. [cite\_start]Communicates with Agents via Kafka (A2A protocol)[cite: 535]. [cite\_start]Sync calls to Auth/Identity and Knowledge Base (for vector lookup)[cite: 536]. [cite\_start]Publishes events to Kafka[cite: 536].

[cite\_start]**Proposed Folder Structure (within mono-repo)**: `/backend_orchestrator/` (as shown above)[cite: 537].

**README.md Outline**:

  * [cite\_start]**Backend AI Orchestrator Service Description**: Central service for managing AI agent workflows, conversation state, and LLM interactions[cite: 538].
  * [cite\_start]**Features**: Intent classification, agent routing, multi-turn conversation management, RAG integration, LLM abstraction, event publishing[cite: 539].
  * [cite\_start]**Dependencies**: Kafka, Redis, PostgreSQL (optional for persistent state), Auth/Identity Service, all AI Agent Services[cite: 540].
  * [cite\_start]**Setup**: Environment variables (.env): Kafka broker URL, Redis connection string, LLM API keys (via secrets management)[cite: 541]. [cite\_start]Configuration (config/): `llm_config.yaml`, `orchestration_rules.yaml`[cite: 542]. [cite\_start]Prompt templates (prompts/): System, intent recognition, summarization[cite: 542].
  * [cite\_start]**Build**: `docker build -t vibe-orchestrator .`[cite: 542].
  * [cite\_start]**Run**: `docker run -p 8080:8080 vibe-orchestrator`[cite: 543].
  * [cite\_start]**API Endpoints**: `/v1/chat/message`, `/v1/health`[cite: 543].
  * [cite\_start]**Internal Components**: `llm_abstraction`, `conversation_manager`, `workflow_engine`, `agent_router`[cite: 543].
  * [cite\_start]**Testing**: `pytest` commands for unit and integration tests[cite: 544].

**ASCII Art Diagram (Backend AI Orchestrator Component Diagram)**:

```
+------------------------------------------------------------------+
| Backend AI Orchestrator Service |
| |
| +-------------------+ +---------------------+ |
| | User Input Handler|<---| API Gateway | |
| | (External Interface)| |
| +----------+--------+ +---------------------+ |
| | |
| v |
| +-------------------------+ |
| | Intent Recognition & | |
| | Routing Engine | |
| +----------+--------------+ |
| (Identified Intent, Context) |
| v |
| +-------------------------+ |
| | Conversation Manager |<---+ (Updates, Decisions) |
| | (State, History) | |
| +----------+--------------+ |
| | |
| v |
| +-------------------------+ |
| | Workflow Engine |-----| (Handles complex flows e.g. booking) |
| | (Business Logic Rules) |
| +----------+--------------+ |
| (Task for Agent) |
| v |
| +-------------------------+ |
| | Agent Registry & | |
| | Task Dispatcher |-----| (Publishes/Consumes A2A messages) |
| +----------+--------------+ |
| | |
| v |
| +-------------------------+ |
| | LLM Abstraction Layer |<----| (Invokes LLM for responses) |
| | (Model Swapping, | |
| | Prompt Templates) | |
| +----------+--------------+ |
| | |
| v |
| +-------------------------+ |
| | RAG Orchestration Module|<----| (Queries Vector DB for context)
```
