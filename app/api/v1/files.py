from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.utils.file_upload import file_upload_service
from app.services.chat_service import ChatService
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import MessageCreate, MessageResponse, MessageType
from app.websocket.websocket_handler import broadcast_new_message
import uuid

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    chat_id: Optional[uuid.UUID] = Form(None),
    message_type: Optional[str] = Form(None),
    reply_to_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file and optionally send it as a message.
    
    Args:
        file (UploadFile): File to upload
        chat_id (Optional[uuid.UUID]): Chat ID to send file as message
        message_type (Optional[str]): Type of message (image, video, audio, file)
        reply_to_id (Optional[uuid.UUID]): ID of message being replied to
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Upload result with file information
    """
    try:
        # Determine message type if not provided
        if not message_type:
            message_type = file_upload_service.get_file_type_from_filename(file.filename)
        
        # Upload file
        file_url, original_filename, file_size, thumbnail_url = await file_upload_service.upload_file(
            file, message_type
        )
        
        result = {
            "file_url": file_url,
            "file_name": original_filename,
            "file_size": file_size,
            "thumbnail_url": thumbnail_url,
            "message_type": message_type
        }
        
        # If chat_id is provided, send as message
        if chat_id:
            chat_service = ChatService(db)
            message_repo = MessageRepository(db)
            
            # Create message
            message_data = MessageCreate(
                content=None,
                message_type=MessageType(message_type),
                reply_to_id=reply_to_id
            )
            
            message_response = chat_service.send_message(chat_id, message_data, current_user.id)
            
            # Update message with file information
            message_repo.update_message_file_info(
                message_response.id,
                file_url,
                original_filename,
                file_size,
                thumbnail_url
            )
            
            # Get updated message
            updated_message = message_repo.get_message_with_details(message_response.id)
            if updated_message:
                from app.services.chat_service import ChatService
                chat_service_instance = ChatService(db)
                updated_response = chat_service_instance._build_message_response(updated_message)
                
                # Broadcast the new message to other users in the chat
                await broadcast_new_message(updated_response.dict(), chat_id, current_user.id)
                
                result["message"] = updated_response.dict()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/upload-multiple", status_code=status.HTTP_201_CREATED)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    chat_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files.
    
    Args:
        files (List[UploadFile]): Files to upload
        chat_id (Optional[uuid.UUID]): Chat ID to send files as messages
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Upload results for all files
    """
    if len(files) > 10:  # Limit to 10 files per upload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files can be uploaded at once"
        )
    
    results = []
    chat_service = None
    message_repo = None
    
    if chat_id:
        chat_service = ChatService(db)
        message_repo = MessageRepository(db)
    
    for file in files:
        try:
            # Determine message type
            message_type = file_upload_service.get_file_type_from_filename(file.filename)
            
            # Upload file
            file_url, original_filename, file_size, thumbnail_url = await file_upload_service.upload_file(
                file, message_type
            )
            
            result = {
                "file_url": file_url,
                "file_name": original_filename,
                "file_size": file_size,
                "thumbnail_url": thumbnail_url,
                "message_type": message_type,
                "status": "success"
            }
            
            # If chat_id is provided, send as message
            if chat_id and chat_service and message_repo:
                try:
                    # Create message
                    message_data = MessageCreate(
                        content=None,
                        message_type=MessageType(message_type)
                    )
                    
                    message_response = chat_service.send_message(chat_id, message_data, current_user.id)
                    
                    # Update message with file information
                    message_repo.update_message_file_info(
                        message_response.id,
                        file_url,
                        original_filename,
                        file_size,
                        thumbnail_url
                    )
                    
                    # Get updated message
                    updated_message = message_repo.get_message_with_details(message_response.id)
                    if updated_message:
                        from app.services.chat_service import ChatService
                        chat_service_instance = ChatService(db)
                        updated_response = chat_service_instance._build_message_response(updated_message)
                        
                        # Broadcast the new message to other users in the chat
                        await broadcast_new_message(updated_response.dict(), chat_id, current_user.id)
                        
                        result["message"] = updated_response.dict()
                
                except Exception as e:
                    result["status"] = "uploaded_but_message_failed"
                    result["error"] = str(e)
            
            results.append(result)
            
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {"files": results}


@router.post("/upload-avatar", status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar image.
    
    Args:
        file (UploadFile): Avatar image file
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Upload result with avatar URL
    """
    # Validate that it's an image
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Upload file
        file_url, original_filename, file_size, thumbnail_url = await file_upload_service.upload_file(
            file, "image"
        )
        
        # Update user avatar
        from app.repositories.user_repository import UserRepository
        from app.schemas.auth import UserUpdate
        
        user_repo = UserRepository(db)
        user_update = UserUpdate(avatar_url=file_url)
        updated_user = user_repo.update_user(current_user.id, user_update)
        
        if not updated_user:
            # If user update failed, clean up uploaded file
            file_upload_service.delete_file(file_url)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user avatar"
            )
        
        return {
            "avatar_url": file_url,
            "thumbnail_url": thumbnail_url,
            "message": "Avatar updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )


@router.delete("/delete")
async def delete_file(
    file_url: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file from storage.
    
    Args:
        file_url (str): URL of file to delete
        current_user (User): Current authenticated user
        
    Returns:
        dict: Deletion result
    """
    # Note: In a production system, you would want to verify that the user
    # has permission to delete this file (e.g., they uploaded it or it's their avatar)
    
    success = file_upload_service.delete_file(file_url)
    
    if success:
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get("/validate")
async def validate_file_upload(
    filename: str,
    file_size: int,
    current_user: User = Depends(get_current_user)
):
    """
    Validate file before upload (pre-upload validation).
    
    Args:
        filename (str): Name of file to validate
        file_size (int): Size of file in bytes
        current_user (User): Current authenticated user
        
    Returns:
        dict: Validation result
    """
    # Check file size
    if file_size > file_upload_service.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {file_upload_service.max_file_size} bytes"
        )
    
    # Check file extension
    file_extension = filename.split('.')[-1].lower()
    file_type = file_upload_service.get_file_type_from_filename(filename)
    
    allowed_extensions = []
    if file_type == "image":
        allowed_extensions = file_upload_service.allowed_image_extensions
    elif file_type == "video":
        allowed_extensions = file_upload_service.allowed_video_extensions
    elif file_type == "audio":
        allowed_extensions = ['mp3', 'wav', 'ogg', 'aac', 'm4a']
    
    is_allowed = (
        file_extension in file_upload_service.allowed_image_extensions or
        file_extension in file_upload_service.allowed_video_extensions or
        file_extension in ['mp3', 'wav', 'ogg', 'aac', 'm4a']
    )
    
    return {
        "valid": is_allowed,
        "file_type": file_type,
        "file_extension": file_extension,
        "allowed_extensions": allowed_extensions,
        "max_file_size": file_upload_service.max_file_size
    }
