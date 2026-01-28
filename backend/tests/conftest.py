"""
Configuration for tests with mocking.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the backend directory to Python path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)


# Mock external services before importing the main module
@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services to avoid real API calls"""

    # Mock MinIO
    with patch("backend.services.storage.StorageService.__init__") as mock_storage_init:
        mock_storage_init.return_value = None

    # Mock OpenAI
    with patch(
        "backend.services.openai_service.openai_service.is_available"
    ) as mock_openai_available:
        mock_openai_available.return_value = False

    # Mock Kafka
    with patch(
        "backend.services.job_ingestion_service.JobIngestionService.init_kafka"
    ) as mock_kafka_init:
        mock_kafka_init.return_value = None

    yield


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    import sys

    # Remove any existing modules with conflicting prefixes
    for module_name in list(sys.modules.keys()):
        if module_name.startswith("backend.") or module_name in ["db", "api"]:
            del sys.modules[module_name]

    from db.database import Base

    # Reset SQLAlchemy registry to prevent duplicate class errors
    Base.registry._class_registry.clear()

    # Import models module first
    from api.main import app
    from db import models
    # Clean database before each test
    from db.database import engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Create a mock user object"""
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.profile = MagicMock()
    return user


@pytest.fixture
def mock_job():
    """Create a mock job object"""
    job = MagicMock()
    job.id = "test-job-id"
    job.title = "Test Job"
    job.company = "Test Company"
    job.description = "Test job description"
    job.apply_url = "https://example.com/apply"
    job.created_at = "2026-01-01T00:00:00"
    return job


@pytest.fixture
def mock_profile():
    """Create a mock candidate profile"""
    profile = MagicMock()
    profile.full_name = "John Doe"
    profile.phone = "123-456-7890"
    profile.location = "San Francisco, CA"
    profile.work_experience = [MagicMock(), MagicMock()]
    profile.education = [MagicMock(degree="Bachelor of Computer Science")]
    profile.skills = ["Python", "JavaScript"]
    profile.resume_file_url = "/path/to/resume.pdf"
    return profile


@pytest.fixture
def mock_application_task(mock_user, mock_job):
    """Create a mock application task"""
    task = MagicMock()
    task.id = "test-task-id"
    task.user_id = mock_user.id
    task.job_id = mock_job.id
    task.status = "queued"
    task.attempt_count = 0
    task.updated_at = "2026-01-01T00:00:00"
    return task


@pytest.fixture
def test_data():
    """Create test data for authentication tests"""
    return {
        "users": [
            {"email": "test@example.com", "password": "TestPass123!"},
            {"email": "another@example.com", "password": "AnotherPass456@"},
        ],
        "jobs": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco",
                "description": "Python, FastAPI, PostgreSQL",
            }
        ],
    }
