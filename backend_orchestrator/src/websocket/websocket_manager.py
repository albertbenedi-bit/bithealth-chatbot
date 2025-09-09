import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()

class WebSocketManager:
    """Manages WebSocket connections for real-time communication with frontend clients"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept a WebSocket connection and store it by session_id"""
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket
            logger.info("WebSocket connection established", session_id=session_id)
        except Exception as e:
            logger.error("Failed to establish WebSocket connection", session_id=session_id, error=str(e))
            raise
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info("WebSocket connection closed", session_id=session_id)
    
    async def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific session's WebSocket connection"""
        if session_id not in self.active_connections:
            logger.warning("No active WebSocket connection for session", session_id=session_id)
            return False
        
        websocket = self.active_connections[session_id]
        try:
            await websocket.send_text(json.dumps(message))
            logger.debug("Message sent via WebSocket", session_id=session_id, message_type=message.get("type"))
            return True
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected while sending message", session_id=session_id)
            self.disconnect(session_id)
            return False
        except Exception as e:
            logger.error("Failed to send WebSocket message", session_id=session_id, error=str(e))
            self.disconnect(session_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all active WebSocket connections"""
        if not self.active_connections:
            logger.debug("No active WebSocket connections for broadcast")
            return
        
        disconnected_sessions = []
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during broadcast", session_id=session_id)
                disconnected_sessions.append(session_id)
            except Exception as e:
                logger.error("Failed to broadcast to WebSocket", session_id=session_id, error=str(e))
                disconnected_sessions.append(session_id)
        
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
        
        logger.debug("Broadcast completed", active_connections=len(self.active_connections))
    
    def get_active_connections_count(self) -> int:
        """Get the number of active WebSocket connections"""
        return len(self.active_connections)
    
    def is_connected(self, session_id: str) -> bool:
        """Check if a session has an active WebSocket connection"""
        return session_id in self.active_connections
