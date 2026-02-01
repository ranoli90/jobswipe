"""
Spike Load Test - Jobswipe API
Tests system resilience under sudden traffic spikes
"""

from locust import HttpUser, task, between
import json
import random
import os

class SpikeUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Extreme user behavior for spikes

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

    @task(5)
    def search_jobs_spike(self):
        """Extremely high frequency job searches"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager", "frontend", "backend", "fullstack", "devops"]),
            "location": random.choice(["San Francisco", "New York", "Remote", "London", "Berlin", "Toronto", "Sydney"]),
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
    def get_job_details_spike(self):
        """Extremely high frequency job detail requests"""
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
    def submit_application_spike(self):
        """Extremely high frequency application submissions"""
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
