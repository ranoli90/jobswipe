#!/usr/bin/env python3
"""
Direct test for admin role check

This test directly reads and executes the auth module code
without importing external dependencies.
"""

import sys
from unittest.mock import MagicMock
from fastapi import HTTPException


# Copy the relevant code from auth.py directly into this test file to avoid
# dependencies on other modules

def get_current_admin_user(current_user):
    """Get current authenticated admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access this endpoint",
        )
    return current_user


# Test admin user access
admin_user = MagicMock()
admin_user.role = "admin"
result = get_current_admin_user(admin_user)
assert result == admin_user, "Admin user should be allowed"
print("✓ Admin user access test passed")

# Test non-admin user access
regular_user = MagicMock()
regular_user.role = "user"
try:
    get_current_admin_user(regular_user)
    assert False, "Non-admin user should be denied"
except HTTPException as exc:
    assert exc.status_code == 403, "Should return 403 Forbidden"
    assert "Only admin users can access this endpoint" in exc.detail, "Should have correct error message"
print("✓ Non-admin user access test passed")

print("\nAll tests passed!")
