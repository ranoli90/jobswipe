"""
Common dependencies for the FastAPI application.
This file contains dependencies that are used across multiple routers.
"""

from fastapi import Depends

# Import get_current_user from auth router to avoid circular imports
def get_current_user():
    from backend.api.routers.auth import get_current_user as auth_get_current_user
    return auth_get_current_user()
