"""
Common dependencies for the FastAPI application.
This file contains dependencies that are used across multiple routers.
"""

from fastapi import Depends
from backend.api.routers.auth import get_current_user
