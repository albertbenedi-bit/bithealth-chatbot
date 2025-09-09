export interface User {
  id: string;
  email: string;
  name: string;
  role: 'patient' | 'staff' | 'admin';
  department?: string;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  session_id?: string;
  context?: {
    language?: 'en' | 'id';
    user_type?: 'patient' | 'staff';
    department?: string;
    priority?: 'low' | 'normal' | 'high';
  };
}

export interface ChatResponse {
  response: string;
  session_id: string;
  intent: string;
  requires_human_handoff: boolean;
  suggested_actions: string[];
  confidence_score: number;
  processing_time_ms: number;
  correlation_id?: string;
}

// export interface ConversationMessage {
//   timestamp: string;
//   role: 'user' | 'assistant' | 'system';
//   content: string;
//   metadata?: {
//     intent?: string;
//     confidence?: number;
//   };
// }
export interface ConversationMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    intent?: string;
    confidence?: number;
    correlation_id?: string; // Add this
    status?: 'pending' | 'completed' | 'error'; // Add this for UI
  };
}

export interface SessionData {
  session_id: string;
  user_id: string;
  created_at: string;
  last_activity: string;
  conversation_history: ConversationMessage[];
  context: {
    language: string;
    current_intent?: string;
    workflow_state?: string;
  };
  pending_tasks: Array<{
    task_id: string;
    task_type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at: string;
  }>;
}

export interface MetricsData {
  active_sessions: number;
  total_messages_processed: number;
  llm_provider: string;
  fallback_provider: string;
  uptime_seconds: number;
  intent_distribution: Record<string, number>;
  response_times: {
    avg_ms: number;
    p95_ms: number;
    p99_ms: number;
  };
  error_rates: {
    llm_provider_errors: number;
    session_errors: number;
    agent_timeouts: number;
  };
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  timestamp: string;
  version: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface WebSocketMessage {
  type: 'final_response' | 'typing' | 'status' | 'error';
  data: object;
  timestamp: string;
  correlation_id?: string;
}

export interface FinalResponseMessage {
  type: 'final_response';
  data: {
    session_id: string;
    response: string;
    intent?: string;
    requires_human_handoff: boolean;
    suggested_actions: string[];
    correlation_id?: string;
  };
  timestamp: string;
}
