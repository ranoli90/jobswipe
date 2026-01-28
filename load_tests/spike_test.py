"""
Spike Load Test - Jobswipe API
Tests system resilience under sudden traffic spikes
"""

from locust import HttpUser, task, between
import json
import random

class SpikeUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Extreme user behavior for spikes
    
    @task(5)
    def search_jobs_spike(self):
        """Extremely high frequency job searches"""
        params = {
            "keywords": random.choice(["software engineer", "data analyst", "product manager", "frontend", "backend", "fullstack", "devops"]),
            "location": random.choice(["San Francisco", "New York", "Remote", "London", "Berlin", "Toronto", "Sydney"]),
            "page": random.randint(1, 10)
        }
        self.client.get("/api/jobs/search", params=params)
    
    @task(3)
    def get_job_details_spike(self):
        """Extremely high frequency job detail requests"""
        job_id = random.randint(1, 2500)
        self.client.get(f"/api/jobs/{job_id}")
    
    @task(2)
    def submit_application_spike(self):
        """Extremely high frequency application submissions"""
        self.client.post("/api/applications", json={
            "job_id": random.randint(1, 1000),
            "resume": "base64encodedresume",
            "cover_letter": "This is a cover letter"
        })
    
    @task(2)
    def get_recommendations_spike(self):
        """Extremely high frequency recommendations"""
        self.client.get("/api/recommendations")
    
    @task(1)
    def analyze_profile_spike(self):
        """Extremely high frequency profile analysis"""
        self.client.post("/api/profile/analyze", json={
            "resume": "base64encodedresume",
            "experience": random.randint(1, 10)
        })
    
    @task(1)
    def bulk_process_jobs(self):
        """Bulk job processing - high load operation"""
        self.client.post("/api/jobs/bulk_process", json={
            "job_ids": [random.randint(1, 100) for _ in range(20)]
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
