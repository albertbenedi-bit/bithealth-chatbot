import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '../../auth/AuthContext';
import { ChatSidebar } from './ChatSidebar';
import { ChatArea } from './ChatArea';
import { SessionData } from '../../types/api';
import { apiService } from '../../services/api';

export function ChatLayout() {
  const { authState } = useAuth();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [currentSession, setCurrentSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(false);

  const handleNewChat = useCallback(() => {
    const newSessionId = uuidv4();
    const newSession: SessionData = {
      session_id: newSessionId,
      user_id: authState.user?.id || '',
      created_at: new Date().toISOString(),
      last_activity: new Date().toISOString(),
      conversation_history: [
        {
          timestamp: new Date().toISOString(),
          role: 'assistant',
          content: 'Hello! I am your healthcare assistant. How can I help you today?',
          metadata: { status: 'completed' }
        }
      ],
      context: { language: 'en' },
      pending_tasks: [],
    };
    setCurrentSession(newSession);
    setCurrentSessionId(newSessionId);
    setSessions(prev => [newSession, ...prev]);
  }, [authState.user?.id]);

  // Automatically create a new session on initial load if none exists.
  useEffect(() => {
    if (!currentSessionId && !loading) {
      handleNewChat();
    }
  }, [currentSessionId, loading, handleNewChat]);

  const handleSelectSession = useCallback(async (sessionId: string) => {
    if (sessionId === currentSessionId) return;
    
    setLoading(true);
    try {
      const sessionData = await apiService.getSession(sessionId);
      setCurrentSession(sessionData);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
      // If a session fails to load (e.g., 404 Not Found), remove it from the sidebar.
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      // If the failed session was the current one, clear the main view.
      if (currentSessionId === sessionId) {
        setCurrentSession(null);
        setCurrentSessionId(null);
      }
    } finally {
      setLoading(false);
    }
  }, [currentSessionId]);

  const handleSessionUpdate = useCallback((sessionData: SessionData) => {
    setCurrentSession(sessionData);
    setCurrentSessionId(sessionData.session_id);
    
    setSessions(prev => {
      const existingIndex = prev.findIndex(s => s.session_id === sessionData.session_id);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = sessionData;
        // Sort by last activity to move the most recent session to the top
        return updated.sort((a, b) => 
          new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime());
      } else {
        return [sessionData, ...prev];
      }
    });
  }, []);

  return (
    <div className="flex h-screen bg-gray-50">
      <ChatSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        loading={loading}
      />
      <ChatArea
        session={currentSession}
        userId={authState.user?.id || ''}
        onSessionUpdate={handleSessionUpdate}
        loading={loading}
      />
    </div>
  );
}
