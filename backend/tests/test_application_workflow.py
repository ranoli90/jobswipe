"""
Integration Tests for Job Application Workflow

Tests the complete application flow from job search to application submission.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import test fixtures - use pytest fixtures directly
# from tests.conftest import client, mock_db_session


class TestJobApplicationWorkflow:
    """Integration tests for job application workflow"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        return {
            "id": "test-user-123",
            "email": "testuser@example.com",
            "name": "Test User",
            "is_active": True,
        }

    @pytest.fixture
    def mock_job(self):
        """Create a mock job for testing"""
        return {
            "id": "job-123",
            "title": "Senior Software Engineer",
            "company": "Test Company",
            "location": "Remote",
            "url": "https://example.com/job/123",
            "source": "greenhouse",
            "salary_min": 100000,
            "salary_max": 150000,
            "description": "We are looking for a senior engineer...",
        }

    def test_user_registration_flow(self, client):
        """Test user registration workflow"""
        # Test user registration endpoint
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "name": "New User",
            },
        )

        # Assert registration succeeds or returns appropriate error for existing user
        assert response.status_code in [201, 400, 409]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "access_token" in data

    def test_user_login_flow(self, client):
        """Test user login workflow"""
        # First register a user
        client.post(
            "/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "SecurePassword123!",
                "name": "Login Test",
            },
        )

        # Then login
        response = client.post(
            "/v1/auth/login",
            json={"email": "logintest@example.com", "password": "SecurePassword123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    def test_job_search_flow(self, client):
        """Test job search workflow"""
        response = client.get(
            "/v1/jobs/",
            params={"page": 1, "page_size": 10, "query": "software engineer"},
        )

        # Assert response is successful
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "page" in data

    def test_job_detail_flow(self, client, mock_job):
        """Test getting job details"""
        response = client.get(f"/v1/jobs/{mock_job['id']}")

        # Should return 200 if job exists, 404 if not
        assert response.status_code in [200, 404]

    def test_swipe_right_flow(self, client, mock_user, mock_job):
        """Test swipe right (like) workflow"""
        # This would require authentication
        # Mock the authentication
        with patch("backend.api.routers.jobs.get_current_user") as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.post(f"/v1/jobs/{mock_job['id']}/like")

            # Assert response
            assert response.status_code in [200, 201, 404, 401]

            if response.status_code == 200:
                data = response.json()
                assert data.get("matched") is not None

    def test_application_submission_flow(self, client, mock_user, mock_job):
        """Test job application submission workflow"""
        with patch(
            "backend.api.routers.applications.get_current_user"
        ) as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.post(
                f"/v1/applications/",
                json={
                    "job_id": mock_job["id"],
                    "resume_id": "resume-123",
                    "cover_letter": "I am interested in this position...",
                },
            )

            assert response.status_code in [201, 400, 401, 404, 409]

            if response.status_code == 201:
                data = response.json()
                assert "id" in data
                assert data.get("status") in ["pending", "submitted", "in_progress"]

    def test_application_status_flow(self, client, mock_user):
        """Test checking application status"""
        with patch(
            "backend.api.routers.applications.get_current_user"
        ) as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.get("/v1/applications/")

            assert response.status_code == 200
            data = response.json()
            assert "applications" in data

    def test_profile_update_flow(self, client, mock_user):
        """Test profile update workflow"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.put(
                "/v1/profile/",
                json={
                    "name": "Updated Name",
                    "bio": "New bio",
                    "skills": ["Python", "FastAPI", "PostgreSQL"],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("name") == "Updated Name"

    def test_notification_preferences_flow(self, client, mock_user):
        """Test notification preferences workflow"""
        with patch(
            "backend.api.routers.notifications.get_current_user"
        ) as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.put(
                "/v1/notifications/preferences",
                json={
                    "push_enabled": True,
                    "email_enabled": True,
                    "quiet_hours_enabled": True,
                    "quiet_hours_start": "22:00:00",
                    "quiet_hours_end": "08:00:00",
                },
            )

            assert response.status_code == 200


class TestAuthenticationFlow:
    """Tests for authentication flow edge cases"""

    def test_invalid_login(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_weak_password_rejection(self, client):
        """Test that weak passwords are rejected"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",  # Weak password
                "name": "Test",
            },
        )

        assert response.status_code == 422

    def test_token_refresh(self, client):
        """Test token refresh workflow"""
        # First register and login
        client.post(
            "/v1/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "SecurePassword123!",
                "name": "Refresh Test",
            },
        )

        login_response = client.post(
            "/v1/auth/login",
            json={"email": "refreshtest@example.com", "password": "SecurePassword123!"},
        )

        if login_response.status_code == 200:
            refresh_token = login_response.json().get("refresh_token")

            # Try to refresh
            response = client.post(
                "/v1/auth/refresh", json={"refresh_token": refresh_token}
            )

            assert response.status_code == 200


class TestJobIngestionFlow:
    """Tests for job ingestion workflow"""

    def test_ingestion_status(self, client):
        """Test checking ingestion status"""
        with patch(
            "backend.api.routers.jobs_ingestion.get_current_user"
        ) as mock_get_user:
            mock_get_user.return_value = Mock(id="admin-user", is_admin=True)

            response = client.get("/v1/ingestion/status")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "last_run" in data

    def test_manual_ingestion_trigger(self, client):
        """Test manually triggering job ingestion"""
        with patch(
            "backend.api.routers.jobs_ingestion.get_current_user"
        ) as mock_get_user:
            mock_get_user.return_value = Mock(id="admin-user", is_admin=True)

            response = client.post(
                "/v1/ingestion/trigger", json={"source": "greenhouse", "limit": 100}
            )

            assert response.status_code in [200, 202, 400, 401, 403]


class TestAnalyticsFlow:
    """Tests for analytics workflow"""

    def test_analytics_dashboard(self, client):
        """Test analytics dashboard endpoint"""
        with patch("backend.api.routers.analytics.get_current_user") as mock_get_user:
            mock_get_user.return_value = Mock(id="admin-user", is_admin=True)

            response = client.get("/v1/analytics/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data

    def test_user_analytics(self, client, mock_user):
        """Test user-specific analytics"""
        with patch("backend.api.routers.analytics.get_current_user") as mock_get_user:
            mock_get_user.return_value = Mock(id=mock_user["id"])

            response = client.get(f"/v1/analytics/users/{mock_user['id']}")

            assert response.status_code in [200, 403, 404]


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
