from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.repositories.user_repository import UserRepository
from app.websocket.connection_manager import connection_manager
from app.schemas.chat import TypingIndicator, MessageDelivery
import json
import uuid
import asyncio
from typing import Optional


async def get_current_user_websocket(websocket: WebSocket, token: str = Query(...), 
                                   db: Session = Depends(get_db)):
    """
    Authenticate user for WebSocket connection.
    
    Args:
        websocket (WebSocket): WebSocket connection
        token (str): JWT token
        db (Session): Database session
        
    Returns:
        User: Authenticated user
        
    Raises:
        WebSocketException: If authentication fails
    """
    try:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return None
        
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(uuid.UUID(user_id))
        
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="User not found or inactive")
            return None
        
        return user
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return None


async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Main WebSocket endpoint for real-time chat communication.
    
    Args:
        websocket (WebSocket): WebSocket connection
        db (Session): Database session
    """
    # Authenticate user
    user = await get_current_user_websocket(websocket, db=db)
    if not user:
        return
    
    connection_id = None
    
    try:
        # Connect user
        connection_id = await connection_manager.connect(websocket, user)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "user_id": str(user.id),
                "connection_id": connection_id
            }
        }))
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await handle_websocket_message(message_data, user.id, db)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Send error for invalid JSON
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }))
            except Exception as e:
                # Send error for other exceptions
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": str(e)}
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up connection
        if connection_id:
            await connection_manager.disconnect(user.id, connection_id)


async def handle_websocket_message(message_data: dict, user_id: uuid.UUID, db: Session):
    """
    Handle incoming WebSocket messages.
    
    Args:
        message_data (dict): Message data from client
        user_id (uuid.UUID): Authenticated user ID
        db (Session): Database session
    """
    message_type = message_data.get("type")
    data = message_data.get("data", {})
    
    if message_type == "join_chat":
        await handle_join_chat(data, user_id)
    
    elif message_type == "leave_chat":
        await handle_leave_chat(data, user_id)
    
    elif message_type == "typing_indicator":
        await handle_typing_indicator(data, user_id)
    
    elif message_type == "message_read":
        await handle_message_read(data, user_id, db)
    
    elif message_type == "ping":
        # Handle ping for connection keep-alive
        await connection_manager.send_personal_message(user_id, {
            "type": "pong",
            "data": {"timestamp": data.get("timestamp")}
        })
    
    else:
        # Unknown message type
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        })


async def handle_join_chat(data: dict, user_id: uuid.UUID):
    """
    Handle user joining a chat room.
    
    Args:
        data (dict): Message data containing chat_id
        user_id (uuid.UUID): User ID
    """
    try:
        chat_id = uuid.UUID(data.get("chat_id"))
        await connection_manager.join_chat_room(user_id, chat_id)
        
        # Send confirmation
        await connection_manager.send_personal_message(user_id, {
            "type": "chat_joined",
            "data": {"chat_id": str(chat_id)}
        })
        
        # Notify other users in the chat
        await connection_manager.broadcast_to_chat(chat_id, {
            "type": "user_joined_chat",
            "data": {
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            }
        }, exclude_user=user_id)
        
    except (ValueError, KeyError):
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": "Invalid chat_id"}
        })


async def handle_leave_chat(data: dict, user_id: uuid.UUID):
    """
    Handle user leaving a chat room.
    
    Args:
        data (dict): Message data containing chat_id
        user_id (uuid.UUID): User ID
    """
    try:
        chat_id = uuid.UUID(data.get("chat_id"))
        await connection_manager.leave_chat_room(user_id, chat_id)
        
        # Send confirmation
        await connection_manager.send_personal_message(user_id, {
            "type": "chat_left",
            "data": {"chat_id": str(chat_id)}
        })
        
        # Notify other users in the chat
        await connection_manager.broadcast_to_chat(chat_id, {
            "type": "user_left_chat",
            "data": {
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            }
        }, exclude_user=user_id)
        
    except (ValueError, KeyError):
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": "Invalid chat_id"}
        })


async def handle_typing_indicator(data: dict, user_id: uuid.UUID):
    """
    Handle typing indicator updates.
    
    Args:
        data (dict): Message data containing chat_id and is_typing
        user_id (uuid.UUID): User ID
    """
    try:
        chat_id = uuid.UUID(data.get("chat_id"))
        is_typing = data.get("is_typing", False)
        
        await connection_manager.handle_typing_indicator(chat_id, user_id, is_typing)
        
    except (ValueError, KeyError):
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": "Invalid typing indicator data"}
        })


async def handle_message_read(data: dict, user_id: uuid.UUID, db: Session):
    """
    Handle message read confirmation.
    
    Args:
        data (dict): Message data containing message_id and chat_id
        user_id (uuid.UUID): User ID
        db (Session): Database session
    """
    try:
        message_id = uuid.UUID(data.get("message_id"))
        chat_id = uuid.UUID(data.get("chat_id"))
        
        # Update message status in database
        from app.repositories.message_repository import MessageRepository
        message_repo = MessageRepository(db)
        message_repo.update_message_status(message_id, "read")
        
        # Broadcast read receipt
        await connection_manager.handle_message_read(message_id, chat_id, user_id)
        
    except (ValueError, KeyError):
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": "Invalid message read data"}
        })


async def broadcast_new_message(message_data: dict, chat_id: uuid.UUID, sender_id: uuid.UUID):
    """
    Broadcast a new message to all users in a chat.
    
    Args:
        message_data (dict): Message data to broadcast
        chat_id (uuid.UUID): Chat ID
        sender_id (uuid.UUID): Sender user ID
    """
    message = {
        "type": "new_message",
        "data": message_data
    }
    
    await connection_manager.broadcast_to_chat(chat_id, message, exclude_user=sender_id)


async def broadcast_message_update(message_data: dict, chat_id: uuid.UUID):
    """
    Broadcast a message update to all users in a chat.
    
    Args:
        message_data (dict): Updated message data
        chat_id (uuid.UUID): Chat ID
    """
    message = {
        "type": "message_updated",
        "data": message_data
    }
    
    await connection_manager.broadcast_to_chat(chat_id, message)


async def broadcast_message_delete(message_id: uuid.UUID, chat_id: uuid.UUID):
    """
    Broadcast a message deletion to all users in a chat.
    
    Args:
        message_id (uuid.UUID): Deleted message ID
        chat_id (uuid.UUID): Chat ID
    """
    message = {
        "type": "message_deleted",
        "data": {
            "message_id": str(message_id),
            "chat_id": str(chat_id)
        }
    }
    
    await connection_manager.broadcast_to_chat(chat_id, message)


# Background task to clean up typing indicators
async def cleanup_typing_indicators():
    """Background task to clean up old typing indicators."""
    while True:
        await connection_manager.cleanup_typing_indicators()
        await asyncio.sleep(30)  # Run every 30 seconds
