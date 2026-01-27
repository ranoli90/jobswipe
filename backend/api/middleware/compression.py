"""
Response Compression Middleware

Provides gzip and brotli compression for API responses.
"""

import gzip
import logging
from typing import Callable, Set

import brotli
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that compresses responses using gzip or brotli.

    Configuration:
    - COMPRESSION_TYPE: "gzip", "brotli", or "auto" (prefers gzip)
    - COMPRESSION_MIN_SIZE: Minimum response size to compress (default: 500 bytes)
    - COMPRESS_EXCLUDE_PATHS: Paths to exclude from compression
    """

    # MIME types that should not be compressed
    COMPRESSIBLE_TYPES: Set[str] = {
        "text/html",
        "text/css",
        "text/javascript",
        "text/plain",
        "text/xml",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/x-javascript",
        "application/xml+rss",
        "image/svg+xml",
    }

    # Types that benefit from compression
    TEXT_TYPES: Set[str] = {
        "text/",
        "application/json",
        "application/xml",
    }

    def __init__(self, app, compression_type: str = "gzip", min_size: int = 500):
        super().__init__(app)
        self.compression_type = compression_type
        self.min_size = min_size
        self.exclude_paths: Set[str] = set()

    def _should_compress(self, content_type: str) -> bool:
        """Check if the content type should be compressed"""
        if not content_type:
            return False

        content_type = content_type.lower().split(";")[0].strip()

        # Check if it's a compressible type
        for compressible in self.COMPRESSIBLE_TYPES:
            if content_type.startswith(compressible):
                return True

        # Check if it's a text-based type
        for text_type in self.TEXT_TYPES:
            if content_type.startswith(text_type):
                return True

        return False

    def _get_accept_encoding(self, request: Request) -> str:
        """Get the preferred encoding from Accept-Encoding header"""
        accept_encoding = request.headers.get("Accept-Encoding", "")

        if "br" in accept_encoding and self.compression_type in ("brotli", "auto"):
            return "br"
        elif "gzip" in accept_encoding:
            return "gzip"
        return ""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip compression for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip compression for streaming responses
        if request.url.path.startswith("/ws/"):
            return await call_next(request)

        # Get response
        response = await call_next(request)

        # Skip if already has content-encoding
        if response.headers.get("Content-Encoding"):
            return response

        # Check if we should compress
        content_type = response.headers.get("Content-Type", "")

        # For StreamingResponse, we can't easily check size
        if isinstance(response, StreamingResponse):
            return response

        # Check body exists and is large enough
        if not hasattr(response, "body") or not response.body:
            return response

        if len(response.body) < self.min_size:
            return response

        if not self._should_compress(content_type):
            return response

        # Get preferred encoding
        encoding = self._get_accept_encoding(request)
        if not encoding:
            return response

        try:
            if encoding == "gzip":
                compressed_body = gzip.compress(response.body)
                if len(compressed_body) >= len(response.body):
                    # Compression didn't help, skip
                    return response

                response.headers["Content-Encoding"] = "gzip"
                response.headers["Vary"] = "Accept-Encoding"
                response.body = compressed_body

            elif encoding == "br":
                compressed_body = brotli.compress(response.body)
                if len(compressed_body) >= len(response.body):
                    return response

                response.headers["Content-Encoding"] = "br"
                response.headers["Vary"] = "Accept-Encoding"
                response.body = compressed_body

        except Exception as e:
            logger.warning(f"Compression failed for {request.url.path}: {e}")
            # Fall back to uncompressed response

        return response


def add_compression_middleware(
    app, compression_type: str = "gzip", min_size: int = 500
):
    """
    Add compression middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
        compression_type: "gzip", "brotli", or "auto"
        min_size: Minimum response size to compress (bytes)
    """
    app.add_middleware(
        CompressionMiddleware, compression_type=compression_type, min_size=min_size
    )

    logger.info(
        f"Compression middleware added with {compression_type} (min_size: {min_size} bytes)"
    )
