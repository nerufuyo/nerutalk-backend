import os
import uuid
import mimetypes
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import hashlib


class FileUploadService:
    """
    Service for handling file uploads and storage.
    
    Supports local storage and AWS S3 storage with automatic
    image processing and thumbnail generation.
    """
    
    def __init__(self):
        """Initialize the file upload service."""
        self.upload_dir = "uploads"
        self.max_file_size = settings.max_file_size
        self.allowed_image_extensions = settings.allowed_image_extensions.split(',')
        self.allowed_video_extensions = settings.allowed_video_extensions.split(',')
        
        # Initialize S3 client if credentials are provided
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(f"{self.upload_dir}/images", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/videos", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/audio", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/files", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/thumbnails", exist_ok=True)
    
    def validate_file(self, file: UploadFile, allowed_types: List[str] = None) -> bool:
        """
        Validate uploaded file.
        
        Args:
            file (UploadFile): Uploaded file
            allowed_types (List[str]): List of allowed file types
            
        Returns:
            bool: True if file is valid
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            )
        
        # Check file extension
        if file.filename:
            file_extension = file.filename.split('.')[-1].lower()
            
            if allowed_types and file_extension not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type '{file_extension}' is not allowed"
                )
        
        return True
    
    def get_file_type_from_filename(self, filename: str) -> str:
        """
        Determine file type based on filename.
        
        Args:
            filename (str): File name
            
        Returns:
            str: File type (image, video, audio, file)
        """
        if not filename:
            return "file"
        
        extension = filename.split('.')[-1].lower()
        
        if extension in self.allowed_image_extensions:
            return "image"
        elif extension in self.allowed_video_extensions:
            return "video"
        elif extension in ['mp3', 'wav', 'ogg', 'aac', 'm4a']:
            return "audio"
        else:
            return "file"
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent conflicts.
        
        Args:
            original_filename (str): Original filename
            
        Returns:
            str: Unique filename
        """
        if not original_filename:
            return str(uuid.uuid4())
        
        name, extension = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{extension}"
    
    async def upload_file(self, file: UploadFile, file_type: str = None) -> Tuple[str, str, int, Optional[str]]:
        """
        Upload file and return file information.
        
        Args:
            file (UploadFile): File to upload
            file_type (str): Type of file (image, video, audio, file)
            
        Returns:
            Tuple[str, str, int, Optional[str]]: (file_url, filename, file_size, thumbnail_url)
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Determine file type if not provided
            if not file_type:
                file_type = self.get_file_type_from_filename(file.filename)
            
            # Validate file based on type
            if file_type == "image":
                self.validate_file(file, self.allowed_image_extensions)
            elif file_type == "video":
                self.validate_file(file, self.allowed_video_extensions)
            else:
                self.validate_file(file)
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Check file size again after reading
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
                )
            
            # Upload to S3 if configured, otherwise save locally
            if self.s3_client and settings.aws_bucket_name:
                file_url, thumbnail_url = await self._upload_to_s3(
                    file_content, unique_filename, file_type, file.content_type
                )
            else:
                file_url, thumbnail_url = await self._save_locally(
                    file_content, unique_filename, file_type
                )
            
            return file_url, file.filename, file_size, thumbnail_url
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def _upload_to_s3(self, file_content: bytes, filename: str, 
                           file_type: str, content_type: str = None) -> Tuple[str, Optional[str]]:
        """
        Upload file to AWS S3.
        
        Args:
            file_content (bytes): File content
            filename (str): Filename
            file_type (str): File type
            content_type (str): MIME content type
            
        Returns:
            Tuple[str, Optional[str]]: (file_url, thumbnail_url)
        """
        try:
            # Determine S3 key (path)
            s3_key = f"{file_type}s/{filename}"
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=settings.aws_bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            )
            
            # Generate file URL
            file_url = f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            
            # Generate thumbnail for images
            thumbnail_url = None
            if file_type == "image":
                thumbnail_url = await self._generate_and_upload_thumbnail_s3(
                    file_content, filename
                )
            
            return file_url, thumbnail_url
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to S3: {str(e)}"
            )
    
    async def _save_locally(self, file_content: bytes, filename: str, 
                           file_type: str) -> Tuple[str, Optional[str]]:
        """
        Save file locally.
        
        Args:
            file_content (bytes): File content
            filename (str): Filename
            file_type (str): File type
            
        Returns:
            Tuple[str, Optional[str]]: (file_url, thumbnail_url)
        """
        # Determine file path
        file_path = os.path.join(self.upload_dir, f"{file_type}s", filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Generate file URL (this would be served by your web server)
        file_url = f"/uploads/{file_type}s/{filename}"
        
        # Generate thumbnail for images
        thumbnail_url = None
        if file_type == "image":
            thumbnail_url = await self._generate_thumbnail_locally(file_path, filename)
        
        return file_url, thumbnail_url
    
    async def _generate_and_upload_thumbnail_s3(self, image_content: bytes, 
                                               original_filename: str) -> Optional[str]:
        """
        Generate thumbnail and upload to S3.
        
        Args:
            image_content (bytes): Original image content
            original_filename (str): Original filename
            
        Returns:
            Optional[str]: Thumbnail URL
        """
        try:
            # Generate thumbnail
            thumbnail_content = self._create_thumbnail(image_content)
            if not thumbnail_content:
                return None
            
            # Generate thumbnail filename
            name, _ = os.path.splitext(original_filename)
            thumbnail_filename = f"{name}_thumb.jpg"
            thumbnail_key = f"thumbnails/{thumbnail_filename}"
            
            # Upload thumbnail to S3
            self.s3_client.put_object(
                Bucket=settings.aws_bucket_name,
                Key=thumbnail_key,
                Body=thumbnail_content,
                ContentType="image/jpeg"
            )
            
            # Return thumbnail URL
            return f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{thumbnail_key}"
            
        except Exception:
            return None
    
    async def _generate_thumbnail_locally(self, image_path: str, 
                                        original_filename: str) -> Optional[str]:
        """
        Generate thumbnail locally.
        
        Args:
            image_path (str): Path to original image
            original_filename (str): Original filename
            
        Returns:
            Optional[str]: Thumbnail URL
        """
        try:
            # Generate thumbnail filename
            name, _ = os.path.splitext(original_filename)
            thumbnail_filename = f"{name}_thumb.jpg"
            thumbnail_path = os.path.join(self.upload_dir, "thumbnails", thumbnail_filename)
            
            # Create thumbnail
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return f"/uploads/thumbnails/{thumbnail_filename}"
            
        except Exception:
            return None
    
    def _create_thumbnail(self, image_content: bytes) -> Optional[bytes]:
        """
        Create thumbnail from image content.
        
        Args:
            image_content (bytes): Original image content
            
        Returns:
            Optional[bytes]: Thumbnail content
        """
        try:
            from io import BytesIO
            
            # Open image
            with Image.open(BytesIO(image_content)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Save to bytes
                output = BytesIO()
                img.save(output, format="JPEG", quality=85)
                return output.getvalue()
                
        except Exception:
            return None
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_url (str): File URL to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            if self.s3_client and settings.aws_bucket_name and file_url.startswith("https://"):
                # Extract S3 key from URL
                s3_key = file_url.split(f"{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/")[-1]
                self.s3_client.delete_object(Bucket=settings.aws_bucket_name, Key=s3_key)
            else:
                # Delete local file
                if file_url.startswith("/uploads/"):
                    file_path = file_url[1:]  # Remove leading slash
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            return True
            
        except Exception:
            return False
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """
        Generate hash for file content to detect duplicates.
        
        Args:
            file_content (bytes): File content
            
        Returns:
            str: File hash
        """
        return hashlib.md5(file_content).hexdigest()


# Global file upload service instance
file_upload_service = FileUploadService()
