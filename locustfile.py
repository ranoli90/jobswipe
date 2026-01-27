"""
Locust load testing file for JobSwipe API
Tests concurrent user swiping and API performance under load
"""

import json
import os
import random
import uuid

from locust import HttpUser, between, constant, task


class JobSwipeUser(HttpUser):
    """Simulates a JobSwipe user performing typical actions"""

    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Setup user session on start"""
        self.user_id = str(uuid.uuid4())
        self.auth_token = None
        self.profile_created = False

        # Register/Login user
        self._register_or_login()

    def _register_or_login(self):
        """Register a new user or login with existing credentials"""
        # For load testing, we'll use a pool of pre-created test users
        test_users = [
            {"email": f"test_user_{i}@example.com", "password": "testpass123"}
            for i in range(1, 101)  # 100 test users
        ]

        # Randomly select a test user
        user = random.choice(test_users)

        # Attempt login
        login_response = self.client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": user["password"]},
        )

        if login_response.status_code == 200:
            self.auth_token = login_response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        else:
            # User doesn't exist, register them
            register_response = self.client.post(
                "/api/auth/register",
                json={
                    "email": user["email"],
                    "password": user["password"],
                    "full_name": f"Test User {random.randint(1, 100)}",
                },
            )

            if register_response.status_code == 201:
                self.auth_token = register_response.json().get("access_token")
                self.client.headers.update(
                    {"Authorization": f"Bearer {self.auth_token}"}
                )
                self._create_test_profile()

    def _create_test_profile(self):
        """Create a test profile for the user"""
        if not self.profile_created:
            skills = random.sample(
                [
                    "Python",
                    "JavaScript",
                    "Java",
                    "C++",
                    "React",
                    "Django",
                    "Node.js",
                    "AWS",
                    "Docker",
                    "Kubernetes",
                    "SQL",
                    "MongoDB",
                ],
                random.randint(3, 8),
            )

            profile_data = {
                "full_name": f"Test User {random.randint(1, 1000)}",
                "skills": skills,
                "location": random.choice(
                    ["San Francisco", "New York", "London", "Berlin", "Tokyo"]
                ),
                "headline": f"Experienced {random.choice(skills)} Developer",
                "work_experience": [
                    {
                        "position": f"{random.choice(['Senior', 'Mid-level', 'Junior'])} Developer",
                        "company": f"Tech Company {random.randint(1, 100)}",
                        "duration": f"{random.randint(1, 5)} years",
                    }
                ],
                "education": [
                    {
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "school": f"University {random.randint(1, 50)}",
                    }
                ],
            }

            response = self.client.put("/api/profile/", json=profile_data)
            if response.status_code == 200:
                self.profile_created = True

    @task(3)  # Higher weight - users swipe more than other actions
    def swipe_jobs(self):
        """Simulate job swiping - the core user action"""
        if not self.auth_token:
            return

        # Get personalized jobs
        response = self.client.get("/api/jobs/personalized", params={"limit": 10})

        if response.status_code == 200:
            jobs = response.json()
            if jobs:
                # Simulate swiping through jobs
                for job_data in jobs[: random.randint(1, 5)]:  # Swipe 1-5 jobs
                    job = job_data.get("job", {})
                    job_id = job.get("id")

                    if job_id:
                        # Random decision: like, dislike, or superlike
                        action = random.choice(["like", "dislike", "superlike"])

                        # Record interaction
                        interaction_data = {
                            "job_id": job_id,
                            "interaction_type": action,
                            "swipe_direction": "right" if action == "like" else "left",
                            "timestamp": "2026-01-27T12:00:00Z",
                        }

                        self.client.post("/api/jobs/interact", json=interaction_data)

    @task(1)
    def view_job_details(self):
        """View detailed job information"""
        if not self.auth_token:
            return

        # Get a random job to view details
        response = self.client.get("/api/jobs/", params={"limit": 50})
        if response.status_code == 200:
            jobs = response.json()
            if jobs:
                job = random.choice(jobs)
                job_id = job.get("id")
                if job_id:
                    self.client.get(f"/api/jobs/{job_id}")

    @task(1)
    def search_jobs(self):
        """Perform job searches"""
        if not self.auth_token:
            return

        search_terms = [
            "python developer",
            "frontend engineer",
            "data scientist",
            "devops engineer",
            "product manager",
            "ux designer",
        ]

        search_term = random.choice(search_terms)
        self.client.get("/api/jobs/search", params={"q": search_term, "limit": 20})

    @task(1)
    def apply_to_job(self):
        """Simulate job application (less frequent)"""
        if not self.auth_token:
            return

        # Get jobs and randomly apply to one
        response = self.client.get("/api/jobs/personalized", params={"limit": 5})
        if response.status_code == 200:
            jobs = response.json()
            if jobs and random.random() < 0.1:  # 10% chance to apply
                job_data = random.choice(jobs)
                job = job_data.get("job", {})
                job_id = job.get("id")

                if job_id:
                    application_data = {
                        "job_id": job_id,
                        "cover_letter": "I am very interested in this position and believe my skills would be a great fit.",
                        "customizations": {
                            "salary_expectation": random.choice(
                                [80000, 100000, 120000, 150000]
                            ),
                            "start_date": "Immediate",
                        },
                    }

                    self.client.post("/api/applications/submit", json=application_data)

    @task(1)
    def check_notifications(self):
        """Check for notifications"""
        if not self.auth_token:
            return

        self.client.get("/api/notifications/")

    @task(1)
    def update_profile(self):
        """Occasionally update profile"""
        if not self.auth_token or random.random() > 0.05:  # 5% chance
            return

        # Add a new skill
        new_skill = random.choice(
            [
                "Machine Learning",
                "Blockchain",
                "React Native",
                "GraphQL",
                "TypeScript",
                "Rust",
                "Go",
                "Scala",
            ]
        )

        current_profile_response = self.client.get("/api/profile/")
        if current_profile_response.status_code == 200:
            current_profile = current_profile_response.json()
            skills = current_profile.get("skills", [])
            if new_skill not in skills:
                skills.append(new_skill)

                update_data = {
                    "skills": skills,
                    "headline": f"Experienced developer skilled in {', '.join(skills[:3])}",
                }

                self.client.put("/api/profile/", json=update_data)

    @task(1)
    def view_analytics(self):
        """View user analytics/dashboard"""
        if not self.auth_token:
            return

        self.client.get("/api/analytics/dashboard")


class HighLoadUser(JobSwipeUser):
    """User type for high load testing - faster actions"""

    wait_time = constant(0.5)  # Much faster actions

    @task(5)
    def aggressive_swiping(self):
        """Aggressive job swiping for load testing"""
        self.swipe_jobs()


class MobileAppUser(HttpUser):
    """Simulates mobile app usage patterns"""

    wait_time = between(2, 5)  # Mobile users tend to take longer

    def on_start(self):
        """Mobile-specific setup"""
        self.user_id = str(uuid.uuid4())
        self.device_token = f"device_token_{self.user_id}"
        self.auth_token = None

        # Register device for push notifications
        self.client.post(
            "/api/notifications/register-device",
            json={
                "device_token": self.device_token,
                "platform": random.choice(["ios", "android"]),
            },
        )

        # Login
        self._register_or_login()

    def _register_or_login(self):
        """Mobile login flow"""
        # Similar to web user but with mobile-specific headers
        self.client.headers.update(
            {"User-Agent": "JobSwipe-Mobile/1.0.0", "X-Device-Type": "mobile"}
        )

        # Use mobile test users
        user = {
            "email": f"mobile_user_{random.randint(1, 50)}@example.com",
            "password": "mobilepass123",
        }

        login_response = self.client.post("/api/auth/login", json=user)
        if login_response.status_code == 200:
            self.auth_token = login_response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})

    @task(4)
    def mobile_job_browsing(self):
        """Mobile-optimized job browsing"""
        if not self.auth_token:
            return

        # Mobile users often browse with location context
        response = self.client.get(
            "/api/jobs/personalized",
            params={
                "limit": 5,  # Smaller batches on mobile
                "include_location": "true",
            },
        )

        if response.status_code == 200:
            jobs = response.json()
            for job_data in jobs:
                # Mobile users often view job details
                job = job_data.get("job", {})
                job_id = job.get("id")
                if job_id and random.random() < 0.3:  # 30% view details
                    self.client.get(f"/api/jobs/{job_id}")

    @task(2)
    def quick_swipes(self):
        """Quick swipe actions typical on mobile"""
        if not self.auth_token:
            return

        response = self.client.get("/api/jobs/personalized", params={"limit": 3})
        if response.status_code == 200:
            jobs = response.json()
            for job_data in jobs:
                job = job_data.get("job", {})
                job_id = job.get("id")
                if job_id:
                    # Quick decisions on mobile
                    action = random.choice(["like", "dislike"])
                    self.client.post(
                        "/api/jobs/interact",
                        json={
                            "job_id": job_id,
                            "interaction_type": action,
                            "swipe_direction": "right" if action == "like" else "left",
                        },
                    )


# Configuration for different load test scenarios
def setup_test_environment():
    """Setup environment variables for load testing"""
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://test:test@localhost:5432/jobswipe_test"
    )
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_load_testing")
    os.environ.setdefault("ENVIRONMENT", "load_test")


# Pre-test setup
setup_test_environment()
