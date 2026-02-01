"""
Scaling Trigger Load Test - Jobswipe API
Tests the system's auto-scaling behavior under increasing load
"""

from locust import HttpUser, task, between
import json
import random
import os

class ScalingTriggerUser(HttpUser):
    wait_time = between(0.5, 1.5)  # Aggressive user behavior

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

    @task(4)
    def search_jobs_high_load(self):
        """High frequency job searches to trigger scaling"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager", "frontend developer", "backend developer"]),
            "location": random.choice(["San Francisco", "New York", "Remote", "London", "Berlin"]),
            "page": random.randint(1, 10)
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

    @task(3)
    def get_job_details_high_load(self):
        """High frequency job detail requests"""
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

    @task(2)
    def submit_application(self):
        """Simulate job applications"""
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
                            with self.client.post("/api/applications", json={"job_id": job_id}, catch_response=True, name="/api/applications") as post_response:
                                if post_response.status_code == 200:
                                    try:
                                        data = post_response.json()
                                        if "task_id" not in data:
                                            post_response.failure("Invalid application response")
                                    except json.JSONDecodeError:
                                        post_response.failure("Invalid JSON response")
                                else:
                                    post_response.failure(f"Status code {post_response.status_code}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code {response.status_code}")
