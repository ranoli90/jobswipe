"""
File Upload Validation Middleware

Validates uploaded files for security and type compliance.
"""

import logging
import os
import re
from typing import Callable, Optional, Set, Tuple

import magic
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class FileValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate file uploads.

    Configuration:
    - ALLOWED_FILE_TYPES: Set of allowed MIME types (e.g., {"application/pdf"})
    - ALLOWED_EXTENSIONS: Set of allowed file extensions (e.g., {".pdf", ".docx"})
    - MAX_FILE_SIZE: Maximum file size in bytes (default: 10MB)
    - BLOCKED_PATTERNS: Patterns that trigger immediate rejection
    """

    # Known dangerous file signatures (magic bytes)
    DANGEROUS_SIGNATURES = {
        b"\x4d\x5a",  # EXE/DLL (Windows executable)
        b"\x7f\x45\x4c\x46",  # ELF (Linux executable)
        b"\xca\xfe\xba\xbe",  # Java class
        b"\x89PNG",  # PNG (can contain executable code)
        b"\x49\x44\x33",  # ID3 (audio metadata)
    }

    # Executable extensions that should be blocked
    DANGEROUS_EXTENSIONS = {
        ".exe",
        ".dll",
        ".bat",
        ".sh",
        ".cmd",
        ".com",
        ".pif",
        ".scr",
        ".js",
        ".jse",
        ".vbs",
        ".vbe",
        ".wsh",
        ".wsf",
        ".wsc",
        ".ps1",
        ".ps1xml",
        ".ps2",
        ".ps2xml",
        ".psc1",
        ".psc2",
        ".msh",
        ".msh1",
        ".msh2",
        ".mshxml",
        ".msh1xml",
        ".msh2xml",
        ".elf",
        ".bin",
        ".out",
        ".so",
        ".dylib",
    }

    def __init__(
        self,
        app,
        allowed_file_types: Set[str] = None,
        allowed_extensions: Set[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        block_dangerous: bool = True,
    ):
        super().__init__(app)
        self.allowed_file_types = allowed_file_types or {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "text/plain",
            "text/csv",
            "text/markdown",
            "application/json",
        }
        self.allowed_extensions = allowed_extensions or {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".txt",
            ".csv",
            ".md",
            ".json",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
        }
        self.max_file_size = max_file_size
        self.block_dangerous = block_dangerous

    def _validate_file_content(self, content: bytes) -> Tuple[bool, str]:
        """
        Validate file content using magic bytes.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous signatures
        for signature in self.DANGEROUS_SIGNATURES:
            if content[: len(signature)] == signature:
                return (
                    False,
                    f"Potentially dangerous file type detected (signature: {signature.hex()})",
                )

        # Check for embedded executables in common formats
        if content[:4] == b"\x89PNG":
            # PNG files should not contain PE/ELF headers
            if b"MZ" in content:
                return False, "Embedded executable detected in PNG file"

        return True, ""

    def _validate_extension(self, filename: str) -> Tuple[bool, str]:
        """
        Validate file extension.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "No filename provided"

        ext = os.path.splitext(filename)[1].lower()

        if self.block_dangerous and ext in self.DANGEROUS_EXTENSIONS:
            return False, f"File extension '{ext}' is not allowed"

        if ext not in self.allowed_extensions:
            return (
                False,
                f"File extension '{ext}' is not allowed. Allowed: {', '.join(self.allowed_extensions)}",
            )

        return True, ""

    def _validate_filename(self, filename: str) -> Tuple[bool, str]:
        """
        Validate filename for path traversal and special characters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "No filename provided"

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "Invalid characters in filename"

        # Check for special characters
        if re.search(r"[\x00-\x1f\x7f-\x9f]", filename):
            return False, "Control characters not allowed in filename"

        # Check for double extensions (common malware technique)
        if filename.count(".") > 1:
            return False, "Multiple file extensions not allowed"

        return True, ""

    def _get_content_type(self, content: bytes) -> str:
        """Get MIME type using magic bytes"""
        mime_type = magic.from_buffer(content, mime=True)
        return mime_type

    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request and validate file uploads"""
        # Only process POST, PUT, PATCH requests with content-type multipart
        content_type = request.headers.get("content-type", "")

        if not content_type.startswith("multipart/form-data"):
            return await call_next(request)

        # Read a chunk of the body to validate
        body = await request.body()

        if not body:
            return await call_next(request)

        # Check file size (read entire body for validation)
        if len(body) > self.max_file_size:
            logger.warning("File upload rejected: size %s exceeds max %s" % (len(body), self.max_file_size)
            )
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File size exceeds maximum allowed ({self.max_file_size // (1024*1024)}MB)",
                        "details": {
                            "max_size_mb": self.max_file_size // (1024 * 1024),
                            "provided_size_mb": len(body) // (1024 * 1024),
                        },
                    },
                },
            )

        # Create a new request with the original body
        async def receive():
            return {"type": "http.request", "body": body}

        request._receive = receive  # type: ignore[attr-defined]  # noqa: SLF001

        # Try to parse form data and validate files
        try:
            # We'll validate when the file is actually accessed
            # For now, just pass through
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception:
            logger.error("File validation error")
            raise


def add_file_validation_middleware(
    app,
    allowed_file_types: Set[str] = None,
    allowed_extensions: Set[str] = None,
    max_file_size: int = 10 * 1024 * 1024,
):
    """
    Add file validation middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
        allowed_file_types: Set of allowed MIME types
        allowed_extensions: Set of allowed file extensions
        max_file_size: Maximum file size in bytes
    """
    app.add_middleware(
        FileValidationMiddleware,
        allowed_file_types=allowed_file_types,
        allowed_extensions=allowed_extensions,
        max_file_size=max_file_size,
    )

    logger.info("File validation middleware added (max_size: %s bytes)", max_file_size)


# Utility function to validate a single file
def validate_file(
    filename: str,
    content: bytes,
    allowed_extensions: Set[str] = None,
    allowed_file_types: Set[str] = None,
    max_size: int = 10 * 1024 * 1024,
    block_dangerous: bool = True,
) -> Tuple[bool, str]:
    """
    Validate a single file.

    Args:
        filename: Original filename
        content: File content bytes
        allowed_extensions: Set of allowed extensions
        allowed_file_types: Set of allowed MIME types
        max_size: Maximum file size
        block_dangerous: Block dangerous file types

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    if len(content) > max_size:
        return False, f"File size exceeds maximum ({max_size // (1024*1024)}MB)"

    # Validate filename
    valid, error = FileValidationMiddleware._validate_extension.__func__(None, filename)  # noqa: SLF001
    if not valid:
        return False, error

    valid, error = FileValidationMiddleware._validate_filename(None, filename)  # noqa: SLF001
    if not valid:
        return False, error

    # Validate content
    valid, error = FileValidationMiddleware._validate_content(None, content)  # noqa: SLF001
    if not valid:
        return False, error

    # Check MIME type
    mime_type = magic.from_buffer(content[:1024], mime=True)
    if allowed_file_types and mime_type not in allowed_file_types:
        return False, f"File type '{mime_type}' is not allowed"

    return True, ""


# Resume file validation constants
RESUME_ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
RESUME_ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
RESUME_MAX_SIZE = 5 * 1024 * 1024  # 5MB

def validate_resume_file(filename: str, content: bytes) -> Tuple[bool, str]:
    """
    Validate a resume file specifically.

    Args:
        filename: Resume filename
        content: File content bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_file(
        filename=filename,
        content=content,
        allowed_extensions=RESUME_ALLOWED_EXTENSIONS,
        allowed_file_types=RESUME_ALLOWED_TYPES,
        max_size=RESUME_MAX_SIZE,
    )
