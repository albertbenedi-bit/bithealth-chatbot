import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Alert, AlertDescription } from '../ui/alert';
import { Avatar, AvatarFallback } from '../ui/avatar';
import {
  Send,
  Loader2,
  AlertTriangle,
  User,
  Bot,
  Clock,
  CheckCircle,
} from 'lucide-react';
import type { SessionData, ConversationMessage, ChatRequest, WebSocketMessage, FinalResponseMessage } from '../../types/api';
import { apiService } from '../../services/api';
import { websocketService } from '../../services/websocket.js';
import { formatDistanceToNow } from 'date-fns';

interface ChatAreaProps {
  session: SessionData | null;
  userId: string;
  onSessionUpdate: (session: SessionData) => void;
  loading: boolean;
}

export function ChatArea({ session, userId, onSessionUpdate, loading }: ChatAreaProps) {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.conversation_history]);

  useEffect(() => {
    if (!loading && !sending) {
      inputRef.current?.focus();
    }
  }, [loading, sending]);

  // This ref will always hold the latest session object, preventing stale closures
  const sessionRef = useRef(session);
  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  const handleFinalResponse = useCallback((message: WebSocketMessage) => {
    const currentSession = sessionRef.current;
    if (message.type !== 'final_response' || !currentSession) {
      return;
    }

    const finalResponse = message as FinalResponseMessage;
    const { data } = finalResponse;

    console.log('Received final_response via WebSocket:', finalResponse, 'for session:', currentSession.session_id);

    // Use .map for a guaranteed immutable update, which is safer for React state.
    const updatedHistory = currentSession.conversation_history.map(msg => {
      if (msg.role === 'assistant' && msg.metadata?.correlation_id === data.correlation_id) {
        // Found the message to update. Return a new object.
        return {
          ...msg,
          content: data.response,
          timestamp: finalResponse.timestamp, // Use the new timestamp from the backend
          metadata: { ...msg.metadata, status: 'completed' as const, intent: data.intent },
        };
      }
      // Return all other messages unchanged.
      return msg;
    });

    const updatedSession: SessionData = {
      ...currentSession,
      conversation_history: updatedHistory,
      last_activity: new Date().toISOString(),
      context: {
        ...currentSession.context,
        current_intent: data.intent,
      },
    };

    onSessionUpdate(updatedSession);

    if (data.requires_human_handoff && currentSession.session_id === data.session_id) {
      setError('This conversation requires human assistance. A staff member will be notified.');
    }
  }, [onSessionUpdate, setError]);

  useEffect(() => {
    // This effect manages the WebSocket connection for the active session.
    if (!session?.session_id) {
      // If there's no session, ensure we are disconnected.
      websocketService.disconnect();
      setWsConnected(false);
      return;
    }

    // Connect and subscribe
    websocketService.connect(session.session_id).then(() => {
      setWsConnected(true);
      console.log(`WebSocket connected for session: ${session.session_id}`);
    }).catch(err => {
      console.error('WebSocket connection failed:', err);
      setError('Failed to establish real-time connection.');
    });

    const unsubscribe = websocketService.onMessage(handleFinalResponse);

    // Cleanup function: This runs when the component unmounts or dependencies change.
    return () => {
      console.log(`Cleaning up WebSocket for session: ${session.session_id}`);
      unsubscribe();
      websocketService.disconnect();
      setWsConnected(false);
    };
  }, [session?.session_id, handleFinalResponse]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sending || !session) return;

    const userMessage = message.trim();
    setMessage('');
    setSending(true);
    setError(null);

    try {
      const request: ChatRequest = {
        user_id: userId,
        message: userMessage,
        session_id: session.session_id,
        context: { 
          ...session.context, 
          language: 'en', 
          user_type: 'patient' 
        },
      };

      const response = await apiService.sendMessage(request);

      console.log('API service initial response:', response);

      const newHistory: ConversationMessage[] = [
        ...session.conversation_history,
        {
          timestamp: new Date().toISOString(),
          role: 'user',
          content: userMessage,
        },
        {
          timestamp: new Date().toISOString(),
          role: 'assistant',
          content: response.response, // Initial response content
          metadata: {
            intent: response.intent,
            confidence: response.confidence_score,
            correlation_id: response.correlation_id,
            status: 'pending', // Mark as pending
          },
        },
      ];

      const updatedSession: SessionData = {
        ...session,
        session_id: response.session_id, // The backend confirms/returns the session_id
        last_activity: new Date().toISOString(),
        conversation_history: newHistory,
        context: { ...session.context, current_intent: response.intent },
      };

      onSessionUpdate(updatedSession);

      if (response.requires_human_handoff) {
        setError('This conversation requires human assistance. A staff member will be notified.');
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const renderMessage = (msg: ConversationMessage, index: number) => {
    const isUser = msg.role === 'user';
    const isSystem = msg.role === 'system';
    const isAssistant = msg.role === 'assistant';
    const isAssistantPending = isAssistant && msg.metadata?.status === 'pending';
    const isAssistantError = isAssistant && msg.metadata?.status === 'error';
    // Make the key unique based on status to force a re-render on update.
    const messageKey = `${msg.metadata?.correlation_id || msg.timestamp}-${msg.metadata?.status || 'completed'}-${index}`;

    return (
      <div
        key={messageKey} // This key will now change when the status changes
        className={`flex items-start space-x-3 ${
          isUser ? 'flex-row-reverse space-x-reverse' : ''
        } mb-4`}
      >
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className={isUser ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </AvatarFallback>
        </Avatar>

        <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
          <div
            className={`inline-block max-w-[80%] p-3 rounded-lg ${
              isUser
                ? 'bg-blue-600 text-white'
                : isSystem
                ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            {/* Always display the content of the message */}
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

            {/* Display additional info and loader for pending assistant messages */}
            {isAssistantPending && (
              <div className="mt-2 text-xs opacity-75 text-gray-600">
                {msg.metadata?.intent && (
                  <span className="inline-flex items-center space-x-1 mb-1">
                    <CheckCircle className="h-3 w-3" />
                    <span>Intent: {msg.metadata.intent}</span>
                    {msg.metadata.confidence !== undefined && (
                      <span>({Math.round(msg.metadata.confidence * 100)}%)</span>
                    )}
                  </span>
                )}
                {msg.metadata?.correlation_id && ( // Display correlation_id if available
                  <div className="mb-1">
                    <span className="inline-flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>ID: {msg.metadata.correlation_id.substring(0, 8)}...</span> {/* Truncate for display */}
                    </span>
                  </div>
                )}
                <div className="flex items-center space-x-1 mt-1">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Processing...</span>
                </div>
              </div>
            )}

            {/* Show intent/confidence only for completed assistant messages */}
            {isAssistant && !isAssistantPending && !isAssistantError && msg.metadata?.intent && (
              <div className="mt-2 text-xs opacity-75">
                <span className="inline-flex items-center space-x-1">
                  <CheckCircle className="h-3 w-3" />
                  <span>Intent: {msg.metadata.intent}</span>
                  {msg.metadata.confidence !== undefined && (
                    <span>({Math.round(msg.metadata.confidence * 100)}%)</span>
                  )}
                </span>
              </div>
            )}
          </div>

          <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : ''}`}>
            <span className="inline-flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true })}</span>
            </span>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-600" />
          <p className="text-gray-600">Loading conversation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {!session ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <Bot className="h-16 w-16 mx-auto text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Welcome to PV Chatbot</h2>
            <p className="text-gray-600">
              Your healthcare assistant for appointment management, information, and support.
            </p>
            <div className="text-sm text-gray-500 space-y-1">
              <p>• Schedule, reschedule, or cancel appointments</p>
              <p>• Get pre-admission and post-discharge information</p>
              <p>• Ask questions about hospital services</p>
              <p>• Receive personalized healthcare guidance</p>
            </div>
            <p className="text-sm text-blue-600 font-medium">
              Start a conversation by typing a message below
            </p>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          <div className="border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Healthcare Assistant
                </h3>
                <p className="text-sm text-gray-500">
                  Session started {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                </p>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <CheckCircle className={`h-4 w-4 ${wsConnected ? 'text-green-500' : 'text-yellow-500'}`} />
                <span>{wsConnected ? 'Connected' : 'Connecting...'}</span>
              </div>
            </div>
          </div>

          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {session.conversation_history.map((msg, index) => renderMessage(msg, index))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>
      )}

      <div className="border-t border-gray-200 p-4">
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <Input
            ref={inputRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here..."
            disabled={sending}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!message.trim() || sending}
            className="px-6"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        <div className="mt-2 text-xs text-gray-500 text-center">
          <p>This chatbot provides information only and does not replace professional medical advice.</p>
        </div>
      </div>
    </div>
  );
}