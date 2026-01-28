"""
Endurance Load Test - Jobswipe API
Tests system stability under sustained load for extended periods
"""

from locust import HttpUser, task, between
import json
import random

class EnduranceUser(HttpUser):
    wait_time = between(1.5, 4)  # Normal user think time for endurance
    
    @task(3)
    def search_jobs_endurance(self):
        """Sustained job searches"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager", "devops", "ux designer"]),
            "location": random.choice(["San Francisco", "New York", "Remote", "Austin", "Seattle"]),
            "page": random.randint(1, 8)
        }
        self.client.get("/api/jobs/search", params=params)
    
    @task(2)
    def get_job_details_endurance(self):
        """Sustained job detail requests"""
        job_id = random.randint(1, 1500)
        self.client.get(f"/api/jobs/{job_id}")
    
    @task(1)
    def view_profile_endurance(self):
        """Sustained profile views"""
        self.client.get("/api/profile")
    
    @task(1)
    def get_notifications_endurance(self):
        """Sustained notifications requests"""
        self.client.get("/api/notifications")
    
    @task(1)
    def get_metrics_endurance(self):
        """Sustained metrics collection"""
        self.client.get("/metrics")
    
    @task(1)
    def save_search(self):
        """Simulate saving searches"""
        self.client.post("/api/searches/save", json={
            "keywords": random.choice(["software engineer", "data analyst"]),
            "location": random.choice(["San Francisco", "Remote"])
        })
    
    def on_start(self):
        """Authenticate user before testing"""
        auth_response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            if token:
                self.client.headers["Authorization"] = f"Bearer {token}"
