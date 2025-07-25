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
from datetime import datetime


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
    
    elif message_type == "call_initiated":
        await handle_call_initiated(data, user_id)
    
    elif message_type == "call_answered":
        await handle_call_answered(data, user_id)
    
    elif message_type == "call_declined":
        await handle_call_declined(data, user_id)
    
    elif message_type == "call_ended":
        await handle_call_ended(data, user_id)
    
    elif message_type == "call_participant_joined":
        await handle_call_participant_joined(data, user_id)
    
    elif message_type == "call_participant_left":
        await handle_call_participant_left(data, user_id)
    
    elif message_type == "location_update":
        await handle_location_update(data, user_id, db)
    
    elif message_type == "location_share_start":
        await handle_location_share_start(data, user_id, db)
    
    elif message_type == "location_share_stop":
        await handle_location_share_stop(data, user_id, db)
    
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


# Video Call WebSocket Handlers

async def handle_call_initiated(data: dict, user_id: uuid.UUID):
    """
    Handle video call initiation notification.
    
    Args:
        data (dict): Call data containing call_id, callee_id, etc.
        user_id (uuid.UUID): Caller's user ID
    """
    try:
        call_id = data.get("call_id")
        callee_id = uuid.UUID(data.get("callee_id"))
        call_type = data.get("call_type", "video")
        channel_name = data.get("channel_name")
        
        # Notify the callee about incoming call
        await connection_manager.send_personal_message(callee_id, {
            "type": "incoming_call",
            "data": {
                "call_id": call_id,
                "caller_id": str(user_id),
                "call_type": call_type,
                "channel_name": channel_name
            }
        })
        
        # Send confirmation to caller
        await connection_manager.send_personal_message(user_id, {
            "type": "call_initiated_success",
            "data": {
                "call_id": call_id,
                "channel_name": channel_name
            }
        })
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid call initiation data: {str(e)}"}
        })


async def handle_call_answered(data: dict, user_id: uuid.UUID):
    """
    Handle call answer notification.
    
    Args:
        data (dict): Call data containing call_id, accept status
        user_id (uuid.UUID): Callee's user ID
    """
    try:
        call_id = data.get("call_id")
        caller_id = uuid.UUID(data.get("caller_id"))
        accepted = data.get("accepted", False)
        channel_name = data.get("channel_name")
        
        if accepted:
            # Notify caller that call was answered
            await connection_manager.send_personal_message(caller_id, {
                "type": "call_answered",
                "data": {
                    "call_id": call_id,
                    "callee_id": str(user_id),
                    "channel_name": channel_name
                }
            })
        else:
            # Notify caller that call was declined
            await connection_manager.send_personal_message(caller_id, {
                "type": "call_declined",
                "data": {
                    "call_id": call_id,
                    "callee_id": str(user_id)
                }
            })
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid call answer data: {str(e)}"}
        })


async def handle_call_declined(data: dict, user_id: uuid.UUID):
    """
    Handle call decline notification.
    
    Args:
        data (dict): Call data containing call_id, caller_id
        user_id (uuid.UUID): Callee's user ID
    """
    try:
        call_id = data.get("call_id")
        caller_id = uuid.UUID(data.get("caller_id"))
        
        # Notify caller that call was declined
        await connection_manager.send_personal_message(caller_id, {
            "type": "call_declined",
            "data": {
                "call_id": call_id,
                "callee_id": str(user_id)
            }
        })
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid call decline data: {str(e)}"}
        })


async def handle_call_ended(data: dict, user_id: uuid.UUID):
    """
    Handle call end notification.
    
    Args:
        data (dict): Call data containing call_id, participants
        user_id (uuid.UUID): User who ended the call
    """
    try:
        call_id = data.get("call_id")
        participants = data.get("participants", [])
        end_reason = data.get("end_reason", "user_ended")
        
        # Notify all participants that call has ended
        for participant_id in participants:
            try:
                participant_uuid = uuid.UUID(participant_id)
                if participant_uuid != user_id:  # Don't notify the user who ended the call
                    await connection_manager.send_personal_message(participant_uuid, {
                        "type": "call_ended",
                        "data": {
                            "call_id": call_id,
                            "ended_by": str(user_id),
                            "end_reason": end_reason
                        }
                    })
            except ValueError:
                continue  # Skip invalid participant IDs
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid call end data: {str(e)}"}
        })


async def handle_call_participant_joined(data: dict, user_id: uuid.UUID):
    """
    Handle participant joining a group call.
    
    Args:
        data (dict): Call data containing call_id, participant info
        user_id (uuid.UUID): User ID of the participant who joined
    """
    try:
        call_id = data.get("call_id")
        participants = data.get("participants", [])
        participant_name = data.get("participant_name", "Unknown")
        
        # Notify all other participants about the new joiner
        for participant_id in participants:
            try:
                participant_uuid = uuid.UUID(participant_id)
                if participant_uuid != user_id:  # Don't notify the joiner
                    await connection_manager.send_personal_message(participant_uuid, {
                        "type": "call_participant_joined",
                        "data": {
                            "call_id": call_id,
                            "participant_id": str(user_id),
                            "participant_name": participant_name
                        }
                    })
            except ValueError:
                continue  # Skip invalid participant IDs
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid participant join data: {str(e)}"}
        })


async def handle_call_participant_left(data: dict, user_id: uuid.UUID):
    """
    Handle participant leaving a group call.
    
    Args:
        data (dict): Call data containing call_id, participant info
        user_id (uuid.UUID): User ID of the participant who left
    """
    try:
        call_id = data.get("call_id")
        participants = data.get("participants", [])
        participant_name = data.get("participant_name", "Unknown")
        
        # Notify all remaining participants about the departure
        for participant_id in participants:
            try:
                participant_uuid = uuid.UUID(participant_id)
                if participant_uuid != user_id:  # Don't notify the leaver
                    await connection_manager.send_personal_message(participant_uuid, {
                        "type": "call_participant_left",
                        "data": {
                            "call_id": call_id,
                            "participant_id": str(user_id),
                            "participant_name": participant_name
                        }
                    })
            except ValueError:
                continue  # Skip invalid participant IDs
        
    except (ValueError, KeyError) as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Invalid participant leave data: {str(e)}"}
        })


# Video call utility functions for broadcasting

async def broadcast_call_event(event_type: str, call_data: dict, participants: list):
    """
    Broadcast a call event to all participants.
    
    Args:
        event_type (str): Type of call event
        call_data (dict): Call event data
        participants (list): List of participant user IDs
    """
    message = {
        "type": event_type,
        "data": call_data
    }
    
    for participant_id in participants:
        try:
            participant_uuid = uuid.UUID(participant_id)
            await connection_manager.send_personal_message(participant_uuid, message)
        except (ValueError, TypeError):
            continue  # Skip invalid participant IDs


async def notify_call_quality_update(call_id: int, quality_data: dict, participants: list):
    """
    Notify participants about call quality updates.
    
    Args:
        call_id (int): Call ID
        quality_data (dict): Quality metrics data
        participants (list): List of participant user IDs
    """
    await broadcast_call_event("call_quality_update", {
        "call_id": call_id,
        "quality": quality_data
    }, participants)

# Background task to clean up typing indicators
async def cleanup_typing_indicators():
    """Background task to clean up old typing indicators."""
    while True:
        await connection_manager.cleanup_typing_indicators()
        await asyncio.sleep(30)  # Run every 30 seconds


# Location-related WebSocket handlers

async def handle_location_update(data: dict, user_id: uuid.UUID, db: Session):
    """
    Handle real-time location updates from clients.
    
    Args:
        data (dict): Location data from client
        user_id (uuid.UUID): User ID
        db (Session): Database session
    """
    try:
        from app.services.location_service import LocationService
        from app.schemas.location import UserLocationCreate
        
        # Validate required fields
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        
        if latitude is None or longitude is None:
            await connection_manager.send_personal_message(user_id, {
                "type": "error",
                "data": {"message": "Latitude and longitude are required"}
            })
            return
        
        # Create location update data
        location_data = UserLocationCreate(
            latitude=latitude,
            longitude=longitude,
            accuracy=data.get("accuracy"),
            altitude=data.get("altitude"),
            speed=data.get("speed"),
            heading=data.get("heading")
        )
        
        # Update location using service
        location_service = LocationService(db)
        location = await location_service.update_user_location(int(user_id), location_data)
        
        # Send confirmation to user
        await connection_manager.send_personal_message(user_id, {
            "type": "location_updated",
            "data": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timestamp": location.created_at.isoformat()
            }
        })
        
        # Notify users who are sharing location with this user
        await notify_location_shares(user_id, location)
        
    except Exception as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Location update failed: {str(e)}"}
        })


async def handle_location_share_start(data: dict, user_id: uuid.UUID, db: Session):
    """
    Handle starting location sharing via WebSocket.
    
    Args:
        data (dict): Location share data
        user_id (uuid.UUID): User ID
        db (Session): Database session
    """
    try:
        from app.services.location_service import LocationService
        from app.schemas.location import LocationShareCreate
        from datetime import datetime, timedelta
        
        # Parse share data
        target_user_id = data.get("target_user_id")
        duration_minutes = data.get("duration_minutes", 60)
        
        # Create location share
        share_data = LocationShareCreate(
            target_user_id=target_user_id,
            expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes),
            is_active=True
        )
        
        location_service = LocationService(db)
        location_share = await location_service.create_location_share(int(user_id), share_data)
        
        # Send confirmation to user
        await connection_manager.send_personal_message(user_id, {
            "type": "location_share_started",
            "data": {
                "share_id": location_share.id,
                "target_user_id": location_share.target_user_id,
                "expires_at": location_share.expires_at.isoformat() if location_share.expires_at else None
            }
        })
        
        # Notify target user if specific user share
        if target_user_id:
            try:
                target_uuid = uuid.UUID(str(target_user_id))
                await connection_manager.send_personal_message(target_uuid, {
                    "type": "location_share_received",
                    "data": {
                        "sharer_id": int(user_id),
                        "share_id": location_share.id,
                        "expires_at": location_share.expires_at.isoformat() if location_share.expires_at else None
                    }
                })
            except (ValueError, TypeError):
                pass  # Skip invalid target user ID
        
    except Exception as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Location share start failed: {str(e)}"}
        })


async def handle_location_share_stop(data: dict, user_id: uuid.UUID, db: Session):
    """
    Handle stopping location sharing via WebSocket.
    
    Args:
        data (dict): Location share data
        user_id (uuid.UUID): User ID
        db (Session): Database session
    """
    try:
        from app.services.location_service import LocationService
        
        share_id = data.get("share_id")
        if not share_id:
            await connection_manager.send_personal_message(user_id, {
                "type": "error",
                "data": {"message": "Share ID is required"}
            })
            return
        
        location_service = LocationService(db)
        success = await location_service.delete_location_share(share_id, int(user_id))
        
        if success:
            await connection_manager.send_personal_message(user_id, {
                "type": "location_share_stopped",
                "data": {"share_id": share_id}
            })
        else:
            await connection_manager.send_personal_message(user_id, {
                "type": "error",
                "data": {"message": "Location share not found or access denied"}
            })
        
    except Exception as e:
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {"message": f"Location share stop failed: {str(e)}"}
        })


async def notify_location_shares(user_id: uuid.UUID, location):
    """
    Notify users who are sharing location with the updated user.
    
    Args:
        user_id (uuid.UUID): User who updated location
        location: Location object with updated coordinates
    """
    try:
        from app.repositories.location_repository import LocationRepository
        from app.core.database import get_db
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            location_repo = LocationRepository(db)
            
            # Get users who have access to this user's location
            active_shares = location_repo.get_active_location_shares(int(user_id))
            
            for share in active_shares:
                # Send location update to target user
                if share.target_user_id:
                    try:
                        target_uuid = uuid.UUID(str(share.target_user_id))
                        await connection_manager.send_personal_message(target_uuid, {
                            "type": "shared_location_update",
                            "data": {
                                "user_id": int(user_id),
                                "latitude": location.latitude,
                                "longitude": location.longitude,
                                "accuracy": location.accuracy,
                                "timestamp": location.created_at.isoformat(),
                                "share_id": share.id
                            }
                        })
                    except (ValueError, TypeError):
                        continue  # Skip invalid target user IDs
        finally:
            db.close()
            
    except Exception as e:
        # Log error but don't interrupt the main location update
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error notifying location shares: {str(e)}")


async def notify_geofence_event(user_id: int, geofence_name: str, event_type: str, location_data: dict):
    """
    Notify user about geofence events via WebSocket.
    
    Args:
        user_id (int): User ID
        geofence_name (str): Name of the geofence area
        event_type (str): Type of event (entry/exit)
        location_data (dict): Location data when event occurred
    """
    try:
        user_uuid = uuid.UUID(str(user_id))
        await connection_manager.send_personal_message(user_uuid, {
            "type": "geofence_event",
            "data": {
                "geofence_name": geofence_name,
                "event_type": event_type,
                "location": location_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    except (ValueError, TypeError):
        pass  # Skip invalid user ID
