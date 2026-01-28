"""
Simple test to verify the admin role check functionality

This test creates a simple FastAPI app with the notifications endpoint
and tests the access control with different user roles.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.api.routers.auth import get_current_user, get_current_admin_user
from backend.api.routers.notifications import router
from backend.db.models import User

# Create a test app
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

# Test data
def test_get_current_admin_user_admin():
    """Test that admin users are allowed access"""
    # Create a mock admin user
    admin_user = MagicMock(spec=User)
    admin_user.role = "admin"
    
    # This should not raise an exception
    result = get_current_admin_user(admin_user)
    assert result == admin_user


def test_get_current_admin_user_non_admin():
    """Test that non-admin users are denied access"""
    # Create a mock regular user
    regular_user = MagicMock(spec=User)
    regular_user.role = "user"
    
    # This should raise an exception with 403 status code
    with pytest.raises(Exception) as exc_info:
        get_current_admin_user(regular_user)
    
    assert "403" in str(exc_info.value)
    assert "Only admin users can access this endpoint" in str(exc_info.value)


@patch("backend.api.routers.auth.get_current_user")
def test_notifications_stats_endpoint_admin(mock_get_current_user):
    """Test that the /stats endpoint allows admin users"""
    # Create a mock admin user
    admin_user = MagicMock(spec=User)
    admin_user.role = "admin"
    mock_get_current_user.return_value = admin_user
    
    client = TestClient(app)
    response = client.get("/v1/notifications/stats")
    
    assert response.status_code == 500  # Should fail because no DB session, but not 403


@patch("backend.api.routers.auth.get_current_user")
def test_notifications_stats_endpoint_non_admin(mock_get_current_user):
    """Test that the /stats endpoint denies non-admin users"""
    # Create a mock regular user
    regular_user = MagicMock(spec=User)
    regular_user.role = "user"
    mock_get_current_user.return_value = regular_user
    
    client = TestClient(app)
    response = client.get("/v1/notifications/stats")
    
    assert response.status_code == 403
    assert "Only admin users can access this endpoint" in response.json()["detail"]


if __name__ == "__main__":
    test_get_current_admin_user_admin()
    print("✓ test_get_current_admin_user_admin passed")
    
    test_get_current_admin_user_non_admin()
    print("✓ test_get_current_admin_user_non_admin passed")
    
    test_notifications_stats_endpoint_admin()
    print("✓ test_notifications_stats_endpoint_admin passed")
    
    test_notifications_stats_endpoint_non_admin()
    print("✓ test_notifications_stats_endpoint_non_admin passed")
    
    print("\nAll tests passed!")
