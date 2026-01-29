"""
Storage Service

Handles file storage operations using Cloudflare R2.
"""

import logging
import os

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage operations"""

    def __init__(self):
        """Initialize StorageService - MinIO connection is lazily established"""
        self.client = None
        # Storage configuration
        self.cloudflare_r2_account_id = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID")
        self.cloudflare_r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.cloudflare_r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.cloudflare_r2_bucket = os.getenv("CLOUDFLARE_R2_BUCKET", "jobswipe-storage")
        
        # Only validate configuration when client is initialized
        # This allows the service to be imported without requiring all variables to be set immediately

    def _get_client(self):
        """Lazily initialize and return MinIO client"""
        if self.client is None:
            try:
                if not self.cloudflare_r2_account_id:
                    raise ValueError(
                        "CLOUDFLARE_R2_ACCOUNT_ID environment variable is required for storage operations"
                    )
                if not self.cloudflare_r2_access_key_id:
                    raise ValueError(
                        "CLOUDFLARE_R2_ACCESS_KEY_ID environment variable is required for storage operations"
                    )
                if not self.cloudflare_r2_secret_access_key:
                    raise ValueError(
                        "CLOUDFLARE_R2_SECRET_ACCESS_KEY environment variable is required for storage operations"
                    )
                    
                endpoint = f"https://{self.cloudflare_r2_account_id}.r2.cloudflarestorage.com"
                self.client = Minio(
                    endpoint,
                    access_key=self.cloudflare_r2_access_key_id,
                    secret_key=self.cloudflare_r2_secret_access_key,
                    secure=True,
                )
                # Ensure bucket exists (only when client is first initialized)
                if not self.client.bucket_exists(self.cloudflare_r2_bucket):
                    self.client.make_bucket(self.cloudflare_r2_bucket)
                    logger.info("Created bucket: %s", self.cloudflare_r2_bucket)
                else:
                    logger.info("Bucket exists: %s", self.cloudflare_r2_bucket)
            except Exception as e:
                logger.error("Failed to connect to MinIO: %s", str(e))
                raise
        return self.client

    def upload_file(
        self,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file to storage.

        Args:
            file_path: Target file path
            file_content: File content as bytes
            content_type: Content type (default: application/octet-stream)

        Returns:
            File URL
        """
        try:
            self._get_client().put_object(
                self.cloudflare_r2_bucket,
                file_path,
                data=bytes(file_content),
                length=len(file_content),
                content_type=content_type,
            )

            logger.info("File uploaded successfully: %s", file_path)

            return self.get_file_url(file_path)

        except S3Error as e:
            logger.error("Error uploading file %s: %s", file_path, str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error uploading file %s: %s", file_path, str(e))
            raise

    def get_file_url(self, file_path: str) -> str:
        """
        Get file URL.

        Args:
            file_path: File path

        Returns:
            File URL
        """
        try:
            return self._get_client().presigned_get_object(
                self.cloudflare_r2_bucket, file_path, expires=604800
            )
        except Exception as e:
            logger.error("Error getting file URL for %s: %s", file_path, str(e))
            raise

    def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage.

        Args:
            file_path: File path

        Returns:
            File content as bytes
        """
        try:
            response = self._get_client().get_object(self.cloudflare_r2_bucket, file_path)
            data = response.read()
            response.close()
            response.release_conn()

            logger.info("File downloaded successfully: %s", file_path)

            return data

        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning("File not found: %s", file_path)
                return None
            logger.error("Error downloading file %s: %s", file_path, str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error downloading file %s: %s", file_path, str(e))
            raise

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: File path

        Returns:
            Boolean indicating success
        """
        try:
            self._get_client().remove_object(self.cloudflare_r2_bucket, file_path)
            logger.info("File deleted successfully: %s", file_path)

            return True

        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning("File not found: %s", file_path)
                return False
            logger.error("Error deleting file %s: %s", file_path, str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error deleting file %s: %s", file_path, str(e))
            raise

    def list_files(self, prefix: str = "") -> list:
        """
        List files in a bucket with prefix.

        Args:
            prefix: Prefix for filtering files

        Returns:
            List of file paths
        """
        try:
            objects = self._get_client().list_objects(
                self.cloudflare_r2_bucket, prefix=prefix, recursive=True
            )
            return [obj.object_name for obj in objects]

        except Exception as e:
            logger.error("Error listing files with prefix %s: %s", prefix, str(e))
            raise


# Singleton instance
storage_service = StorageService()


# Helper functions for convenience
def upload_file(
    file_path: str, file_content: bytes, content_type: str = "application/octet-stream"
) -> str:
    """
    Convenience function to upload file.

    Args:
        file_path: Target file path
        file_content: File content as bytes
        content_type: Content type (default: application/octet-stream)

    Returns:
        File URL
    """
    return storage_service.upload_file(file_path, file_content, content_type)


def download_file(file_path: str) -> bytes:
    """
    Convenience function to download file.

    Args:
        file_path: File path

    Returns:
        File content as bytes
    """
    return storage_service.download_file(file_path)


def delete_file(file_path: str) -> bool:
    """
    Convenience function to delete file.

    Args:
        file_path: File path

    Returns:
        Boolean indicating success
    """
    return storage_service.delete_file(file_path)


def list_files(prefix: str = "") -> list:
    """
    Convenience function to list files.

    Args:
        prefix: Prefix for filtering files

    Returns:
        List of file paths
    """
    return storage_service.list_files(prefix)
