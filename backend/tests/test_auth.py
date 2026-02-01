"""
Authentication Tests

Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_register(client: TestClient, test_data):
    """Test user registration"""
    user_data = test_data["users"][0]

    response = client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == user_data["email"]
    assert "id" in data["user"]


def test_register_duplicate_email(client: TestClient, test_data):
    """Test duplicate email registration"""
    user_data = test_data["users"][0]

    # First registration
    client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )

    # Second registration should fail
    response = client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": "DifferentPass123!"},
    )

    assert response.status_code == 400


def test_login(client: TestClient, test_data):
    """Test user login"""
    user_data = test_data["users"][0]

    # First register
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    print("Register response status:", register_response.status_code)
    print("Register response body:", register_response.json())
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
        )
    print("Login response status:", response.status_code)
    print("Login response body:", response.json())

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client: TestClient, test_data):
    """Test login with incorrect password"""
    user_data = test_data["users"][0]

    # First register
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert register_response.status_code == 200, f"Register failed: {register_response.text}"

    # Login with incorrect password
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_get_me(client: TestClient, test_data):
    """Test getting current user info"""
    user_data = test_data["users"][0]

    # Register
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert register_response.status_code == 200, f"Register failed: {register_response.text}"

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    data = login_response.json()
    assert "access_token" in data, "Missing access_token in login response"
    token = data["access_token"]

    # Get current user
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == user_data["email"]
