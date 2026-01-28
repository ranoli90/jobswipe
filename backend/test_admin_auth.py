"""
Standalone test for admin role check

This test focuses on testing the get_current_admin_user dependency directly
without importing other modules that require external dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from unittest.mock import MagicMock
from fastapi import HTTPException
from api.routers.auth import get_current_admin_user


def test_get_current_admin_user_admin():
    """Test that admin users are allowed access"""
    # Create a mock admin user
    admin_user = MagicMock()
    admin_user.role = "admin"
    
    # This should not raise an exception
    result = get_current_admin_user(admin_user)
    assert result == admin_user


def test_get_current_admin_user_non_admin():
    """Test that non-admin users are denied access"""
    # Create a mock regular user
    regular_user = MagicMock()
    regular_user.role = "user"
    
    # This should raise an exception with 403 status code
    try:
        get_current_admin_user(regular_user)
        assert False, "Expected exception was not raised"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "Only admin users can access this endpoint" in exc.detail


if __name__ == "__main__":
    test_get_current_admin_user_admin()
    print("✓ test_get_current_admin_user_admin passed")
    
    test_get_current_admin_user_non_admin()
    print("✓ test_get_current_admin_user_non_admin passed")
    
    print("\nAll tests passed!")
