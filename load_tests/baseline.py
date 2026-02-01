"""
Baseline Load Test - Jobswipe API
Tests the system's performance under normal traffic conditions
"""

from locust import HttpUser, task, between
import json
import random
import os

class BaselineUser(HttpUser):
    wait_time = between(1, 3)  # Normal user think time

    def on_start(self):
        """Authenticate user before testing"""
        # Use environment variables for credentials
        email = os.environ.get("LOCUST_USER_EMAIL", "test@example.com")
        password = os.environ.get("LOCUST_USER_PASSWORD", "password123")
        
        try:
            auth_response = self.client.post("/api/auth/login", json={
                "email": email,
                "password": password
            })
            auth_response.raise_for_status()  # Raise an exception for non-2xx status codes
            token = auth_response.json().get("access_token")
            if token:
                self.client.headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            print(f"Authentication failed: {e}")

    @task(3)
    def search_jobs(self):
        """Search jobs - most frequent user action"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager"]),
            "location": random.choice(["San Francisco", "New York", "Remote"]),
            "page": random.randint(1, 5)
        }
        with self.client.get("/api/jobs/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, list):
                        response.failure("Response is not a list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code {response.status_code}")

    @task(2)
    def get_job_details(self):
        """Get job details"""
        # First, search for a job to get a valid job_id
        params = {
            "keywords": "software engineer",
            "location": "Remote",
            "page": 1
        }
        with self.client.get("/api/jobs/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    jobs = response.json()
                    if jobs:
                        job_id = jobs[0].get("id")
                        if job_id:
                            with self.client.get(f"/api/jobs/{job_id}", catch_response=True, name="/api/jobs/[job_id]") as job_response:
                                if job_response.status_code == 200:
                                    try:
                                        job_data = job_response.json()
                                        if not isinstance(job_data, dict) or "id" not in job_data:
                                            job_response.failure("Invalid job details response")
                                    except json.JSONDecodeError:
                                        job_response.failure("Invalid JSON response")
                                else:
                                    job_response.failure(f"Status code {job_response.status_code}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code {response.status_code}")

    @task(1)
    def view_profile(self):
        """View user profile"""
        with self.client.get("/api/profile", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, dict) or "id" not in data:
                        response.failure("Invalid profile response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code != 404: # It's ok if the profile is not found
                response.failure(f"Status code {response.status_code}")

    @task(1)
    def get_notifications(self):
        """Get user notifications"""
        with self.client.get("/api/notifications", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, dict) or "notifications" not in data:
                        response.failure("Invalid notifications response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code {response.status_code}")

    @task(1)
    def get_metrics(self):
        """Get application metrics"""
        self.client.get("/metrics")
