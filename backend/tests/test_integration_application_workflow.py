"""
Integration tests for job application submission workflow
Tests the full flow: API → Celery → External site application
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


class TestApplicationWorkflowIntegration:
    """Integration tests for application submission workflow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_celery(self):
        """Mock Celery task"""
        with patch('backend.api.routers.applications.celery_app') as mock_celery_app:
            mock_task = MagicMock()
            mock_celery_app.send_task.return_value = mock_task
            yield mock_celery_app

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        with patch('backend.db.database.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # Mock user lookup
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user

            # Mock job lookup
            mock_job = MagicMock()
            mock_job.id = "test-job-id"
            mock_job.title = "Test Job"
            mock_job.apply_url = "https://example.com/apply"
            mock_job.source = "greenhouse"
            mock_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_job]

            yield mock_session

    def test_application_submission_api_to_celery(self, client, mock_celery, mock_db_session):
        """Test API endpoint queues Celery task for application submission"""
        # Mock authentication
        with patch('backend.api.middleware.api_key_auth.verify_api_key', return_value="test-user-id"):
            # Mock task creation
            with patch('backend.services.application_service.create_application_task') as mock_create_task:
                mock_task = MagicMock()
                mock_task.id = "task-123"
                mock_create_task.return_value = mock_task

                response = client.post(
                    "/api/applications/submit",
                    json={
                        "job_id": "test-job-id",
                        "cover_letter": "Test cover letter"
                    },
                    headers={"X-API-Key": "test-key"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "task-123"
                assert data["status"] == "queued"

                # Verify Celery task was queued
                mock_celery.send_task.assert_called_once_with(
                    'application_agent.apply_to_job',
                    args=['task-123'],
                    queue='applications'
                )

    def test_application_workflow_with_external_site_success(self, mock_db_session):
        """Test full workflow with mocked external site success"""
        from backend.services.application_service import run_application_task

        # Mock task
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = "user-123"
        mock_task.job_id = "job-456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.id = "job-456"
        mock_job.source = "greenhouse"
        mock_job.apply_url = "https://greenhouse.example.com/apply"

        mock_profile = MagicMock()
        mock_profile.user_id = "user-123"
        mock_profile.full_name = "John Doe"
        mock_profile.email = "john@example.com"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco"
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task, mock_job, mock_profile
        ]

        # Mock resume download
        with patch('backend.services.application_service.download_file', return_value=b"resume content"):
            # Mock tempfile
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/resume.pdf"
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock GreenhouseAgent success
                with patch('backend.services.application_service.GreenhouseAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (True, None)

                    # Mock audit logger
                    with patch('backend.services.application_service.ApplicationLogger') as mock_logger_class:
                        mock_logger = MagicMock()
                        mock_logger_class.return_value = mock_logger
                        mock_logger.get_logs.return_value = []

                        # Mock file cleanup
                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task("task-123", mock_db_session)

                            assert result == True
                            assert mock_task.status == "success"
                            assert mock_task.attempt_count == 1
                            mock_apply.assert_called_once()

    def test_application_workflow_with_captcha_handling(self, mock_db_session):
        """Test workflow when CAPTCHA is encountered"""
        from backend.services.application_service import run_application_task

        # Mock task
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = "user-123"
        mock_task.job_id = "job-456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.source = "lever"
        mock_job.apply_url = "https://lever.example.com/apply"

        mock_profile = MagicMock()
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task, mock_job, mock_profile
        ]

        # Mock resume download
        with patch('backend.services.application_service.download_file', return_value=b"resume content"):
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock LeverAgent with CAPTCHA error
                with patch('backend.services.application_service.LeverAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (False, "CAPTCHA detected on application form")

                    with patch('backend.services.application_service.ApplicationLogger') as mock_logger_class:
                        mock_logger = MagicMock()
                        mock_logger_class.return_value = mock_logger

                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task("task-123", mock_db_session)

                            assert result == False
                            assert mock_task.status == "waiting_human"
                            assert "CAPTCHA" in mock_task.last_error

    def test_application_workflow_with_multiple_sources(self, mock_db_session):
        """Test workflow handles different job sources correctly"""
        from backend.services.application_service import run_application_task

        test_cases = [
            ("greenhouse", "GreenhouseAgent"),
            ("lever", "LeverAgent"),
        ]

        for source, agent_class in test_cases:
            # Mock task
            mock_task = MagicMock()
            mock_task.id = f"task-{source}"
            mock_task.user_id = "user-123"
            mock_task.job_id = f"job-{source}"
            mock_task.status = "queued"
            mock_task.attempt_count = 0

            # Mock job and profile
            mock_job = MagicMock()
            mock_job.source = source
            mock_job.apply_url = f"https://{source}.example.com/apply"

            mock_profile = MagicMock()
            mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_task, mock_job, mock_profile
            ]

            # Mock resume download
            with patch('backend.services.application_service.download_file', return_value=b"resume content"):
                with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                    mock_temp_file = MagicMock()
                    mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                    # Mock agent success
                    agent_mock = MagicMock()
                    with patch(f'backend.services.application_service.{agent_class}', agent_mock):
                        agent_mock.apply = AsyncMock(return_value=(True, None))

                        with patch('backend.services.application_service.ApplicationLogger') as mock_logger_class:
                            mock_logger = MagicMock()
                            mock_logger_class.return_value = mock_logger

                            with patch('backend.services.application_service.os.unlink'):

                                result = await run_application_task(f"task-{source}", mock_db_session)

                                assert result == True
                                agent_mock.apply.assert_called_once()

    def test_application_workflow_error_handling(self, mock_db_session):
        """Test workflow handles various error conditions"""
        from backend.services.application_service import run_application_task

        # Test missing resume
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = "user-123"
        mock_task.job_id = "job-456"

        mock_job = MagicMock()
        mock_profile = MagicMock()
        mock_profile.resume_file_url = None  # No resume

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task, mock_job, mock_profile
        ]

        result = await run_application_task("task-123", mock_db_session)

        assert result == False
        assert mock_task.status == "failed"
        assert mock_task.last_error == "No resume found"

        # Test unknown job source
        mock_task.status = "queued"
        mock_job.source = "unknown"
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task, mock_job, mock_profile
        ]

        with patch('backend.services.application_service.download_file', return_value=b"resume"):
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file:

                    result = await run_application_task("task-123", mock_db_session)

                    assert result == False
                    assert mock_task.status == "needs_review"