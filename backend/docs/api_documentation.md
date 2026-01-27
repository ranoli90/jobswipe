# API Documentation

This document provides comprehensive API documentation with examples for the JobSwipe platform.

## Base URL

```
Production: https://api.jobswipe.app
Staging: https://api.staging.jobswipe.app
Development: http://localhost:8000
```

## Authentication

All API endpoints require authentication via Bearer token (JWT) or API key.

### Bearer Token (JWT)

```bash
curl -H "Authorization: Bearer <your_jwt_token>" https://api.jobswipe.app/api/v1/jobs
```

### API Key

```bash
curl -H "X-API-Key: <your_api_key>" https://api.jobswipe.app/api/v1/jobs
```

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [...]
  }
}
```

## Authentication Endpoints

### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123",
  "confirm_password": "secure_password123"
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "message": "Registration successful. Please verify your email."
  }
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "ref_tok_..."
  }
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "status": "active",
    "mfa_enabled": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Jobs Endpoints

### List Jobs

```http
GET /api/v1/jobs?page=1&per_page=20&location=Remote&type=full_time
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `location` (string): Filter by location
- `type` (string): Job type filter
- `search` (string): Search query

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "job-uuid",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "type": "full_time",
      "salary_range": "$150k - $200k",
      "description": "We are looking for a senior engineer...",
      "apply_url": "https://example.com/apply",
      "created_at": "2024-01-20T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

### Get Job Details

```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "type": "full_time",
    "salary_range": "$150k - $200k",
    "description": "Full job description...",
    "raw_json": {...},
    "apply_url": "https://example.com/apply",
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T10:00:00Z"
  }
}
```

### Swipe Right (Save Job)

```http
POST /api/v1/jobs/{job_id}/like
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Job saved to your list",
    "match_score": 0.85
  }
}
```

### Swipe Left (Skip Job)

```http
POST /api/v1/jobs/{job_id}/skip
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Job skipped"
  }
}
```

### Get Job Matches

```http
GET /api/v1/jobs/matches
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "job": {...},
      "match_score": 0.92,
      "match_reasons": ["Skills match", "Location match"]
    }
  ],
  "meta": {
    "total_matches": 5,
    "average_score": 0.78
  }
}
```

## Profile Endpoints

### Get Profile

```http
GET /api/v1/profile
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "profile-uuid",
    "user_id": "user-uuid",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "location": "San Francisco, CA",
    "headline": "Senior Software Engineer",
    "work_experience": [
      {
        "company": "Tech Corp",
        "title": "Senior Engineer",
        "start_date": "2020-01",
        "end_date": null,
        "current": true,
        "description": "Led team of 5 engineers..."
      }
    ],
    "education": [
      {
        "institution": "Stanford University",
        "degree": "M.S. Computer Science",
        "graduation_year": 2019
      }
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
    "resume_file_url": "https://storage.example.com/resumes/...",
    "parsed_at": "2024-01-15T10:30:00Z"
  }
}
```

### Update Profile

```http
PUT /api/v1/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "John Doe",
  "location": "San Francisco, CA",
  "headline": "Senior Software Engineer"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Profile updated successfully"
  }
}
```

### Upload Resume

```http
POST /api/v1/profile/resume
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: (binary PDF)
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "resume_url": "https://storage.example.com/resumes/...",
    "parsed": true,
    "parsing_summary": {
      "skills_extracted": 15,
      "experience_years": 5,
      "education_entries": 2
    }
  }
}
```

### Add Work Experience

```http
POST /api/v1/profile/work_experience
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "company": "New Company",
  "title": "Staff Engineer",
  "start_date": "2023-06",
  "current": true,
  "description": "Leading infrastructure initiatives..."
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "exp-uuid",
    "message": "Work experience added successfully"
  }
}
```

### Add Education

```http
POST /api/v1/profile/education
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "institution": "MIT",
  "degree": "Ph.D. Computer Science",
  "field_of_study": "Artificial Intelligence",
  "graduation_year": 2025
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "edu-uuid",
    "message": "Education added successfully"
  }
}
```

### Update Skills

```http
PUT /api/v1/profile/skills
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"]
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Skills updated successfully"
  }
}
```

## Applications Endpoints

### Submit Application

```http
POST /api/v1/applications
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid",
  "resume_id": "resume-uuid",
  "cover_letter": "optional cover letter text",
  "answers": [
    {
      "question": "Years of experience?",
      "answer": "5"
    }
  ]
}
```

**Response (202 Accepted):**

```json
{
  "success": true,
  "data": {
    "application_id": "app-uuid",
    "task_id": "task-uuid",
    "status": "queued",
    "message": "Application submitted successfully"
  }
}
```

### List Applications

```http
GET /api/v1/applications?status=submitted&page=1
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "app-uuid",
      "job_id": "job-uuid",
      "job_title": "Senior Software Engineer",
      "company": "Tech Corp",
      "status": "completed",
      "submitted_at": "2024-01-20T10:00:00Z",
      "completed_at": "2024-01-20T10:05:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 5
  }
}
```

### Get Application Status

```http
GET /api/v1/applications/{application_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "app-uuid",
    "job_id": "job-uuid",
    "status": "completed",
    "steps": [
      {
        "step": "form_submission",
        "status": "completed",
        "completed_at": "2024-01-20T10:01:00Z"
      },
      {
        "step": "resume_upload",
        "status": "completed",
        "completed_at": "2024-01-20T10:02:00Z"
      },
      {
        "step": "assessment",
        "status": "completed",
        "completed_at": "2024-01-20T10:05:00Z"
      }
    ],
    "artifacts": {
      "submitted_application_id": "GH-12345"
    }
  }
}
```

## Analytics Endpoints

### Get User Analytics

```http
GET /api/v1/analytics/user
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "period": "30d",
    "summary": {
      "jobs_viewed": 150,
      "jobs_saved": 45,
      "jobs_applied": 12,
      "interviews_scheduled": 3
    },
    "trends": [
      {
        "date": "2024-01-20",
        "jobs_viewed": 10,
        "jobs_applied": 2
      }
    ],
    "top_companies": [
      {
        "name": "Tech Corp",
        "applications": 3,
        "interviews": 1
      }
    ]
  }
}
```

### Get Platform Analytics (Admin)

```http
GET /api/v1/analytics/platform
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "period": "30d",
    "metrics": {
      "total_users": 10000,
      "active_users": 5000,
      "total_jobs": 50000,
      "total_applications": 25000,
      "success_rate": 0.45
    },
    "growth": {
      "users": {"current": 10000, "previous": 8500},
      "applications": {"current": 25000, "previous": 20000}
    }
  }
}
```

## Notifications Endpoints

### Get Notifications

```http
GET /api/v1/notifications?unread_only=true&page=1
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "notif-uuid",
      "type": "application_completed",
      "title": "Application Completed",
      "message": "Your application to Tech Corp has been submitted.",
      "read": false,
      "created_at": "2024-01-20T10:05:00Z"
    }
  ],
  "meta": {
    "unread_count": 5,
    "total": 50
  }
}
```

### Mark as Read

```http
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Notification marked as read"
  }
}
```

### Mark All as Read

```http
PUT /api/v1/notifications/read_all
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "All notifications marked as read"
  }
}
```

### Get Notification Preferences

```http
GET /api/v1/notifications/preferences
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "push_enabled": true,
    "push_application_submitted": true,
    "push_application_completed": true,
    "push_application_failed": false,
    "email_enabled": true,
    "email_application_completed": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
  }
}
```

### Update Notification Preferences

```http
PUT /api/v1/notifications/preferences
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "push_enabled": true,
  "email_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "message": "Preferences updated successfully"
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request parameters |
| AUTHENTICATION_ERROR | 401 | Invalid or missing credentials |
| AUTHORIZATION_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## Rate Limits

| Endpoint Type | Requests per minute |
|---------------|---------------------|
| Auth endpoints | 10 |
| General API | 60 |
| Read-only | 120 |
| Webhooks | 30 |

## Webhooks

### Configure Webhook

```http
POST /api/v1/webhooks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["application.submitted", "application.completed"],
  "secret": "webhook_secret_key"
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "webhook_id": "wh-uuid",
    "url": "https://your-server.com/webhook",
    "events": ["application.submitted", "application.completed"],
    "status": "active"
  }
}
```

### Webhook Payload Example

```json
{
  "event": "application.completed",
  "timestamp": "2024-01-20T10:05:00Z",
  "data": {
    "application_id": "app-uuid",
    "job_id": "job-uuid",
    "job_title": "Senior Software Engineer",
    "company": "Tech Corp",
    "status": "completed",
    "artifacts": {
      "submitted_application_id": "GH-12345"
    }
  },
  "signature": "sha256=..."
}
```

## SDK Examples

### Python

```python
import requests

class JobSwipeClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_jobs(self, page: int = 1, per_page: int = 20):
        response = requests.get(
            f"{self.base_url}/api/v1/jobs",
            headers=self.headers,
            params={"page": page, "per_page": per_page}
        )
        return response.json()
    
    def submit_application(self, job_id: str, resume_id: str):
        response = requests.post(
            f"{self.base_url}/api/v1/applications",
            headers=self.headers,
            json={"job_id": job_id, "resume_id": resume_id}
        )
        return response.json()

# Usage
client = JobSwipeClient("https://api.jobswipe.app", "your_api_key")
jobs = client.get_jobs(page=1)
```

### JavaScript

```javascript
class JobSwipeClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  async getJobs(page = 1, perPage = 20) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/jobs?page=${page}&per_page=${perPage}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async submitApplication(jobId, resumeId) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/applications`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ job_id: jobId, resume_id: resumeId })
      }
    );
    return response.json();
  }
}

// Usage
const client = new JobSwipeClient('https://api.jobswipe.app', 'your_api_key');
const jobs = await client.getJobs();
```
