import html
import json
import logging
import re
from typing import Any, Callable, Dict

import magic
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize user inputs to prevent injection attacks"""
    
    # Default maximum file size: 10MB
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Default allowed MIME types for file uploads
    DEFAULT_ALLOWED_MIME_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    # Dangerous HTML tags to remove
    DANGEROUS_HTML_TAGS = ["script", "iframe", "object", "embed"]

    def __init__(
        self,
        app: Callable,
        allowed_mime_types: list = None,
        max_file_size: int = None,
    ):
        super().__init__(app)
        self.allowed_mime_types = allowed_mime_types or self.DEFAULT_ALLOWED_MIME_TYPES
        self.max_file_size = max_file_size or self.DEFAULT_MAX_FILE_SIZE

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Sanitize query parameters
            sanitized_query = self._sanitize_query_params(dict(request.query_params))
            request.scope["query_params"] = sanitized_query

            # Sanitize request body based on content type
            content_type = request.headers.get("content-type", "").lower()

            if "application/json" in content_type:
                body = await request.body()
                if body:
                    try:
                        json_data = json.loads(body.decode("utf-8"))
                        sanitized_data = self._sanitize_json_data(json_data)
                        # Replace the body with sanitized version
                        sanitized_body = json.dumps(sanitized_data).encode("utf-8")
                        request._body = sanitized_body
                    except json.JSONDecodeError:
                        security_logger.warning(
                            "Invalid JSON in request body",
                            extra={
                                "ip": (
                                    request.client.host if request.client else "unknown"
                                ),
                                "path": str(request.url.path),
                                "method": request.method,
                            },
                        )
                        raise HTTPException(status_code=400, detail="Invalid JSON")

            elif (
                "multipart/form-data" in content_type
                or "application/x-www-form-urlencoded" in content_type
            ):
                # For form data, we'll rely on Pydantic validation in endpoints
                # But we can log potential issues
                pass

            # Check file uploads if any
            if hasattr(request, "files") or "multipart" in content_type:
                await self._validate_file_uploads(request)

            response = await call_next(request)
            return response

        except Exception as e:
            security_logger.error(
                f"Input sanitization error: {str(e)}",
                extra={
                    "ip": request.client.host if request.client else "unknown",
                    "path": str(request.url.path),
                    "method": request.method,
                },
            )
            raise

    def _sanitize_query_params(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters"""
        sanitized = {}
        for key, value in query_params.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string by removing dangerous content and encoding HTML"""
        if not isinstance(text, str):
            return text

        # Remove dangerous HTML tags
        for tag in self.DANGEROUS_HTML_TAGS:
            pattern = rf"<{tag}[^>]*>.*?</{tag}>"
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

        # Encode HTML entities
        text = html.escape(text, quote=True)

        return text

    async def _validate_file_uploads(self, request: Request):
        """Validate file uploads for MIME type and size"""
        try:
            # For simplicity, we'll check in the endpoint where files are processed
            # This is a placeholder for file validation logic
            pass
        except Exception as e:
            security_logger.warning(
                f"File upload validation error: {str(e)}",
                extra={
                    "ip": request.client.host if request.client else "unknown",
                    "path": str(request.url.path),
                },
            )
