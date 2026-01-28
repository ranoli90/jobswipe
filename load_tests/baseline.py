"""
Baseline Load Test - Jobswipe API
Tests the system's performance under normal traffic conditions
"""

from locust import HttpUser, task, between
import json
import random

class BaselineUser(HttpUser):
    wait_time = between(1, 3)  # Normal user think time
    
    @task(3)
    def search_jobs(self):
        """Search jobs - most frequent user action"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager"]),
            "location": random.choice(["San Francisco", "New York", "Remote"]),
            "page": random.randint(1, 5)
        }
        self.client.get("/api/jobs/search", params=params)
    
    @task(2)
    def get_job_details(self):
        """Get job details"""
        job_id = random.randint(1, 1000)  # Assuming we have at least 1000 jobs
        self.client.get(f"/api/jobs/{job_id}")
    
    @task(1)
    def view_profile(self):
        """View user profile"""
        self.client.get("/api/profile")
    
    @task(1)
    def get_notifications(self):
        """Get user notifications"""
        self.client.get("/api/notifications")
    
    @task(1)
    def get_metrics(self):
        """Get application metrics"""
        self.client.get("/metrics")
    
    def on_start(self):
        """Authenticate user before testing"""
        # Simulate authenticated user
        auth_response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            if token:
                self.client.headers["Authorization"] = f"Bearer {token}"
