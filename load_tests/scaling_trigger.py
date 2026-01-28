"""
Scaling Trigger Load Test - Jobswipe API
Tests the system's auto-scaling behavior under increasing load
"""

from locust import HttpUser, task, between
import json
import random

class ScalingTriggerUser(HttpUser):
    wait_time = between(0.5, 1.5)  # Aggressive user behavior
    
    @task(4)
    def search_jobs_high_load(self):
        """High frequency job searches to trigger scaling"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager", "frontend developer", "backend developer"]),
            "location": random.choice(["San Francisco", "New York", "Remote", "London", "Berlin"]),
            "page": random.randint(1, 10)
        }
        self.client.get("/api/jobs/search", params=params)
    
    @task(3)
    def get_job_details_high_load(self):
        """High frequency job detail requests"""
        job_id = random.randint(1, 2000)
        self.client.get(f"/api/jobs/{job_id}")
    
    @task(2)
    def submit_application(self):
        """Simulate job applications"""
        self.client.post("/api/applications", json={
            "job_id": random.randint(1, 1000),
            "resume": "base64encodedresume",
            "cover_letter": "This is a cover letter"
        })
    
    @task(2)
    def get_recommendations(self):
        """Get job recommendations"""
        self.client.get("/api/recommendations")
    
    @task(1)
    def analyze_profile(self):
        """Profile analysis - CPU intensive task"""
        self.client.post("/api/profile/analyze", json={
            "resume": "base64encodedresume",
            "experience": random.randint(1, 10)
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
