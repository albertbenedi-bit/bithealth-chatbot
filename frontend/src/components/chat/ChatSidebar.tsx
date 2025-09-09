import { useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { 
  MessageSquarePlus, 
  MessageSquare, 
  LogOut, 
  Settings, 
  Shield,
  User,
  Clock
} from 'lucide-react';
import { SessionData } from '../../types/api';
import { formatDistanceToNow } from 'date-fns';

interface ChatSidebarProps {
  sessions: SessionData[];
  currentSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  loading: boolean;
}

export function ChatSidebar({ 
  sessions, 
  currentSessionId, 
  onNewChat, 
  onSelectSession,
  loading 
}: ChatSidebarProps) {
  const { authState, logout } = useAuth();
  const [showSettings, setShowSettings] = useState(false);

  const getSessionPreview = (session: SessionData) => {
    const lastMessage = session.conversation_history[session.conversation_history.length - 1];
    if (!lastMessage) return 'New conversation';
    
    const preview = lastMessage.role === 'user' 
      ? lastMessage.content 
      : `Assistant: ${lastMessage.content}`;
    
    return preview.length > 50 ? preview.substring(0, 50) + '...' : preview;
  };

  const getSessionTitle = (session: SessionData) => {
    const firstUserMessage = session.conversation_history.find(msg => msg.role === 'user');
    if (!firstUserMessage) return 'New Chat';
    
    const title = firstUserMessage.content;
    return title.length > 30 ? title.substring(0, 30) + '...' : title;
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-blue-100 text-blue-600">
                {authState.user?.name?.charAt(0).toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {authState.user?.name || 'User'}
              </p>
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                {authState.user?.role === 'admin' ? (
                  <Shield className="h-3 w-3" />
                ) : (
                  <User className="h-3 w-3" />
                )}
                <span className="capitalize">{authState.user?.role}</span>
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>

        {showSettings && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg space-y-2">
            <div className="text-xs text-gray-600">
              <p>Email: {authState.user?.email}</p>
              {authState.user?.department && (
                <p>Department: {authState.user.department}</p>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="w-full flex items-center space-x-2"
            >
              <LogOut className="h-3 w-3" />
              <span>Sign Out</span>
            </Button>
          </div>
        )}

        <Button
          onClick={onNewChat}
          className="w-full flex items-center space-x-2"
          disabled={loading}
        >
          <MessageSquarePlus className="h-4 w-4" />
          <span>New Chat</span>
        </Button>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Conversations</h3>
        </div>
        
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-2">
            {sessions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs">Start a new chat to begin</p>
              </div>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => onSelectSession(session.session_id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    currentSessionId === session.session_id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <MessageSquare className="h-4 w-4 mt-1 text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {getSessionTitle(session)}
                      </p>
                      <p className="text-xs text-gray-500 truncate mt-1">
                        {getSessionPreview(session)}
                      </p>
                      <div className="flex items-center space-x-1 mt-2 text-xs text-gray-400">
                        <Clock className="h-3 w-3" />
                        <span>
                          {formatDistanceToNow(new Date(session.last_activity), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
