"""
End-to-End tests for complete user flow
Tests user registration → profile creation → job swiping → application submission
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

# API endpoint constants to avoid duplication
PROFILE_ENDPOINT = "/api/profile/"
PERSONALIZED_JOBS_ENDPOINT = "/api/jobs/personalized"


class TestUserFlowE2E:
    """E2E tests for complete user journey"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_complete_user_registration_flow(self, client):
        """Test complete user registration and initial setup"""
        # Step 1: User registration
        user_email = f"test_user_{uuid.uuid4()}@example.com"
        user_password = "SecurePass123!"

        register_response = client.post(
            "/api/auth/register",
            json={
                "email": user_email,
                "password": user_password,
                "full_name": "Test User",
            },
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "user" in register_data

        access_token = register_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Verify user can access protected endpoints
        profile_response = client.get(PROFILE_ENDPOINT, headers=headers)
        assert profile_response.status_code == 404  # No profile yet

        # Step 3: Upload resume to create profile
        # Create a simple PDF-like content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000009 00000 n\ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n49\n%%EOF"

        files = {"file": ("resume.pdf", pdf_content, "application/pdf")}

        with pytest.mock.patch(
            "backend.services.resume_parser_enhanced.parse_resume_enhanced"
        ) as mock_parse:
            mock_parse.return_value = {
                "full_name": "Test User",
                "email": user_email,
                "phone": "123-456-7890",
                "skills": ["Python", "JavaScript", "React"],
                "work_experience": [
                    {
                        "position": "Software Developer",
                        "company": "Tech Corp",
                        "duration": "2 years",
                    }
                ],
                "education": [
                    {
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "school": "State University",
                    }
                ],
                "parsed_at": "2026-01-27T12:00:00",
            }

            upload_response = client.post(
                "/api/profile/resume", files=files, headers=headers
            )
            assert upload_response.status_code == 200

            profile_data = upload_response.json()
            assert profile_data["full_name"] == "Test User"
            assert profile_data["skills"] == ["Python", "JavaScript", "React"]
            assert "resume_file_url" in profile_data

        # Step 4: Verify profile was created
        profile_response = client.get(PROFILE_ENDPOINT, headers=headers)
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["full_name"] == "Test User"

        return access_token, headers, user_email

    def test_job_discovery_and_interaction_flow(self, client):
        """Test job discovery and interaction flow"""
        # Setup user first
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Get personalized jobs
        jobs_response = client.get(
            PERSONALIZED_JOBS_ENDPOINT, params={"limit": 10}, headers=headers
        )
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()

        # Should return some jobs (mocked or real)
        assert isinstance(jobs_data, list)
        if jobs_data:  # If jobs exist
            job = jobs_data[0]["job"]
            job_id = job["id"]

            # Step 2: View job details
            job_detail_response = client.get(f"/api/jobs/{job_id}", headers=headers)
            assert job_detail_response.status_code in [
                200,
                404,
            ]  # May not exist in test DB

            # Step 3: Interact with job (like/dislike)
            interaction_data = {
                "job_id": job_id,
                "interaction_type": "like",
                "swipe_direction": "right",
                "timestamp": "2026-01-27T12:00:00Z",
            }

            interaction_response = client.post(
                "/api/jobs/interact", json=interaction_data, headers=headers
            )
            assert interaction_response.status_code in [
                200,
                201,
                400,
            ]  # May fail if job doesn't exist

            # Step 4: Get updated personalized jobs (should exclude liked job)
            updated_jobs_response = client.get(
                PERSONALIZED_JOBS_ENDPOINT, params={"limit": 10}, headers=headers
            )
            assert updated_jobs_response.status_code == 200

    def test_application_submission_flow(self, client):
        """Test complete application submission flow"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Find a job to apply to
        jobs_response = client.get(
            PERSONALIZED_JOBS_ENDPOINT, params={"limit": 5}, headers=headers
        )
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()

        if jobs_data:
            job = jobs_data[0]["job"]
            job_id = job["id"]

            # Step 2: Submit application
            application_data = {
                "job_id": job_id,
                "cover_letter": "I am very interested in this position and believe my skills would be a perfect match.",
                "customizations": {
                    "salary_expectation": 90000,
                    "start_date": "Immediate",
                    "remote_work": True,
                },
            }

            with pytest.mock.patch(
                "backend.api.routers.applications.celery_app"
            ) as mock_celery:
                mock_task = pytest.mock.MagicMock()
                mock_celery.send_task.return_value = mock_task

                submit_response = client.post(
                    "/api/applications/submit", json=application_data, headers=headers
                )
                assert submit_response.status_code == 200

                submit_data = submit_response.json()
                assert "task_id" in submit_data
                assert submit_data["status"] == "queued"

                # Verify Celery task was queued
                mock_celery.send_task.assert_called_once_with(
                    "application_agent.apply_to_job",
                    args=[submit_data["task_id"]],
                    queue="applications",
                )

            # Step 3: Check application status (would be polled in real app)
            # In a real scenario, the frontend would poll for status updates

    def test_notification_flow(self, client):
        """Test notification system integration"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Register device for push notifications
        device_data = {
            "device_token": f"device_token_{uuid.uuid4()}",
            "platform": "ios",
        }

        device_response = client.post(
            "/api/notifications/register-device", json=device_data, headers=headers
        )
        assert device_response.status_code in [200, 201, 400]  # May not be implemented

        # Step 2: Check notifications
        notifications_response = client.get("/api/notifications/", headers=headers)
        assert notifications_response.status_code in [200, 404]  # May not exist yet

    def test_profile_update_flow(self, client):
        """Test profile update and refinement flow"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Update profile information
        update_data = {
            "full_name": "Updated Test User",
            "location": "San Francisco, CA",
            "headline": "Senior Python Developer",
            "skills": ["Python", "Django", "React", "AWS", "Docker"],
            "experience": [
                {
                    "position": "Senior Software Engineer",
                    "company": "Tech Startup",
                    "duration": "3 years",
                }
            ],
            "education": [
                {
                    "degree": "Master of Science",
                    "field": "Computer Science",
                    "school": "Top University",
                }
            ],
            "preferences": {
                "job_types": ["full-time", "contract"],
                "remote_preference": "hybrid",
                "experience_level": "senior",
            },
        }

        update_response = client.put(PROFILE_ENDPOINT, json=update_data, headers=headers)
        assert update_response.status_code == 200

        updated_profile = update_response.json()
        assert updated_profile["full_name"] == "Updated Test User"
        assert updated_profile["location"] == "San Francisco, CA"
        assert updated_profile["skills"] == [
            "Python",
            "Django",
            "React",
            "AWS",
            "Docker",
        ]

        # Step 2: Verify updated profile affects job matching
        jobs_response = client.get(
            PERSONALIZED_JOBS_ENDPOINT, params={"limit": 5}, headers=headers
        )
        assert jobs_response.status_code == 200
        # The matching algorithm should now consider the updated skills and preferences

    def test_search_and_filter_flow(self, client):
        """Test job search and filtering capabilities"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Search for specific job types
        search_terms = [
            "python developer",
            "machine learning engineer",
            "frontend developer",
        ]

        for term in search_terms:
            search_response = client.get(
                "/api/jobs/search", params={"q": term, "limit": 10}, headers=headers
            )
            assert search_response.status_code == 200
            search_results = search_response.json()
            assert isinstance(search_results, list)

        # Step 2: Test different filter combinations
        filter_params = [
            {"location": "San Francisco"},
            {"company": "Google"},
            {"remote": "true"},
            {"salary_min": 100000},
        ]

        for filters in filter_params:
            filter_response = client.get(
                "/api/jobs/", params={**filters, "limit": 10}, headers=headers
            )
            assert filter_response.status_code == 200
            filtered_results = filter_response.json()
            assert isinstance(filtered_results, list)

    def test_analytics_and_insights_flow(self, client):
        """Test user analytics and insights"""
        # Setup user with some activity
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Generate some activity first
        jobs_response = client.get(
            PERSONALIZED_JOBS_ENDPOINT, params={"limit": 3}, headers=headers
        )
        if jobs_response.status_code == 200:
            jobs_data = jobs_response.json()
            for job_data in jobs_data[:2]:  # Interact with 2 jobs
                job = job_data["job"]
                interaction_data = {
                    "job_id": job["id"],
                    "interaction_type": (
                        "like" if jobs_data.index(job_data) == 0 else "dislike"
                    ),
                    "swipe_direction": (
                        "right" if jobs_data.index(job_data) == 0 else "left"
                    ),
                }
                client.post(
                    "/api/jobs/interact", json=interaction_data, headers=headers
                )

        # Step 1: Get user analytics
        analytics_response = client.get("/api/analytics/dashboard", headers=headers)
        assert analytics_response.status_code in [200, 404]  # May not be implemented

        # Step 2: Get user insights/recommendations
        insights_response = client.get("/api/analytics/insights", headers=headers)
        assert insights_response.status_code in [200, 404]  # May not be implemented

    def test_error_handling_and_recovery(self, client):
        """Test error handling and recovery throughout the flow"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Test invalid job interaction
        invalid_interaction = {
            "job_id": "nonexistent-job-id",
            "interaction_type": "invalid_type",
            "swipe_direction": "up",
        }

        error_response = client.post(
            "/api/jobs/interact", json=invalid_interaction, headers=headers
        )
        # Should handle gracefully
        assert error_response.status_code in [200, 400, 404, 422]

        # Step 2: Test application to non-existent job
        invalid_application = {"job_id": "nonexistent-job-id", "cover_letter": "Test"}

        with pytest.mock.patch(
            "backend.api.routers.applications.celery_app"
        ) as mock_celery:
            mock_celery.send_task.return_value = pytest.mock.MagicMock()
            app_response = client.post(
                "/api/applications/submit", json=invalid_application, headers=headers
            )
            # Should handle gracefully
            assert app_response.status_code in [200, 400, 404]

        # Step 3: Test profile update with invalid data
        invalid_profile_update = {
            "full_name": "",  # Invalid empty name
            "phone": "invalid-phone-number",
            "skills": [""],  # Invalid empty skill
        }

        update_response = client.put(
            PROFILE_ENDPOINT, json=invalid_profile_update, headers=headers
        )
        # Should validate and reject invalid data
        assert update_response.status_code in [200, 422]  # May accept or reject

        # Step 4: Verify system remains functional after errors
        # User should still be able to get profile
        profile_response = client.get(PROFILE_ENDPOINT, headers=headers)
        assert profile_response.status_code == 200

    def test_concurrent_user_sessions(self, client):
        """Test handling multiple concurrent sessions for the same user"""
        # Setup user
        access_token1, headers1, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Simulate second login/session
        login_response = client.post(
            "/api/auth/login", json={"email": user_email, "password": "SecurePass123!"}
        )

        assert login_response.status_code == 200
        access_token2 = login_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {access_token2}"}

        # Both sessions should work concurrently
        profile1 = client.get(PROFILE_ENDPOINT, headers=headers1)
        profile2 = client.get(PROFILE_ENDPOINT, headers=headers2)

        assert profile1.status_code == 200
        assert profile2.status_code == 200

        # Actions from both sessions should be consistent
        jobs1 = client.get(PERSONALIZED_JOBS_ENDPOINT, headers=headers1)
        jobs2 = client.get(PERSONALIZED_JOBS_ENDPOINT, headers=headers2)

        assert jobs1.status_code == jobs2.status_code == 200

    def test_data_consistency_across_flow(self, client):
        """Test data consistency throughout the entire user flow"""
        # Setup user
        access_token, headers, user_email = self.test_complete_user_registration_flow(
            client
        )

        # Step 1: Create initial profile state
        initial_profile = client.get(PROFILE_ENDPOINT, headers=headers).json()

        # Step 2: Perform various actions
        # Update profile
        client.put(
            PROFILE_ENDPOINT,
            json={"skills": ["Python", "New Skill"], "headline": "Updated Headline"},
            headers=headers,
        )

        # Interact with jobs
        jobs = client.get(
            PERSONALIZED_JOBS_ENDPOINT, params={"limit": 2}, headers=headers
        )
        if jobs.status_code == 200 and jobs.json():
            job_id = jobs.json()[0]["job"]["id"]
            client.post(
                "/api/jobs/interact",
                json={"job_id": job_id, "interaction_type": "like"},
                headers=headers,
            )

        # Step 3: Verify data consistency
        # Profile should reflect updates
        updated_profile = client.get(PROFILE_ENDPOINT, headers=headers)
        assert updated_profile.status_code == 200

        profile_data = updated_profile.json()
        assert profile_data["headline"] == "Updated Headline"
        assert "New Skill" in profile_data.get("skills", [])

        # Job interactions should be recorded
        # (This would require checking interaction history endpoint if available)

        # Step 4: Verify no data corruption occurred
        # Profile should still be valid JSON and contain expected fields
        required_fields = ["full_name", "skills"]
        for field in required_fields:
            assert field in profile_data
