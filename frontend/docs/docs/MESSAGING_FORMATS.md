# Messaging Formats and Standards

## Overview

This document defines the standard messaging formats, data structures, and communication protocols used in the PV Chatbot Frontend application. These standards ensure consistent data exchange between the frontend, backend orchestrator, and authentication services.

## API Communication Standards

### HTTP Standards

#### Request Headers
```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
Accept: application/json
User-Agent: PV-Chatbot-Frontend/1.0.0
```

#### Response Headers
```http
Content-Type: application/json
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

#### Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request format
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Authentication Message Formats

### Login Request
```typescript
interface LoginRequest {
  email: string;           // Valid email format
  password: string;        // Minimum 8 characters
  remember_me?: boolean;   // Optional, defaults to false
}
```

**Example:**
```json
{
  "email": "patient@example.com",
  "password": "securePassword123",
  "remember_me": true
}
```

### Authentication Response
```typescript
interface AuthResponse {
  access_token: string;    // JWT token
  token_type: string;      // Always "Bearer"
  expires_in: number;      // Token expiration in seconds
  user: User;              // User information
}
```

**Example:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "patient@example.com",
    "name": "John Doe",
    "role": "patient",
    "department": null
  }
}
```

### User Data Format
```typescript
interface User {
  id: string;              // Unique user identifier
  email: string;           // User email address
  name: string;            // Display name
  role: UserRole;          // User role enum
  department?: string;     // Optional department
}

type UserRole = 'patient' | 'staff' | 'admin';
```

## Chat Message Formats

### Chat Request Format
```typescript
interface ChatRequest {
  user_id: string;         // Required: User identifier
  message: string;         // Required: User message (max 2000 chars)
  session_id?: string;     // Optional: Existing session UUID
  context?: ChatContext;   // Optional: Additional context
}

interface ChatContext {
  language?: 'en' | 'id';           // Language preference
  user_type?: 'patient' | 'staff';  // User type
  department?: string;              // Hospital department
  priority?: 'low' | 'normal' | 'high'; // Message priority
}
```

**Example:**
```json
{
  "user_id": "patient_123",
  "message": "I want to book an appointment with a cardiologist",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "language": "en",
    "user_type": "patient",
    "priority": "normal"
  }
}
```

### Chat Response Format
```typescript
interface ChatResponse {
  response: string;                    // AI-generated response
  session_id: string;                  // Session identifier (UUID)
  intent: string;                      // Classified intent
  requires_human_handoff: boolean;     // Human intervention needed
  suggested_actions: string[];         // Suggested follow-up actions
  confidence_score: number;           // Intent confidence (0-1)
  processing_time_ms: number;         // Response processing time
}
```

**Example:**
```json
{
  "response": "I'll help you book a cardiology appointment. Let me check available slots for you.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "appointment_booking",
  "requires_human_handoff": false,
  "suggested_actions": ["wait_for_agent_response"],
  "confidence_score": 0.98,
  "processing_time_ms": 1150
}
```

### Intent Classifications

| Intent | Description | Example Messages |
|--------|-------------|------------------|
| `appointment_booking` | Schedule new appointment | "I want to book an appointment", "Schedule me with a doctor" |
| `appointment_modify` | Change existing appointment | "Reschedule my appointment", "Cancel my booking" |
| `general_info` | General inquiries | "What are your hours?", "Where is the parking?" |
| `medical_emergency` | Urgent medical situations | "I have chest pain", "This is an emergency" |
| `pre_admission` | Pre-procedure information | "What should I prepare for surgery?" |
| `post_discharge` | Post-care instructions | "What medications should I take?" |

### Suggested Actions

| Action | Description |
|--------|-------------|
| `wait_for_agent_response` | Agent is processing request |
| `select_appointment_slot` | Choose from available appointments |
| `provide_patient_id` | Patient identification required |
| `contact_support` | Escalate to human support |
| `call_emergency_services` | Call emergency number immediately |
| `rephrase` | Rephrase the question |

## Session Management Formats

### Session Data Structure
```typescript
interface SessionData {
  session_id: string;                    // UUID format
  user_id: string;                       // User identifier
  created_at: string;                    // ISO 8601 timestamp
  last_activity: string;                 // ISO 8601 timestamp
  conversation_history: ConversationMessage[]; // Message array
  context: SessionContext;               // Session context
  pending_tasks: PendingTask[];          // Pending operations
}
```

### Conversation Message Format
```typescript
interface ConversationMessage {
  timestamp: string;                     // ISO 8601 timestamp
  role: 'user' | 'assistant' | 'system'; // Message sender
  content: string;                       // Message content
  metadata?: MessageMetadata;            // Optional metadata
}

interface MessageMetadata {
  intent?: string;                       // Classified intent
  confidence?: number;                   // Confidence score
  processing_time?: number;              // Processing time in ms
  error?: string;                        // Error message if any
}
```

**Example:**
```json
{
  "timestamp": "2024-01-15T10:29:00Z",
  "role": "user",
  "content": "I need to book an appointment",
  "metadata": null
}
```

### Session Context Format
```typescript
interface SessionContext {
  language: string;                      // Current language
  current_intent?: string;               // Active intent
  workflow_state?: string;               // Current workflow state
  user_preferences?: UserPreferences;    // User settings
}

interface UserPreferences {
  notification_enabled: boolean;
  preferred_language: string;
  timezone: string;
}
```

### Pending Task Format
```typescript
interface PendingTask {
  task_id: string;                       // Unique task identifier
  task_type: string;                     // Type of task
  status: TaskStatus;                    // Current status
  created_at: string;                    // ISO 8601 timestamp
  data?: Record<string, any>;            // Task-specific data
}

type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';
```

## Admin Dashboard Formats

### Metrics Data Format
```typescript
interface MetricsData {
  active_sessions: number;               // Current active sessions
  total_messages_processed: number;     // Cumulative message count
  llm_provider: string;                  // Primary LLM provider
  fallback_provider: string;             // Backup LLM provider
  uptime_seconds: number;                // Service uptime
  intent_distribution: Record<string, number>; // Intent percentages
  response_times: ResponseTimeMetrics;   // Performance metrics
  error_rates: ErrorRateMetrics;         // Error statistics
}
```

### Response Time Metrics
```typescript
interface ResponseTimeMetrics {
  avg_ms: number;                        // Average response time
  p95_ms: number;                        // 95th percentile
  p99_ms: number;                        // 99th percentile
  min_ms: number;                        // Minimum response time
  max_ms: number;                        // Maximum response time
}
```

### Error Rate Metrics
```typescript
interface ErrorRateMetrics {
  llm_provider_errors: number;           // LLM provider error rate (0-1)
  session_errors: number;                // Session error rate (0-1)
  agent_timeouts: number;                // Agent timeout rate (0-1)
  total_errors: number;                  // Total error count
}
```

## Error Response Formats

### Standard Error Response
```typescript
interface ApiError {
  detail: string;                        // Human-readable error message
  error_code?: string;                   // Machine-readable error code
  timestamp?: string;                    // ISO 8601 timestamp
  field_errors?: FieldError[];           // Validation errors
}

interface FieldError {
  field: string;                         // Field name
  message: string;                       // Error message
  code: string;                          // Error code
}
```

**Example:**
```json
{
  "detail": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z",
  "field_errors": [
    {
      "field": "message",
      "message": "Message cannot be empty",
      "code": "REQUIRED"
    }
  ]
}
```

## WebSocket Message Formats (Future)

### WebSocket Connection
```typescript
interface WebSocketMessage {
  type: MessageType;                     // Message type
  data: any;                            // Message payload
  timestamp: string;                     // ISO 8601 timestamp
  correlation_id?: string;               // Request correlation
}

type MessageType = 'message' | 'typing' | 'status' | 'error';
```

### Real-time Chat Message
```typescript
interface RealtimeChatMessage {
  type: 'message';
  data: {
    session_id: string;
    message: ConversationMessage;
  };
  timestamp: string;
}
```

### Typing Indicator
```typescript
interface TypingIndicator {
  type: 'typing';
  data: {
    session_id: string;
    user_id: string;
    is_typing: boolean;
  };
  timestamp: string;
}
```

## Data Validation Standards

### Input Validation Rules

#### Message Content
- **Maximum Length**: 2000 characters
- **Minimum Length**: 1 character
- **Allowed Characters**: Unicode text, basic punctuation
- **Prohibited Content**: HTML tags, script content

#### User Identifiers
- **Format**: Alphanumeric with underscores and hyphens
- **Length**: 3-50 characters
- **Pattern**: `^[a-zA-Z0-9_-]+$`

#### Session IDs
- **Format**: UUID v4
- **Pattern**: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`

#### Timestamps
- **Format**: ISO 8601 with UTC timezone
- **Pattern**: `YYYY-MM-DDTHH:mm:ss.sssZ`
- **Example**: `2024-01-15T10:30:00.123Z`

### Response Validation

#### Required Fields
All API responses must include:
- Appropriate HTTP status code
- Content-Type header
- Timestamp field
- Correlation ID for tracking

#### Optional Fields
- Rate limiting headers
- Cache control headers
- Custom application headers

## Security Standards

### Token Format
```typescript
interface JWTPayload {
  sub: string;                           // Subject (user ID)
  email: string;                         // User email
  role: string;                          // User role
  iat: number;                          // Issued at timestamp
  exp: number;                          // Expiration timestamp
  iss: string;                          // Issuer
  aud: string;                          // Audience
}
```

### Request Signing (Future)
```typescript
interface SignedRequest {
  payload: any;                          // Request payload
  signature: string;                     // HMAC signature
  timestamp: number;                     // Unix timestamp
  nonce: string;                         // Unique request identifier
}
```

## Rate Limiting Formats

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
X-RateLimit-Window: 60
```

### Rate Limit Error Response
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60,
  "limit": 60,
  "window": 60
}
```

## Internationalization Formats

### Language Codes
- **English**: `en`
- **Indonesian**: `id`
- **Format**: ISO 639-1 two-letter codes

### Localized Messages
```typescript
interface LocalizedMessage {
  key: string;                           // Message key
  default: string;                       // Default text
  translations: Record<string, string>;  // Language translations
}
```

**Example:**
```json
{
  "key": "welcome_message",
  "default": "Welcome to PV Chatbot",
  "translations": {
    "en": "Welcome to PV Chatbot",
    "id": "Selamat datang di PV Chatbot"
  }
}
```

## Monitoring and Logging Formats

### Log Entry Format
```typescript
interface LogEntry {
  timestamp: string;                     // ISO 8601 timestamp
  level: LogLevel;                       // Log level
  message: string;                       // Log message
  context: Record<string, any>;          // Additional context
  correlation_id?: string;               // Request correlation
  user_id?: string;                      // User identifier
  session_id?: string;                   // Session identifier
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';
```

### Performance Metrics Format
```typescript
interface PerformanceMetric {
  name: string;                          // Metric name
  value: number;                         // Metric value
  unit: string;                          // Unit of measurement
  timestamp: string;                     // ISO 8601 timestamp
  tags: Record<string, string>;          // Metric tags
}
```

This comprehensive messaging format specification ensures consistent, secure, and maintainable communication across all components of the PV Chatbot system.
