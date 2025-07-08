from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.utils.sticker_service import sticker_service
from app.services.chat_service import ChatService
from app.schemas.chat import MessageCreate, MessageType
from app.websocket.websocket_handler import broadcast_new_message
import uuid
import json

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/stickers/packs")
async def get_sticker_packs(
    current_user: User = Depends(get_current_user)
):
    """
    Get all available sticker packs.
    
    Args:
        current_user (User): Current authenticated user
        
    Returns:
        dict: List of sticker packs
    """
    packs = sticker_service.get_sticker_packs()
    return {"sticker_packs": packs}


@router.get("/stickers/packs/{pack_id}")
async def get_sticker_pack(
    pack_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific sticker pack by ID.
    
    Args:
        pack_id (str): Sticker pack ID
        current_user (User): Current authenticated user
        
    Returns:
        dict: Sticker pack details
        
    Raises:
        HTTPException: If sticker pack not found
    """
    pack = sticker_service.get_sticker_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sticker pack not found"
        )
    
    return pack


@router.get("/stickers/search")
async def search_stickers(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Search stickers by query.
    
    Args:
        q (str): Search query
        limit (int): Maximum number of results
        current_user (User): Current authenticated user
        
    Returns:
        dict: Search results
    """
    stickers = sticker_service.search_stickers(q, limit)
    return {"stickers": stickers, "query": q}


@router.post("/stickers/send")
async def send_sticker(
    chat_id: uuid.UUID,
    pack_id: str,
    sticker_id: str,
    reply_to_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a sticker as a message.
    
    Args:
        chat_id (uuid.UUID): Chat ID to send sticker to
        pack_id (str): Sticker pack ID
        sticker_id (str): Sticker ID
        reply_to_id (Optional[uuid.UUID]): ID of message being replied to
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Sent message information
        
    Raises:
        HTTPException: If sticker not found or send fails
    """
    # Get sticker information
    sticker = sticker_service.get_sticker(pack_id, sticker_id)
    if not sticker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sticker not found"
        )
    
    # Create sticker metadata
    sticker_metadata = {
        "pack_id": pack_id,
        "sticker_id": sticker_id,
        "sticker_name": sticker["name"],
        "sticker_url": sticker["url"]
    }
    
    # Send as message
    chat_service = ChatService(db)
    message_data = MessageCreate(
        content=sticker["name"],  # Sticker name as content
        message_type=MessageType.STICKER,
        reply_to_id=reply_to_id,
        metadata=json.dumps(sticker_metadata)
    )
    
    message_response = chat_service.send_message(chat_id, message_data, current_user.id)
    
    # Broadcast the new message to other users in the chat
    await broadcast_new_message(message_response.dict(), chat_id, current_user.id)
    
    return {"message": message_response.dict()}


@router.get("/gifs/search")
async def search_gifs(
    q: str = Query(..., description="Search query"),
    provider: str = Query("giphy", description="GIF provider (giphy or tenor)"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Search GIFs from external providers.
    
    Args:
        q (str): Search query
        provider (str): GIF provider (giphy or tenor)
        limit (int): Maximum number of results
        offset (int): Offset for pagination
        current_user (User): Current authenticated user
        
    Returns:
        dict: Search results
        
    Raises:
        HTTPException: If provider not supported or API fails
    """
    if provider == "giphy":
        results = await sticker_service.search_gifs_giphy(q, limit, offset)
    elif provider == "tenor":
        results = await sticker_service.search_gifs_tenor(q, limit, offset)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider. Use 'giphy' or 'tenor'"
        )
    
    results["query"] = q
    results["provider"] = provider
    return results


@router.get("/gifs/trending")
async def get_trending_gifs(
    provider: str = Query("giphy", description="GIF provider (currently only giphy)"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Get trending GIFs.
    
    Args:
        provider (str): GIF provider
        limit (int): Maximum number of results
        offset (int): Offset for pagination
        current_user (User): Current authenticated user
        
    Returns:
        dict: Trending GIFs
        
    Raises:
        HTTPException: If provider not supported
    """
    if provider == "giphy":
        results = await sticker_service.get_trending_gifs_giphy(limit, offset)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider. Currently only 'giphy' is supported for trending"
        )
    
    results["provider"] = provider
    return results


@router.post("/gifs/send")
async def send_gif(
    chat_id: uuid.UUID,
    gif_id: str,
    gif_url: str,
    gif_title: str = "",
    provider: str = "giphy",
    preview_url: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    reply_to_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a GIF as a message.
    
    Args:
        chat_id (uuid.UUID): Chat ID to send GIF to
        gif_id (str): GIF ID from provider
        gif_url (str): GIF URL
        gif_title (str): GIF title/description
        provider (str): GIF provider (giphy, tenor)
        preview_url (Optional[str]): Preview/thumbnail URL
        width (Optional[int]): GIF width
        height (Optional[int]): GIF height
        reply_to_id (Optional[uuid.UUID]): ID of message being replied to
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Sent message information
    """
    # Create GIF metadata
    gif_metadata = {
        "gif_id": gif_id,
        "gif_url": gif_url,
        "gif_title": gif_title,
        "provider": provider,
        "preview_url": preview_url,
        "width": width,
        "height": height
    }
    
    # Send as message
    chat_service = ChatService(db)
    message_data = MessageCreate(
        content=gif_title or "GIF",
        message_type=MessageType.GIF,
        reply_to_id=reply_to_id,
        metadata=json.dumps(gif_metadata)
    )
    
    message_response = chat_service.send_message(chat_id, message_data, current_user.id)
    
    # Update message with file information (using GIF URL as file URL)
    from app.repositories.message_repository import MessageRepository
    message_repo = MessageRepository(db)
    message_repo.update_message_file_info(
        message_response.id,
        gif_url,
        f"{gif_title}.gif" if gif_title else "animation.gif",
        0,  # GIF size not tracked for external URLs
        preview_url
    )
    
    # Get updated message
    updated_message = message_repo.get_message_with_details(message_response.id)
    if updated_message:
        updated_response = chat_service._build_message_response(updated_message)
        
        # Broadcast the new message to other users in the chat
        await broadcast_new_message(updated_response.dict(), chat_id, current_user.id)
        
        return {"message": updated_response.dict()}
    
    # Fallback to original response
    await broadcast_new_message(message_response.dict(), chat_id, current_user.id)
    return {"message": message_response.dict()}
