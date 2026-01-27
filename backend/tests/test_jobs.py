"""
Jobs Router Tests

Tests for jobs endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_feed_without_token(client: TestClient):
    """Test getting job feed without authentication"""
    response = client.get("/v1/jobs/feed")
    assert response.status_code == 401


def test_get_feed_authenticated(client: TestClient, test_data):
    """Test getting job feed with authentication"""
    user_data = test_data["users"][0]

    # Register and login
    client.post(
        "/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )

    login_response = client.post(
        "/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )

    token = login_response.json()["access_token"]

    # Get job feed
    response = client.get("/v1/jobs/feed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_job_detail(client: TestClient, test_data):
    """Test getting job detail"""
    user_data = test_data["users"][0]

    # Register and login
    client.post(
        "/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )

    login_response = client.post(
        "/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )

    token = login_response.json()["access_token"]

    job_data = test_data["jobs"][0]

    # Should fail - job doesn't exist
    response = client.get(
        f"/v1/jobs/{job_data['id']}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_swipe_job(client: TestClient, test_data):
    """Test swiping job"""
    user_data = test_data["users"][0]

    # Register and login
    client.post(
        "/v1/auth/register",
        json={"email": user_data["email"], "password": user_data["password"]},
    )

    login_response = client.post(
        "/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )

    token = login_response.json()["access_token"]

    job_data = test_data["jobs"][0]

    # Should fail - job doesn't exist
    response = client.post(
        f"/v1/jobs/{job_data['id']}/swipe",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "right"},
    )

    assert response.status_code == 404
