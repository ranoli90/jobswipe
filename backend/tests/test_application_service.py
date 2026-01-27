"""
Unit tests for ApplicationService
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.application_service import (create_application_task,
                                                  run_application_task)


class TestApplicationService:
    """Test cases for ApplicationService"""

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_create_application_task_success(self, mock_get_db):
        """Test create_application_task successful creation"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock no existing task
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock task creation
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.status = "queued"

        with patch('backend.services.application_service.ApplicationTask', return_value=mock_task) as mock_task_class:
            result = await create_application_task("user123", "job456", mock_db)

            assert result == mock_task
            mock_task_class.assert_called_once()
            mock_db.add.assert_called_once_with(mock_task)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_task)

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_create_application_task_existing(self, mock_get_db):
        """Test create_application_task when task already exists"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock existing task
        existing_task = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_task

        result = await create_application_task("user123", "job456", mock_db)

        assert result == existing_task
        # Should not create new task
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_create_application_task_exception(self, mock_get_db):
        """Test create_application_task with database exception"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock no existing task
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # Mock commit to raise exception
        mock_db.commit.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            await create_application_task("user123", "job456", mock_db)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_success_greenhouse(self, mock_get_db):
        """Test run_application_task successful greenhouse application"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock job
        mock_job = MagicMock()
        mock_job.id = "job456"
        mock_job.source = "greenhouse"
        mock_job.apply_url = "https://greenhouse.example.com/apply"

        # Mock profile
        mock_profile = MagicMock()
        mock_profile.user_id = "user123"
        mock_profile.full_name = "John Doe"
        mock_profile.email = "john@example.com"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco"
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock storage download
        with patch('backend.services.application_service.download_file', return_value=b"resume content") as mock_download:
            # Mock tempfile
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/resume.pdf"
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock GreenhouseAgent
                with patch('backend.services.application_service.GreenhouseAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (True, None)  # Success, no error

                    # Mock audit logger
                    mock_audit_logger = MagicMock()
                    with patch('backend.services.application_service.ApplicationLogger', return_value=mock_audit_logger):
                        # Mock os.unlink
                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task(str(mock_task.id), mock_db)

                            assert result is True
                            assert mock_task.status == "success"
                            assert mock_task.attempt_count == 1
                            mock_apply.assert_called_once()
                            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_success_lever(self, mock_get_db):
        """Test run_application_task successful lever application"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock job
        mock_job = MagicMock()
        mock_job.id = "job456"
        mock_job.source = "lever"
        mock_job.apply_url = "https://lever.example.com/apply"

        # Mock profile
        mock_profile = MagicMock()
        mock_profile.user_id = "user123"
        mock_profile.full_name = "John Doe"
        mock_profile.email = "john@example.com"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco"
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock storage download
        with patch('backend.services.application_service.download_file', return_value=b"resume content"):
            # Mock tempfile
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/resume.pdf"
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock LeverAgent
                with patch('backend.services.application_service.LeverAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (True, None)  # Success, no error

                    # Mock audit logger
                    mock_audit_logger = MagicMock()
                    with patch('backend.services.application_service.ApplicationLogger', return_value=mock_audit_logger):
                        # Mock os.unlink
                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task(str(mock_task.id), mock_db)

                            assert result is True
                            assert mock_task.status == "success"
                            mock_apply.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_task_not_found(self, mock_get_db):
        """Test run_application_task when task not found"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await run_application_task("nonexistent-task-id", mock_db)

        assert result is False

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_job_not_found(self, mock_get_db):
        """Test run_application_task when job not found"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task exists but job doesn't
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, None, None]

        result = await run_application_task(str(mock_task.id), mock_db)

        assert result is False
        assert mock_task.status == "failed"
        assert mock_task.last_error == "Job or profile not found"

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_no_resume(self, mock_get_db):
        """Test run_application_task when no resume available"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.source = "greenhouse"
        mock_profile = MagicMock()
        mock_profile.resume_file_url = None  # No resume

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        result = await run_application_task(str(mock_task.id), mock_db)

        assert result is False
        assert mock_task.status == "failed"
        assert mock_task.last_error == "No resume found"

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_download_resume_failed(self, mock_get_db):
        """Test run_application_task when resume download fails"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.source = "greenhouse"
        mock_profile = MagicMock()
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock download_file to return None (failed)
        with patch('backend.services.application_service.download_file', return_value=None):
            result = await run_application_task(str(mock_task.id), mock_db)

            assert result is False
            assert mock_task.status == "failed"
            assert mock_task.last_error == "No resume found"

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_unknown_source(self, mock_get_db):
        """Test run_application_task with unknown job source"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"

        # Mock job with unknown source
        mock_job = MagicMock()
        mock_job.source = "unknown"
        mock_profile = MagicMock()
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock resume download
        with patch('backend.services.application_service.download_file', return_value=b"resume"):
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file:

                    result = await run_application_task(str(mock_task.id), mock_db)

                    assert result is False
                    assert mock_task.status == "needs_review"

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_captcha_detected(self, mock_get_db):
        """Test run_application_task when CAPTCHA is detected"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.source = "greenhouse"
        mock_profile = MagicMock()
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock resume handling
        with patch('backend.services.application_service.download_file', return_value=b"resume"):
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock GreenhouseAgent with CAPTCHA error
                with patch('backend.services.application_service.GreenhouseAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (False, "CAPTCHA detected on page")

                    with patch('backend.services.application_service.ApplicationLogger'):
                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task(str(mock_task.id), mock_db)

                            assert result is False
                            assert mock_task.status == "waiting_human"
                            assert "CAPTCHA" in mock_task.last_error

    @pytest.mark.asyncio
    @patch('backend.services.application_service.get_db')
    async def test_run_application_task_application_failed(self, mock_get_db):
        """Test run_application_task when application fails"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = "user123"
        mock_task.job_id = "job456"
        mock_task.status = "queued"
        mock_task.attempt_count = 0

        # Mock job and profile
        mock_job = MagicMock()
        mock_job.source = "greenhouse"
        mock_profile = MagicMock()
        mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_task, mock_job, mock_profile]

        # Mock resume handling
        with patch('backend.services.application_service.download_file', return_value=b"resume"):
            with patch('backend.services.application_service.tempfile.NamedTemporaryFile') as mock_tempfile:
                mock_temp_file = MagicMock()
                mock_tempfile.return_value.__enter__.return_value = mock_temp_file

                # Mock GreenhouseAgent failure
                with patch('backend.services.application_service.GreenhouseAgent.apply', new_callable=AsyncMock) as mock_apply:
                    mock_apply.return_value = (False, "Application submission failed")

                    with patch('backend.services.application_service.ApplicationLogger'):
                        with patch('backend.services.application_service.os.unlink'):

                            result = await run_application_task(str(mock_task.id), mock_db)

                            assert result is False
                            assert mock_task.status == "failed"
                            assert mock_task.last_error == "Application submission failed"