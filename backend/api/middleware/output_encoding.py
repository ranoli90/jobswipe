import html
import json
import logging
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class OutputEncodingMiddleware(BaseHTTPMiddleware):
    """Middleware to encode HTML entities in JSON responses for XSS protection"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if isinstance(response, JSONResponse):
            # Get the original data
            original_data = response.body
            try:
                data = json.loads(original_data.decode("utf-8"))
                # Encode HTML entities in all string values
                encoded_data = self._encode_html_in_data(data)
                # Create new response with encoded data
                encoded_body = json.dumps(encoded_data).encode("utf-8")
                response.body = encoded_body
                # Update content-length header
                response.headers["content-length"] = str(len(encoded_body))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not valid JSON, leave as is
                pass

        return response

    def _encode_html_in_data(self, data):
        """Recursively encode HTML entities in data"""
        if isinstance(data, dict):
            return {
                key: self._encode_html_in_data(value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._encode_html_in_data(item) for item in data]
        elif isinstance(data, str):
            return html.escape(data, quote=False)  # Don't escape quotes in JSON
        

        return data
