"""
Tests for application automation service.
"""

import asyncio
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.application_automation import \
    ApplicationAutomationService


class TestApplicationAutomationService:
    """Tests for the application automation service"""

    @pytest.mark.asyncio
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.initialize_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.close_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.navigate_to_application_page"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.handle_common_elements"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.fill_application_form"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.submit_form"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.validate_form_submission"
    )
    @patch("backend.services.application_automation.get_db")
    async def test_auto_apply_to_job_success(
        self,
        mock_get_db,
        mock_validate,
        mock_submit,
        mock_fill_form,
        mock_handle_elements,
        mock_navigate,
        mock_close,
        mock_init,
    ):
        """Test successful job application"""
        mock_validate.return_value = True

        # Create mock db session and query results
        mock_db = MagicMock()

        mock_job = MagicMock()
        mock_job.apply_url = "https://example.com/apply"
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_profile = MagicMock()
        mock_profile.full_name = "Test User"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco, CA"
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.skills = []
        mock_profile.resume_file_url = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_user,
            mock_profile,
        ]

        # Make get_db return a new iterator each time it's called
        def get_db_mock():
            return iter([mock_db])

        mock_get_db.side_effect = get_db_mock

        service = ApplicationAutomationService()

        # Set up page mock
        service.page = MagicMock()
        service.page.screenshot.return_value = b"mock-screenshot"
        service.page.wait_for_load_state.return_value = asyncio.Future()
        service.page.wait_for_load_state.return_value.set_result(None)
        service.page.wait_for_timeout.return_value = asyncio.Future()
        service.page.wait_for_timeout.return_value.set_result(None)

        # Create mock task
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_task.job_id = "test-job-id"
        mock_task.user_id = "test-user-id"

        result = await service.run_application_task(mock_task)

        assert result["success"] == True
        assert result["status"] == "success"
        assert result["submitted"] == True

        mock_init.assert_called_once()
        mock_navigate.assert_called_once()
        mock_handle_elements.assert_called_once()
        mock_fill_form.assert_called_once()
        mock_submit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.initialize_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.close_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.navigate_to_application_page"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.handle_common_elements"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.fill_application_form"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.submit_form"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.validate_form_submission"
    )
    @patch("backend.services.application_automation.get_db")
    async def test_auto_apply_to_job_failure(
        self,
        mock_get_db,
        mock_validate,
        mock_submit,
        mock_fill_form,
        mock_handle_elements,
        mock_navigate,
        mock_close,
        mock_init,
    ):
        """Test failed job application"""
        mock_validate.return_value = False

        # Create mock db session and query results
        mock_db = MagicMock()

        mock_job = MagicMock()
        mock_job.apply_url = "https://example.com/apply"
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_profile = MagicMock()
        mock_profile.full_name = "Test User"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco, CA"
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.skills = []
        mock_profile.resume_file_url = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_user,
            mock_profile,
        ]

        # Make get_db return a new iterator each time it's called
        def get_db_mock():
            return iter([mock_db])

        mock_get_db.side_effect = get_db_mock

        service = ApplicationAutomationService()

        # Set up page mock
        service.page = MagicMock()
        service.page.screenshot.return_value = b"mock-screenshot"
        service.page.wait_for_load_state.return_value = asyncio.Future()
        service.page.wait_for_load_state.return_value.set_result(None)
        service.page.wait_for_timeout.return_value = asyncio.Future()
        service.page.wait_for_timeout.return_value.set_result(None)

        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_task.job_id = "test-job-id"
        mock_task.user_id = "test-user-id"

        result = await service.run_application_task(mock_task)

        assert result["success"] == False
        assert result["status"] == "failed"
        assert result["submitted"] == False

    @pytest.mark.asyncio
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.initialize_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.close_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.navigate_to_application_page"
    )
    @patch("backend.services.application_automation.get_db")
    async def test_auto_apply_exception(
        self, mock_get_db, mock_navigate, mock_close, mock_init
    ):
        """Test exception handling in auto-apply"""
        mock_navigate.side_effect = Exception("Navigation failed")

        # Create mock db session and query results
        mock_db = MagicMock()

        mock_job = MagicMock()
        mock_job.apply_url = "https://example.com/apply"
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_profile = MagicMock()
        mock_profile.full_name = "Test User"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco, CA"
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.skills = []
        mock_profile.resume_file_url = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_user,
            mock_profile,
        ]

        # Make get_db return a new iterator each time it's called
        def get_db_mock():
            return iter([mock_db])

        mock_get_db.side_effect = get_db_mock

        service = ApplicationAutomationService()

        # Set up page mock
        service.page = MagicMock()
        service.page.screenshot.return_value = b"mock-screenshot"

        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_task.job_id = "test-job-id"
        mock_task.user_id = "test-user-id"

        result = await service.run_application_task(mock_task)

        assert result["success"] == False
        assert result["status"] == "failed"
        assert "Navigation failed" in result["message"]

    def test_parse_profile_to_dict(self):
        """Test profile parsing to dictionary format"""
        service = ApplicationAutomationService()

        # Create mock profile
        mock_profile = MagicMock()
        mock_profile.full_name = "John Doe"
        mock_profile.phone = "123-456-7890"
        mock_profile.location = "San Francisco, CA"
        mock_profile.work_experience = [MagicMock(), MagicMock()]
        mock_profile.education = [{"degree": "Bachelor of Computer Science"}]
        mock_profile.skills = ["Python", "JavaScript"]
        mock_profile.resume_file_url = "/path/to/resume.pdf"

        # Create mock user
        mock_user = MagicMock()
        mock_user.email = "john.doe@example.com"

        profile_dict = service._parse_profile_to_dict(mock_profile, mock_user)

        assert profile_dict["full_name"] == "John Doe"
        assert profile_dict["first_name"] == "John"
        assert profile_dict["last_name"] == "Doe"
        assert profile_dict["email"] == "john.doe@example.com"
        assert profile_dict["phone"] == "123-456-7890"
        assert profile_dict["location"] == "San Francisco, CA"
        assert profile_dict["city"] == "San Francisco"
        assert profile_dict["years_experience"] == 2
        assert profile_dict["highest_degree"] == "Bachelor of Computer Science"

    @pytest.mark.asyncio
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.initialize_browser"
    )
    @patch(
        "backend.services.application_automation.ApplicationAutomationService.close_browser"
    )
    async def test_playwright_browser_control(self, mock_close, mock_init):
        """Test Playwright browser control"""
        # Setup mocks
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_init.return_value = None
        mock_close.return_value = None

        service = ApplicationAutomationService()

        # Set up instance variables directly
        service.browser = mock_browser
        service.context = mock_context
        service.page = mock_page

        await service.initialize_browser()
        mock_init.assert_called_once()

        await service.close_browser()
        mock_close.assert_called_once()
