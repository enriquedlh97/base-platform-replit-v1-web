import logging
import os
from typing import Final
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from storage3.types import UploadResponse  # type: ignore[import-untyped]

from app.core.supabase import get_public_storage_url, supabase_admin_client

# Image upload constraints
MAX_IMAGE_MB: Final[int] = 5
ALLOWED_IMAGE_CONTENT_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

# Set up logger for this module
logger = logging.getLogger(__name__)


class FileUploadService:
    """
    Service for handling file uploads to Supabase Storage.

    This service provides centralized file upload functionality with validation,
    error handling, and consistent behavior across different routes.
    """

    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """
        Validate that the uploaded file is a valid image type.

        Note: Size validation is done separately after reading the file content
        to handle cases where the client doesn't send size information.

        Args:
            file: The uploaded file to validate

        Raises:
            HTTPException: If validation fails
        """
        # Validate file type
        if not file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image",
            )
        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))}",
            )

        # Note: some clients do not send size; enforce size after reading bytes

    @staticmethod
    def generate_unique_filename(
        user_id: UUID, original_filename: str = "file.jpg", prefix: str = ""
    ) -> str:
        """
        Generate a unique filename for file uploads.

        Args:
            user_id: ID of the user uploading the file
            original_filename: Original filename from the upload (defaults to "file.jpg")
            prefix: Optional prefix for the file path

        Returns:
            Unique filename string
        """
        file_extension: str = os.path.splitext(original_filename)[1]
        filename: str = f"{user_id}/{uuid4()}{file_extension}"

        if prefix:
            filename = f"{prefix}/{filename}"

        return filename

    @staticmethod
    async def upload_to_storage(
        file_content: bytes,
        bucket_name: str,
        file_path: str,
        content_type: str,
    ) -> str:
        """
        Upload file content to Supabase Storage.

        Args:
            file_content: Binary content of the file
            bucket_name: Name of the storage bucket
            file_path: Path where the file should be stored
            content_type: MIME type of the file

        Returns:
            Public URL of the uploaded file

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Upload to Supabase Storage
            upload_result: UploadResponse = supabase_admin_client.storage.from_(
                bucket_name
            ).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type},
            )

            # Check if upload was successful
            if not upload_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file to {bucket_name}: Upload returned no result",
                )

            # Get public URL using our custom function
            return get_public_storage_url(bucket_name, file_path)

        except Exception as e:
            logger.error(f"Error uploading file to {bucket_name}: {e}")
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to {bucket_name}: {str(e)}",
            )

    @staticmethod
    async def upload_image_for_user(
        file: UploadFile,
        user_id: UUID,
        bucket_name: str,
        max_size_mb: int = MAX_IMAGE_MB,
    ) -> str:
        """
        Complete image upload flow for a user.

        This method handles the entire upload process: validation, filename generation,
        upload to storage, and returns the public URL.

        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            bucket_name: Name of the storage bucket
            max_size_mb: Maximum file size in megabytes

        Returns:
            Public URL of the uploaded file
        """
        # Validate the file (content-type)
        FileUploadService.validate_image_file(file)

        # Read file content and enforce size
        file_content: bytes = await file.read()
        max_size_bytes: int = max_size_mb * 1024 * 1024
        if len(file_content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image file size must be less than {max_size_mb}MB",
            )

        # Generate unique filename
        filename: str = FileUploadService.generate_unique_filename(
            user_id, file.filename or "file.jpg"
        )

        # Upload to storage and return public URL
        # Choose a safe content type
        content_type: str = (
            file.content_type
            if file.content_type in ALLOWED_IMAGE_CONTENT_TYPES
            else "image/jpeg"
        )

        # Log upload attempt (no PII)
        logger.info(
            "upload_image_for_user: user=%s type=%s size_bytes=%s path=%s",
            user_id,
            content_type,
            len(file_content),
            filename,
        )

        return await FileUploadService.upload_to_storage(
            file_content, bucket_name, filename, content_type
        )

    @staticmethod
    async def upload_image_for_workspace(
        file: UploadFile,
        workspace_id: UUID,
        bucket_name: str,
        max_size_mb: int = MAX_IMAGE_MB,
    ) -> str:
        """
        Complete image upload flow for a workspace.

        This method handles the entire upload process: validation, filename generation,
        upload to storage, and returns the public URL.

        Args:
            file: The uploaded file
            workspace_id: ID of the workspace uploading the file
            bucket_name: Name of the storage bucket
            max_size_mb: Maximum file size in megabytes

        Returns:
            Public URL of the uploaded file
        """
        # Validate the file (content-type)
        FileUploadService.validate_image_file(file)

        # Read file content and enforce size
        file_content: bytes = await file.read()
        max_size_bytes: int = max_size_mb * 1024 * 1024
        if len(file_content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image file size must be less than {max_size_mb}MB",
            )

        # Generate unique filename using workspace_id
        file_extension: str = os.path.splitext(file.filename or "file.jpg")[1]
        filename: str = f"workspaces/{workspace_id}/{uuid4()}{file_extension}"

        # Choose a safe content type
        content_type: str = (
            file.content_type
            if file.content_type in ALLOWED_IMAGE_CONTENT_TYPES
            else "image/jpeg"
        )

        # Log upload attempt (no PII)
        logger.info(
            "upload_image_for_workspace: workspace=%s type=%s size_bytes=%s path=%s",
            workspace_id,
            content_type,
            len(file_content),
            filename,
        )

        return await FileUploadService.upload_to_storage(
            file_content, bucket_name, filename, content_type
        )
