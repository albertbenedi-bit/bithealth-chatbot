import redis.asyncio as redis
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import structlog

logger = structlog.get_logger()

class SessionManager:
    """Manages user conversation sessions using Redis"""
    
    def __init__(self, redis_url: str, session_ttl: int = 3600):
        self.redis_url = redis_url
        self.session_ttl = session_ttl  # Session TTL in seconds (1 hour default)
        self.redis_client = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Session manager initialized", redis_url=self.redis_url)
        except Exception as e:
            logger.error("Failed to initialize session manager", error=str(e))
            raise
    
    async def create_session(self, user_id: str, initial_context: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> str:
        """Create a new conversation session, using the provided session_id if available."""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.debug("No session_id provided, generating new one.", new_session_id=session_id)
            else:
                logger.debug("Using client-provided session_id.", session_id=session_id)
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "conversation_history": [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "role": "assistant",
                        "content": "Hello! I am your healthcare assistant. How can I help you today?",
                        "metadata": {"status": "completed"}
                    }
                ],
                "context": initial_context or {},
                "current_intent": None,
                "workflow_state": "initial",
                "pending_tasks": []
            }
            
            session_key = f"session:{session_id}"
            await self.redis_client.setex(
                session_key, 
                self.session_ttl, 
                json.dumps(session_data)
            )
            
            user_sessions_key = f"user_sessions:{user_id}"
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, self.session_ttl)
            
            logger.info("Session created", session_id=session_id, user_id=user_id)
            return session_id
            
        except Exception as e:
            logger.error("Failed to create session", user_id=user_id, error=str(e))
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        try:
            session_key = f"session:{session_id}"
            session_data_bytes = await self.redis_client.get(session_key)
            
            if not session_data_bytes:
                return None
            
            return json.loads(session_data_bytes)

        except json.JSONDecodeError as e:
            logger.error("Failed to decode session data from Redis", session_id=session_id, error=str(e))
            # Corrupted data in Redis is a server error.
            raise ValueError(f"Corrupted session data for {session_id}") from e
        except Exception as e:
            logger.error("Failed to get session from Redis", session_id=session_id, error=str(e))
            # Re-raise to indicate a backend/service dependency problem
            raise
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            session_data.update(updates)
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            session_key = f"session:{session_id}"
            await self.redis_client.setex(
                session_key, 
                self.session_ttl, 
                json.dumps(session_data)
            )
            
            logger.debug("Session updated", session_id=session_id)
            
        except Exception as e:
            logger.error("Failed to update session", session_id=session_id, error=str(e))
            raise
    
    async def add_message_to_history(self, session_id: str, role: str, content: str, 
                                   metadata: Optional[Dict[str, Any]] = None):
        """Add a message to conversation history"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            message = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": role,  # user, assistant, system
                "content": content,
                "metadata": metadata or {}
            }
            
            session_data["conversation_history"].append(message)
            
            if len(session_data["conversation_history"]) > 50:
                session_data["conversation_history"] = session_data["conversation_history"][-50:]
            
            await self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error("Failed to add message to history", 
                        session_id=session_id, error=str(e))
            raise

    async def update_message_by_correlation_id(self, session_id: str, correlation_id: str, new_content: str):
        """Finds a message by its correlation_id in metadata and updates its content."""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                logger.warning("Attempted to update message in a non-existent session.", session_id=session_id)
                return

            history = session_data.get("conversation_history", [])
            message_found = False
            for message in history:
                if message.get("metadata", {}).get("correlation_id") == correlation_id:
                    logger.debug("Found message to update by correlation_id", session_id=session_id, correlation_id=correlation_id)
                    message["content"] = new_content
                    message["timestamp"] = datetime.now(timezone.utc).isoformat()
                    if "metadata" in message:
                        message["metadata"]["status"] = "completed"
                    message_found = True
                    break
            
            if message_found:
                session_data["conversation_history"] = history
                await self.update_session(session_id, session_data)
            else:
                logger.warning("Could not find message with matching correlation_id to update.", session_id=session_id, correlation_id=correlation_id)

        except Exception as e:
            logger.error("Failed to update message by correlation_id", session_id=session_id, correlation_id=correlation_id, error=str(e))
    
    async def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return []
            
            history = session_data.get("conversation_history", [])
            if limit:
                history = history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error("Failed to get conversation history", 
                        session_id=session_id, error=str(e))
            return []
    
    async def clear_session(self, session_id: str):
        """Clear/delete a session"""
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                user_id = session_data["user_id"]
                
                user_sessions_key = f"user_sessions:{user_id}"
                await self.redis_client.srem(user_sessions_key, session_id)
            
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)
            
            logger.info("Session cleared", session_id=session_id)
            
        except Exception as e:
            logger.error("Failed to clear session", session_id=session_id, error=str(e))
            raise
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            sessions = await self.redis_client.smembers(user_sessions_key)
            return [s.decode() for s in sessions] if sessions else []
            
        except Exception as e:
            logger.error("Failed to get user sessions", user_id=user_id, error=str(e))
            return []
    
    async def get_active_session_count(self) -> int:
        """Get total number of active sessions"""
        try:
            pattern = "session:*"
            keys = await self.redis_client.keys(pattern)
            return len(keys)
            
        except Exception as e:
            logger.error("Failed to get active session count", error=str(e))
            return 0
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (called periodically)"""
        try:
            pattern = "user_sessions:*"
            user_session_keys = await self.redis_client.keys(pattern)
            
            for key in user_session_keys:
                session_ids = await self.redis_client.smembers(key)
                valid_sessions = []
                
                for session_id in session_ids:
                    session_key = f"session:{session_id.decode()}"
                    if await self.redis_client.exists(session_key):
                        valid_sessions.append(session_id)
                
                if valid_sessions:
                    await self.redis_client.delete(key)
                    await self.redis_client.sadd(key, *valid_sessions)
                else:
                    await self.redis_client.delete(key)
            
            logger.info("Session cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup expired sessions", error=str(e))
