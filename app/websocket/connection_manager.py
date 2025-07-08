from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.core.security import verify_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.chat import WebSocketMessage, TypingIndicator, MessageDelivery, OnlineStatus
import uuid
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """
    WebSocket connection manager for real-time chat features.
    
    Manages WebSocket connections, user presence, and message broadcasting.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        # Active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[uuid.UUID, Dict[str, WebSocket]] = {}
        
        # Chat room connections: {chat_id: {user_id}}
        self.chat_rooms: Dict[uuid.UUID, Set[uuid.UUID]] = {}
        
        # Typing indicators: {chat_id: {user_id: timestamp}}
        self.typing_users: Dict[uuid.UUID, Dict[uuid.UUID, datetime]] = {}
        
        # User presence: {user_id: last_seen}
        self.user_presence: Dict[uuid.UUID, datetime] = {}
    
    async def connect(self, websocket: WebSocket, user: User) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket (WebSocket): WebSocket connection
            user (User): Authenticated user
            
        Returns:
            str: Connection ID
        """
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = str(uuid.uuid4())
        
        # Add to active connections
        if user.id not in self.active_connections:
            self.active_connections[user.id] = {}
        
        self.active_connections[user.id][connection_id] = websocket
        
        # Update user presence
        self.user_presence[user.id] = datetime.utcnow()
        
        # Broadcast user online status
        await self.broadcast_user_status(user.id, True)
        
        return connection_id
    
    async def disconnect(self, user_id: uuid.UUID, connection_id: str):
        """
        Handle WebSocket disconnection.
        
        Args:
            user_id (uuid.UUID): User ID
            connection_id (str): Connection ID
        """
        # Remove from active connections
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            
            # If no more connections for this user
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Remove from chat rooms
                for chat_id in list(self.chat_rooms.keys()):
                    self.chat_rooms[chat_id].discard(user_id)
                    if not self.chat_rooms[chat_id]:
                        del self.chat_rooms[chat_id]
                
                # Remove from typing indicators
                for chat_id in list(self.typing_users.keys()):
                    self.typing_users[chat_id].pop(user_id, None)
                    if not self.typing_users[chat_id]:
                        del self.typing_users[chat_id]
                
                # Update presence and broadcast offline status
                self.user_presence[user_id] = datetime.utcnow()
                await self.broadcast_user_status(user_id, False)
    
    async def join_chat_room(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        """
        Join a user to a chat room.
        
        Args:
            user_id (uuid.UUID): User ID
            chat_id (uuid.UUID): Chat ID
        """
        if chat_id not in self.chat_rooms:
            self.chat_rooms[chat_id] = set()
        
        self.chat_rooms[chat_id].add(user_id)
    
    async def leave_chat_room(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        """
        Remove a user from a chat room.
        
        Args:
            user_id (uuid.UUID): User ID
            chat_id (uuid.UUID): Chat ID
        """
        if chat_id in self.chat_rooms:
            self.chat_rooms[chat_id].discard(user_id)
            if not self.chat_rooms[chat_id]:
                del self.chat_rooms[chat_id]
    
    async def send_personal_message(self, user_id: uuid.UUID, message: dict):
        """
        Send a message to a specific user.
        
        Args:
            user_id (uuid.UUID): User ID
            message (dict): Message to send
        """
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                await self.disconnect(user_id, connection_id)
    
    async def broadcast_to_chat(self, chat_id: uuid.UUID, message: dict, exclude_user: Optional[uuid.UUID] = None):
        """
        Broadcast a message to all users in a chat room.
        
        Args:
            chat_id (uuid.UUID): Chat ID
            message (dict): Message to broadcast
            exclude_user (Optional[uuid.UUID]): User ID to exclude from broadcast
        """
        if chat_id not in self.chat_rooms:
            return
        
        tasks = []
        for user_id in self.chat_rooms[chat_id]:
            if exclude_user and user_id == exclude_user:
                continue
            
            if user_id in self.active_connections:
                tasks.append(self.send_personal_message(user_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_user_status(self, user_id: uuid.UUID, is_online: bool):
        """
        Broadcast user online status to relevant users.
        
        Args:
            user_id (uuid.UUID): User ID
            is_online (bool): Online status
        """
        message = {
            "type": "user_status",
            "data": {
                "user_id": str(user_id),
                "is_online": is_online,
                "last_seen": self.user_presence.get(user_id).isoformat() if user_id in self.user_presence else None
            }
        }
        
        # Find all users who share chats with this user
        affected_users = set()
        for chat_id, users in self.chat_rooms.items():
            if user_id in users:
                affected_users.update(users)
        
        # Remove the user themselves
        affected_users.discard(user_id)
        
        # Send status update to affected users
        tasks = []
        for affected_user_id in affected_users:
            if affected_user_id in self.active_connections:
                tasks.append(self.send_personal_message(affected_user_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_typing_indicator(self, chat_id: uuid.UUID, user_id: uuid.UUID, is_typing: bool):
        """
        Handle typing indicator updates.
        
        Args:
            chat_id (uuid.UUID): Chat ID
            user_id (uuid.UUID): User ID
            is_typing (bool): Whether user is typing
        """
        if chat_id not in self.typing_users:
            self.typing_users[chat_id] = {}
        
        if is_typing:
            self.typing_users[chat_id][user_id] = datetime.utcnow()
        else:
            self.typing_users[chat_id].pop(user_id, None)
            if not self.typing_users[chat_id]:
                del self.typing_users[chat_id]
        
        # Broadcast typing indicator to other users in the chat
        message = {
            "type": "typing_indicator",
            "data": {
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "is_typing": is_typing
            }
        }
        
        await self.broadcast_to_chat(chat_id, message, exclude_user=user_id)
    
    async def handle_message_delivery(self, message_id: uuid.UUID, recipient_ids: List[uuid.UUID]):
        """
        Handle message delivery confirmation.
        
        Args:
            message_id (uuid.UUID): Message ID
            recipient_ids (List[uuid.UUID]): List of recipient user IDs
        """
        delivery_time = datetime.utcnow()
        
        message = {
            "type": "message_delivered",
            "data": {
                "message_id": str(message_id),
                "delivered_at": delivery_time.isoformat()
            }
        }
        
        # Send delivery confirmation to online recipients
        tasks = []
        for user_id in recipient_ids:
            if user_id in self.active_connections:
                tasks.append(self.send_personal_message(user_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_message_read(self, message_id: uuid.UUID, chat_id: uuid.UUID, user_id: uuid.UUID):
        """
        Handle message read confirmation.
        
        Args:
            message_id (uuid.UUID): Message ID
            chat_id (uuid.UUID): Chat ID
            user_id (uuid.UUID): User who read the message
        """
        read_time = datetime.utcnow()
        
        message = {
            "type": "message_read",
            "data": {
                "message_id": str(message_id),
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "read_at": read_time.isoformat()
            }
        }
        
        # Broadcast read receipt to other users in the chat
        await self.broadcast_to_chat(chat_id, message, exclude_user=user_id)
    
    def is_user_online(self, user_id: uuid.UUID) -> bool:
        """
        Check if a user is currently online.
        
        Args:
            user_id (uuid.UUID): User ID
            
        Returns:
            bool: True if user is online
        """
        return user_id in self.active_connections
    
    def get_online_users_in_chat(self, chat_id: uuid.UUID) -> List[uuid.UUID]:
        """
        Get list of online users in a chat.
        
        Args:
            chat_id (uuid.UUID): Chat ID
            
        Returns:
            List[uuid.UUID]: List of online user IDs
        """
        if chat_id not in self.chat_rooms:
            return []
        
        return [user_id for user_id in self.chat_rooms[chat_id] if self.is_user_online(user_id)]
    
    async def cleanup_typing_indicators(self):
        """Clean up old typing indicators (called periodically)."""
        current_time = datetime.utcnow()
        
        for chat_id in list(self.typing_users.keys()):
            for user_id in list(self.typing_users[chat_id].keys()):
                typing_time = self.typing_users[chat_id][user_id]
                # Remove typing indicator if older than 10 seconds
                if (current_time - typing_time).total_seconds() > 10:
                    del self.typing_users[chat_id][user_id]
                    
                    # Broadcast typing stopped
                    message = {
                        "type": "typing_indicator",
                        "data": {
                            "chat_id": str(chat_id),
                            "user_id": str(user_id),
                            "is_typing": False
                        }
                    }
                    await self.broadcast_to_chat(chat_id, message, exclude_user=user_id)
            
            # Clean up empty chat typing data
            if not self.typing_users[chat_id]:
                del self.typing_users[chat_id]


# Global connection manager instance
connection_manager = ConnectionManager()
