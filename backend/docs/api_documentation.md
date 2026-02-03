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

Successful responses for most endpoints return the data directly:

```json
[
  {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "snippet": "We are looking for a senior engineer...",
    "score": 0.85,
    "apply_url": "https://example.com/apply"
  }
]
```

Some endpoints may return structured responses:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "ref_tok_...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

Error responses follow this structure:

```json
{
  "detail": "Error message here",
  "request_id": "unique-request-id"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limits

| Endpoint Type | Requests per minute | Description |
|---------------|---------------------|-------------|
| Auth endpoints (/api/v1/auth/*) | 5 | Registration, login, password reset |
| General API | 60 | Standard API endpoints |
| Read-only (/api/v1/jobs/*) | 100 | Job browsing and matching |
| Admin operations | 30 | API key management, ingestion |
| WebSocket | 1000 connections | Real-time connections |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Health Check Endpoints

### Basic Health Check

```http
GET /health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**Rate Limit:** 100/minute (public)

### Readiness Check

```http
GET /ready
```

Checks database and Redis connectivity.

**Response (200 OK):**

```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (503 Service Unavailable):**

```json
{
  "status": "not_ready",
  "database": "disconnected",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Rate Limit:** 100/minute (public)

### RabbitMQ Health Check

```http
GET /health/rabbitmq
```

Checks RabbitMQ message broker health.

**Response (200 OK):**

```json
{
  "service": "rabbitmq",
  "status": "healthy",
  "latency_ms": 15.2,
  "message": "RabbitMQ is healthy",
  "details": {
    "status": "ok"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (503 Service Unavailable):**

```json
{
  "service": "rabbitmq",
  "status": "unhealthy",
  "latency_ms": 5000.0,
  "message": "RabbitMQ connection timed out",
  "error": "Timeout after 5s",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Rate Limit:** 60/minute (public)

### OpenSearch Health Check

```http
GET /health/opensearch
```

Checks OpenSearch cluster health.

**Response (200 OK):**

```json
{
  "service": "opensearch",
  "status": "healthy",
  "latency_ms": 25.5,
  "message": "OpenSearch cluster status: green",
  "details": {
    "cluster_name": "jobswipe-cluster",
    "status": "green",
    "number_of_nodes": 1,
    "active_shards": 5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Rate Limit:** 60/minute (public)

### Celery Worker Health Check

```http
GET /health/celery
```

Checks Celery worker availability.

**Response (200 OK):**

```json
{
  "service": "celery",
  "status": "healthy",
  "latency_ms": 45.0,
  "message": "2 Celery worker(s) active",
  "details": {
    "worker_count": 2,
    "workers": ["celery@worker1", "celery@worker2"],
    "worker_stats": {
      "celery@worker1": {
        "processed": 150,
        "prefetch_count": 4
      }
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Rate Limit:** 60/minute (public)

### Comprehensive Health Check

```http
GET /health/detailed
```

Performs health checks on all dependencies.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "total_latency_ms": 150.5,
  "services": {
    "database": {
      "service": "database",
      "status": "healthy",
      "latency_ms": 25.3,
      "message": "Database connection successful",
      "details": {},
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "redis": {
      "service": "redis",
      "status": "healthy",
      "latency_ms": 5.2,
      "message": "Redis connection successful",
      "details": {
        "version": "7.0.0",
        "used_memory_human": "1.5M",
        "connected_clients": 10
      },
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "rabbitmq": {
      "service": "rabbitmq",
      "status": "healthy",
      "latency_ms": 15.2,
      "message": "RabbitMQ is healthy",
      "details": {},
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "opensearch": {
      "service": "opensearch",
      "status": "healthy",
      "latency_ms": 25.5,
      "message": "OpenSearch cluster status: green",
      "details": {},
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "celery": {
      "service": "celery",
      "status": "healthy",
      "latency_ms": 45.0,
      "message": "2 Celery worker(s) active",
      "details": {},
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

**Response (503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "total_latency_ms": 5000.0,
  "services": {
    "database": {
      "service": "database",
      "status": "unhealthy",
      "latency_ms": 5000.0,
      "message": "Database connection timed out",
      "error": "Timeout after 5s",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

**Rate Limit:** 30/minute (public)

## Authentication Endpoints

### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "ref_tok_...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (400 Bad Request - Validation Error):**

```json
{
  "detail": "Email already registered"
}
```

**Response (400 Bad Request - Password Validation):**

```json
{
  "detail": "Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "ref_tok_...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Incorrect email or password"
}
```

**Response (429 Too Many Requests - Account Locked):**

```json
{
  "detail": "Account is temporarily locked due to too many failed attempts. Try again in 30 minutes."
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "ref_tok_..."
}
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "new_ref_tok_...",
  "token_type": "bearer"
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Invalid or expired refresh token"
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "message": "Successfully logged out"
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Could not validate credentials"
}
```

### OAuth2 Login

```http
GET /api/v1/auth/oauth2/{provider}
```

Supported providers: `google`, `linkedin`

**Response (200 OK):**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-string"
}
```

### OAuth2 Callback

```http
GET /api/v1/auth/oauth2/callback/{provider}?code=auth_code&state=state_value
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "ref_tok_...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## MFA Endpoints

### Setup MFA

```http
GET /api/v1/auth/mfa/setup
Authorization: Bearer <access_token>
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "backup_codes": ["12345678", "87654321", "..."]
}
```

### Enable MFA

```http
POST /api/v1/auth/mfa/enable
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "token": "123456"
}
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "message": "MFA enabled successfully"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid verification token"
}
```

### Verify MFA

```http
POST /api/v1/auth/mfa/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "token": "123456"
}
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "message": "MFA verification successful"
}
```

## Jobs Endpoints

### Get Job Feed

```http
GET /api/v1/feed?cursor=optional_cursor&page_size=20
Authorization: Bearer <access_token>
```

**Rate Limit:** 100/minute

**Query Parameters:**
- `cursor` (string, optional): Cursor for pagination
- `page_size` (integer, optional): Number of jobs per page (default: 20, max: 100)

**Response (200 OK):**

```json
[
  {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "snippet": "We are looking for a senior engineer...",
    "score": 0.85,
    "apply_url": "https://example.com/apply"
  }
]
```

### Get Job Matches

```http
GET /api/v1/matches?limit=20&offset=0&min_score=0.0
Authorization: Bearer <access_token>
```

**Rate Limit:** 100/minute

**Query Parameters:**
- `limit` (integer, optional): Number of matches to return (default: 20, min: 1, max: 100)
- `offset` (integer, optional): Offset for pagination (default: 0)
- `min_score` (float, optional): Minimum match score threshold (default: 0.0, range: 0.0-1.0)

**Response (200 OK):**

```json
[
  {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "snippet": "We are looking for a senior engineer...",
    "score": 0.92,
    "metadata": {
      "bm25_score": 0.85,
      "has_skill_match": true,
      "has_location_match": true
    },
    "apply_url": "https://example.com/apply"
  }
]
```

**Response (404 Not Found):**

```json
{
  "detail": "Candidate profile not found"
}
```

### Get Job Details

```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer <access_token>
```

**Rate Limit:** 100/minute

**Response (200 OK):**

```json
{
  "id": "job-uuid",
  "title": "Senior Software Engineer",
  "company": "Tech Corp",
  "location": "Remote",
  "snippet": "Full job description...",
  "score": 0.85,
  "apply_url": "https://example.com/apply"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid job ID format"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

### Swipe Job

```http
POST /api/v1/jobs/{job_id}/swipe
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "action": "right"
}
```

**Rate Limit:** 60/minute

**Request Body:**
- `action` (string, required): Either "right" (like/apply) or "left" (pass)

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully swiped right",
  "job_id": "job-uuid"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid swipe action. Must be 'right' or 'left'"
}
```

**Response (400 Bad Request - Duplicate):**

```json
{
  "detail": "You have already interacted with this job"
}
```

### Search Jobs

```http
GET /api/v1/jobs/search?query=software&location=remote&company=tech&job_type=full_time&limit=20&offset=0
Authorization: Bearer <access_token>
```

**Rate Limit:** 100/minute

**Query Parameters:**
- `query` (string, required): Search query string
- `location` (string, optional): Filter by location
- `company` (string, optional): Filter by company name
- `job_type` (string, optional): Filter by job type (full_time, part_time, contract)
- `limit` (integer, optional): Number of results to return (default: 20, max: 100)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Response (200 OK):**

```json
[
  {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "snippet": "We are looking for a senior engineer...",
    "score": 0.5,
    "apply_url": "https://example.com/apply"
  }
]
```

### Save Job

```http
POST /api/v1/jobs/{job_id}/save
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK) - Job Saved:**

```json
{
  "success": true,
  "message": "Job saved successfully",
  "job_id": "job-uuid",
  "saved": true
}
```

**Response (200 OK) - Job Unsaved (toggle behavior):**

```json
{
  "success": true,
  "message": "Job removed from saved list",
  "job_id": "job-uuid",
  "saved": false
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid job ID format"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

### Get Saved Jobs

```http
GET /api/v1/jobs/saved
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
[
  {
    "id": "job-uuid",
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "snippet": "We are looking for a senior engineer...",
    "score": 0.5,
    "apply_url": "https://example.com/apply"
  }
]
```

## Profile Endpoints

### Get Profile

```http
GET /api/v1/profile
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "id": "profile-uuid",
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
  "parsed_at": "2024-01-15T10:30:00Z",
  "preferences": {
    "job_types": ["full-time", "contract"],
    "remote_preference": "remote",
    "experience_level": "senior"
  }
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Profile not found. Please upload a resume first."
}
```

### Update Profile

```http
PUT /api/v1/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "headline": "Senior Software Engineer",
  "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
  "experience": [...],
  "education": [...],
  "preferences": {
    "job_types": ["full-time"],
    "remote_preference": "hybrid",
    "experience_level": "senior"
  }
}
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "id": "profile-uuid",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "headline": "Senior Software Engineer",
  "work_experience": [...],
  "education": [...],
  "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
  "resume_file_url": "https://storage.example.com/resumes/...",
  "parsed_at": "2024-01-15T10:30:00Z",
  "preferences": {...}
}
```

### Upload Resume

```http
POST /api/v1/profile/resume
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: (binary PDF or DOCX)
```

**Rate Limit:** 10/minute

**Supported Formats:** PDF, DOCX

**Max File Size:** 10MB

**Response (200 OK):**

```json
{
  "id": "profile-uuid",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "headline": "Senior Software Engineer",
  "work_experience": [...],
  "education": [...],
  "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
  "resume_file_url": "resumes/user-uuid/resume.pdf",
  "parsed_at": "2024-01-15T10:30:00Z"
}
```

**Response (400 Bad Request - Invalid File):**

```json
{
  "detail": "Invalid file type. Only PDF and DOCX files are allowed."
}
```

**Response (400 Bad Request - File Too Large):**

```json
{
  "detail": "File too large. Maximum size is 10MB."
}
```

## Applications Endpoints

### Create Application

```http
POST /api/v1/applications
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid"
}
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "id": "app-uuid",
  "job_id": "job-uuid",
  "status": "queued",
  "attempt_count": 0,
  "last_error": null,
  "assigned_worker": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### List Applications

```http
GET /api/v1/applications
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
[
  {
    "id": "app-uuid",
    "job_id": "job-uuid",
    "status": "completed",
    "attempt_count": 1,
    "last_error": null,
    "assigned_worker": "celery@worker1",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
]
```

### Get Application Status

```http
GET /api/v1/applications/{job_id}/status
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "id": "app-uuid",
  "job_id": "job-uuid",
  "status": "completed",
  "attempt_count": 1,
  "last_error": null,
  "assigned_worker": "celery@worker1",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Application not found"
}
```

### Get Application Audit Log

```http
GET /api/v1/applications/{job_id}/audit
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
[
  {
    "id": "audit-uuid",
    "step": "form_submission",
    "payload": {...},
    "artifacts": {...},
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

### Cancel Application

```http
POST /api/v1/applications/{job_id}/cancel
Authorization: Bearer <access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Application cancelled successfully"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Only pending or in-progress tasks can be cancelled"
}
```

### Update Application Status

```http
PUT /api/v1/applications/{job_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "cancelled"
}
```

**Rate Limit:** 30/minute

**Valid Statuses:** `queued`, `running`, `completed`, `failed`, `cancelled`

**Response (200 OK):**

```json
{
  "id": "app-uuid",
  "job_id": "job-uuid",
  "status": "cancelled",
  "attempt_count": 0,
  "last_error": null,
  "assigned_worker": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid status. Must be one of: queued, running, completed, failed, cancelled"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Application not found"
}
```

### Delete Application

```http
DELETE /api/v1/applications/{job_id}
Authorization: Bearer <access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Application deleted successfully"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Application not found"
}
```

## Analytics Endpoints

### Get Analytics Metrics

```http
GET /api/v1/analytics/metrics
Authorization: Bearer <analytics_api_key>
```

**Rate Limit:** 60/minute

**Authentication:** Requires Analytics API Key in Authorization header

**Response (200 OK):**

```json
{
  "total_users": 1250,
  "total_jobs": 5000,
  "total_interactions": 35000,
  "total_applications": 4200,
  "avg_match_score": 0.78,
  "success_rate": 0.65,
  "daily_growth": 0.08
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Invalid analytics API key"
}
```

### Generate Report

```http
POST /api/v1/analytics/generate-report
Authorization: Bearer <analytics_api_key>
Content-Type: application/json

{
  "report_type": "matching_accuracy",
  "time_range": 30,
  "format": "json"
}
```

**Rate Limit:** 10/minute

**Report Types:** `matching_accuracy`, `user_behavior`, `job_market`

**Formats:** `json`, `csv`, `html`

**Response (200 OK):**

```json
{
  "success": true,
  "report_type": "matching_accuracy",
  "time_range": 30,
  "format": "json",
  "file_path": "/tmp/report_123.json",
  "file_name": "report_123.json",
  "size": 1024,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid report type. Valid types: matching_accuracy, user_behavior, job_market"
}
```

### Get Dashboard Summary

```http
GET /api/v1/analytics/dashboard-summary
Authorization: Bearer <analytics_api_key>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "total_users": 1250,
  "active_users_today": 450,
  "total_jobs": 5000,
  "new_jobs_today": 150,
  "total_applications": 4200,
  "applications_today": 85,
  "success_rate": 0.65
}
```

## Notifications Endpoints

### Get Notifications

```http
GET /api/v1/notifications?limit=50
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Query Parameters:**
- `limit` (integer, optional): Maximum notifications to return (default: 50, max: 100)

**Response (200 OK):**

```json
{
  "notifications": [
    {
      "id": "notif-uuid",
      "type": "application_completed",
      "title": "Application Completed",
      "message": "Your application to Tech Corp has been submitted.",
      "read": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Unread Count

```http
GET /api/v1/notifications/unread-count
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "unread_count": 5
}
```

### Mark Notification as Read

```http
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "message": "Notification marked as read"
}
```

### Mark All Notifications as Read

```http
PUT /api/v1/notifications/mark-all-read
Authorization: Bearer <access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "message": "Marked 5 notifications as read"
}
```

### Get Notification Preferences

```http
GET /api/v1/notifications/preferences
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "preferences": {
    "push_enabled": true,
    "push_application_submitted": true,
    "push_application_completed": true,
    "push_application_failed": true,
    "push_captcha_detected": true,
    "push_job_match_found": true,
    "email_enabled": true,
    "email_application_submitted": false,
    "email_application_completed": true,
    "email_application_failed": true,
    "quiet_hours_enabled": false,
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

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "message": "Notification preferences updated successfully"
}
```

### Register Device Token

```http
POST /api/v1/notifications/device-token
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "device_id": "device-123",
  "platform": "ios",
  "token": "apns-device-token",
  "app_version": "1.0.0"
}
```

**Rate Limit:** 30/minute

**Platforms:** `ios`, `android`

**Response (200 OK):**

```json
{
  "message": "Device token registered successfully"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Platform must be 'ios' or 'android'"
}
```

### Unregister Device Token

```http
DELETE /api/v1/notifications/device-token/{device_id}
Authorization: Bearer <access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "message": "Device token unregistered successfully"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Device token not found"
}
```

### Get Notification Statistics (Admin)

```http
GET /api/v1/notifications/stats
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "stats": {
    "total_notifications": 1500,
    "delivered_push": 1200,
    "delivered_email": 850,
    "failed_push": 50,
    "failed_email": 20,
    "service_status": {
      "apns": "healthy",
      "fcm": "healthy",
      "email": "healthy"
    }
  }
}
```

## API Keys Management Endpoints

### Create API Key

```http
POST /api/v1/admin/api-keys
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "name": "Data Ingestion Service",
  "service_type": "ingestion",
  "description": "API key for job ingestion service",
  "permissions": ["ingest_jobs", "get_ingestion_status"],
  "rate_limit": 1000,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Rate Limit:** 10/minute

**Service Types:** `ingestion`, `automation`, `analytics`, `webhook`

**Response (201 Created):**

```json
{
  "id": "key-uuid",
  "key": "js_ingestion_abc123def456",
  "key_prefix": "js_ingestion",
  "name": "Data Ingestion Service",
  "service_type": "ingestion",
  "permissions": ["ingest_jobs", "get_ingestion_status"],
  "rate_limit": 1000,
  "expires_at": "2024-12-31T23:59:59Z",
  "is_active": true,
  "last_used_at": null,
  "usage_count": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid service_type. Must be one of: ['ingestion', 'automation', 'analytics', 'webhook']"
}
```

**Response (403 Forbidden):**

```json
{
  "detail": "Only admin users can create API keys"
}
```

### List API Keys

```http
GET /api/v1/admin/api-keys?service_type=ingestion&active_only=true
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 60/minute

**Query Parameters:**
- `service_type` (string, optional): Filter by service type
- `active_only` (boolean, optional): Only show active keys (default: true)

**Response (200 OK):**

```json
[
  {
    "id": "key-uuid",
    "key_prefix": "js_ingestion",
    "name": "Data Ingestion Service",
    "service_type": "ingestion",
    "permissions": ["ingest_jobs", "get_ingestion_status"],
    "rate_limit": 1000,
    "expires_at": "2024-12-31T23:59:59Z",
    "is_active": true,
    "last_used_at": "2024-01-15T10:45:00Z",
    "usage_count": 15,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get API Key Details

```http
GET /api/v1/admin/api-keys/{key_id}
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "id": "key-uuid",
  "key_prefix": "js_ingestion",
  "name": "Data Ingestion Service",
  "service_type": "ingestion",
  "permissions": ["ingest_jobs", "get_ingestion_status"],
  "rate_limit": 1000,
  "expires_at": "2024-12-31T23:59:59Z",
  "is_active": true,
  "last_used_at": "2024-01-15T10:45:00Z",
  "usage_count": 15,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Invalid key ID format"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "API key not found"
}
```

### Revoke API Key

```http
POST /api/v1/admin/api-keys/{key_id}/revoke
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 30/minute

**Response (204 No Content)**

**Response (404 Not Found):**

```json
{
  "detail": "API key not found"
}
```

### Rotate API Key

```http
POST /api/v1/admin/api-keys/{key_id}/rotate
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "id": "new-key-uuid",
  "key": "js_ingestion_new123key456",
  "key_prefix": "js_ingestion",
  "name": "Data Ingestion Service",
  "service_type": "ingestion",
  "permissions": ["ingest_jobs", "get_ingestion_status"],
  "rate_limit": 1000,
  "expires_at": "2024-12-31T23:59:59Z",
  "is_active": true,
  "last_used_at": null,
  "usage_count": 0,
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Get API Key Statistics

```http
GET /api/v1/admin/api-keys/{key_id}/stats?since=2024-01-01
Authorization: Bearer <admin_access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "key_id": "key-uuid",
  "key_name": "Data Ingestion Service",
  "service_type": "ingestion",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-15T11:00:00Z",
  "total_requests": 150,
  "success_requests": 145,
  "failed_requests": 5,
  "avg_response_time": 0.123,
  "rate_limit_hits": 0
}
```

## Job Deduplication Endpoints

### Find Duplicate Jobs

```http
GET /api/v1/deduplicate/find
Authorization: Bearer <deduplication_api_key>
```

**Rate Limit:** 30/minute

**Authentication:** Requires Deduplication API Key

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Found 3 duplicate groups",
  "duplicate_groups": [
    {
      "main_job": {
        "id": "job-uuid-1",
        "title": "Senior Software Engineer",
        "company": "Tech Corp",
        "source": "greenhouse",
        "similarity": 1.0
      },
      "duplicates": [
        {
          "id": "job-uuid-2",
          "title": "Senior Software Engineer",
          "company": "Tech Corp",
          "source": "lever",
          "similarity": 0.95
        }
      ]
    }
  ]
}
```

### Remove Duplicate Jobs

```http
POST /api/v1/deduplicate/remove
Authorization: Bearer <deduplication_api_key>
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Removed 2 duplicate jobs from 1 groups",
  "duplicate_groups_found": 1,
  "duplicates_removed": 2,
  "unique_jobs_count": 100
}
```

### Run Deduplication Process

```http
POST /api/v1/deduplicate/run
Authorization: Bearer <deduplication_api_key>
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Removed 5 duplicate jobs from 3 groups",
  "duplicate_groups_found": 3,
  "duplicates_removed": 5,
  "unique_jobs_count": 95
}
```

## Job Categorization Endpoints

### Categorize All Jobs

```http
POST /api/v1/categorize/all
Authorization: Bearer <categorization_api_key>
```

**Rate Limit:** 5/minute

**Authentication:** Requires Categorization API Key

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully categorized 1234 jobs",
  "jobs_categorized": 1234,
  "category_counts": {
    "Software Engineering": 856,
    "Product Management": 123,
    "Data Science": 98,
    "Design": 157
  }
}
```

### Get Category Distribution

```http
GET /api/v1/categorize/distribution
Authorization: Bearer <categorization_api_key>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Category distribution retrieved successfully",
  "distribution": {
    "Software Engineering": 856,
    "Product Management": 123,
    "Data Science": 98,
    "Design": 157
  }
}
```

### Run Categorization Process

```http
POST /api/v1/categorize/run
Authorization: Bearer <categorization_api_key>
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully categorized 1234 jobs",
  "jobs_categorized": 1234,
  "category_counts": {
    "Software Engineering": 856,
    "Product Management": 123,
    "Data Science": 98,
    "Design": 157
  }
}
```

## Job Ingestion Endpoints

### Sync Greenhouse Board

```http
POST /api/v1/ingestion/sources/greenhouse/sync?board_token=abc123&incremental=true
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 30/minute

**Authentication:** Requires Ingestion API Key

**Query Parameters:**
- `board_token` (string, required): Greenhouse board token
- `incremental` (boolean, optional): Use incremental sync (default: true)

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully synced 25 jobs from Greenhouse board abc123",
  "jobs_synced": 25
}
```

### Sync Lever Postings

```http
POST /api/v1/ingestion/sources/lever/sync?org_slug=tech-corp&incremental=true
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 30/minute

**Query Parameters:**
- `org_slug` (string, required): Lever organization slug
- `incremental` (boolean, optional): Use incremental sync (default: true)

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully synced 18 jobs from Lever organization tech-corp",
  "jobs_synced": 18
}
```

### Sync RSS Feed

```http
POST /api/v1/ingestion/sources/rss/sync?feed_url=https%3A%2F%2Fexample.com%2Fjobs.rss
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 30/minute

**Query Parameters:**
- `feed_url` (string, required): URL-encoded RSS feed URL

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully synced 12 jobs from RSS feed https://example.com/jobs.rss",
  "jobs_synced": 12
}
```

### Trigger Ingestion

```http
POST /api/v1/ingestion/ingest
Authorization: Bearer <ingestion_api_key>
Content-Type: application/json

{
  "sources": ["greenhouse", "lever"],
  "interval_seconds": 3600
}
```

**Rate Limit:** 10/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully ingested 43 jobs",
  "jobs_ingested": 43,
  "jobs_processed": 43,
  "failed": 0
}
```

### Get Ingestion Status

```http
GET /api/v1/ingestion/status
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "is_running": true,
  "last_run": "2024-01-15T10:30:00Z",
  "next_run": "2024-01-15T11:30:00Z",
  "total_jobs_ingested": 1234,
  "failed_jobs": 42
}
```

### Start Periodic Ingestion

```http
POST /api/v1/ingestion/start-periodic
Authorization: Bearer <ingestion_api_key>
Content-Type: application/json

{
  "sources": ["greenhouse", "lever"],
  "interval_seconds": 3600
}
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Periodic ingestion started with interval 3600 seconds"
}
```

### Stop Periodic Ingestion

```http
POST /api/v1/ingestion/stop-periodic
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Periodic ingestion stopped"
}
```

### Get Ingestion Sources

```http
GET /api/v1/ingestion/sources
Authorization: Bearer <ingestion_api_key>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "sources": [
    {
      "name": "Greenhouse",
      "type": "greenhouse",
      "url": "https://boards-api.greenhouse.io"
    },
    {
      "name": "Lever",
      "type": "lever",
      "url": "https://api.lever.co"
    }
  ]
}
```

## Application Automation Endpoints

### Auto Apply to Job

```http
POST /api/v1/application-automation/auto-apply
Authorization: Bearer <access_token>
Authorization: Bearer <automation_api_key>
Content-Type: application/json

{
  "task_id": "task-uuid",
  "headless": true
}
```

**Rate Limit:** 10/minute

**Authentication:** Requires both user JWT and Automation API Key

**Response (200 OK):**

```json
{
  "success": true,
  "task_id": "task-uuid",
  "status": "completed",
  "message": "Application submitted successfully",
  "submitted": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (403 Forbidden):**

```json
{
  "detail": "Not authorized to access this task"
}
```

### Auto Apply to All Jobs

```http
POST /api/v1/application-automation/auto-apply-all
Authorization: Bearer <access_token>
Authorization: Bearer <automation_api_key>
```

**Rate Limit:** 5/minute

**Response (200 OK):**

```json
{
  "success": true,
  "total": 5,
  "processed": 5,
  "results": [
    {
      "task_id": "task-uuid-1",
      "job_id": "job-uuid-1",
      "status": "completed",
      "submitted": true
    },
    {
      "task_id": "task-uuid-2",
      "job_id": "job-uuid-2",
      "status": "failed",
      "submitted": false,
      "error": "Invalid form data"
    }
  ]
}
```

### Get Pending Tasks

```http
GET /api/v1/application-automation/tasks/pending
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "success": true,
  "pending": 3,
  "tasks": [
    {
      "id": "task-uuid-1",
      "job_id": "job-uuid-1",
      "status": "queued",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Get Application History

```http
GET /api/v1/application-automation/tasks/history
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "success": true,
  "total": 10,
  "tasks": [
    {
      "id": "task-uuid-1",
      "job_id": "job-uuid-1",
      "status": "completed",
      "submitted": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:05:00Z",
      "last_error": null
    }
  ]
}
```

### Get Automation Statistics

```http
GET /api/v1/application-automation/stats
Authorization: Bearer <access_token>
```

**Rate Limit:** 60/minute

**Response (200 OK):**

```json
{
  "success": true,
  "stats": {
    "total": 10,
    "pending": 3,
    "in_progress": 1,
    "success": 5,
    "failed": 1,
    "cancelled": 0
  },
  "success_rate": 50.0
}
```

### Cancel Task

```http
POST /api/v1/application-automation/tasks/{task_id}/cancel
Authorization: Bearer <access_token>
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Task cancelled successfully"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Only pending or in-progress tasks can be cancelled"
}
```

### Generate Cover Letter

```http
POST /api/v1/application-automation/cover-letter/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid",
  "custom_instructions": "Focus on Python and FastAPI skills"
}
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "success": true,
  "cover_letter": "Dear Hiring Manager,\n\nI am writing to apply for the Senior Software Engineer position...",
  "word_count": 450,
  "error": "",
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "model": "gpt-4"
  }
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

**Response (404 Not Found - Profile):**

```json
{
  "detail": "Candidate profile not found"
}
```

### Regenerate Cover Letter

```http
POST /api/v1/application-automation/cover-letter/regenerate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid",
  "previous_letter": "Dear Hiring Manager...",
  "feedback": "Make it more concise",
  "custom_instructions": "Focus on Python and FastAPI skills"
}
```

**Rate Limit:** 30/minute

**Response (200 OK):**

```json
{
  "success": true,
  "cover_letter": "Dear Hiring Manager,\n\nI am applying for the Senior Software Engineer position...",
  "word_count": 300,
  "error": "",
  "metadata": {
    "generated_at": "2024-01-15T10:35:00Z",
    "model": "gpt-4"
  }
}
```

## WebSocket Endpoints

### Connect

```http
WS /api/v1/ws/connect?token=<jwt_token>&connection_types=notifications,job_updates
```

**Connection Types:**
- `notifications` - Real-time notifications
- `job_updates` - Job posting updates
- `application_status` - Application status changes
- `matches` - New job matches

**Connection Message:**

```json
{
  "type": "connected",
  "connection_id": "conn-uuid",
  "user_id": "user-uuid",
  "connection_types": ["notifications", "job_updates"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Ping/Pong

**Client sends:**

```json
{
  "type": "ping"
}
```

**Server responds:**

```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Subscribe to Topics

```json
{
  "type": "subscribe",
  "connection_types": ["matches"]
}
```

### Unsubscribe from Topics

```json
{
  "type": "unsubscribe",
  "connection_types": ["job_updates"]
}
```

### Job Preferences Update

```json
{
  "type": "job_preference",
  "preferences": {
    "remote_only": true,
    "min_salary": 100000
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

## SDK Examples

### Python

```python
import requests
from typing import Optional

class JobSwipeClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            self.headers["X-API-Key"] = api_key
    
    def get_jobs(self, page: int = 1, per_page: int = 20):
        """Get job listings"""
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/feed",
            headers=self.headers,
            params={"page_size": per_page}
        )
        response.raise_for_status()
        return response.json()
    
    def get_matches(self, limit: int = 20, min_score: float = 0.0):
        """Get personalized job matches"""
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/matches",
            headers=self.headers,
            params={"limit": limit, "min_score": min_score}
        )
        response.raise_for_status()
        return response.json()
    
    def swipe_job(self, job_id: str, action: str = "right"):
        """Swipe right (apply) or left (pass) on a job"""
        response = requests.post(
            f"{self.base_url}/api/v1/jobs/{job_id}/swipe",
            headers=self.headers,
            json={"action": action}
        )
        response.raise_for_status()
        return response.json()
    
    def submit_application(self, job_id: str):
        """Submit an application for a job"""
        response = requests.post(
            f"{self.base_url}/api/v1/applications",
            headers=self.headers,
            json={"job_id": job_id}
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = JobSwipeClient("https://api.jobswipe.app", token="your_jwt_token")
jobs = client.get_jobs(page=1)
matches = client.get_matches(limit=10, min_score=0.7)
```

### JavaScript/TypeScript

```typescript
class JobSwipeClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string, apiKey?: string, token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.headers = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      this.headers['Authorization'] = `Bearer ${token}`;
    } else if (apiKey) {
      this.headers['X-API-Key'] = apiKey;
    }
  }

  async getJobs(page = 1, perPage = 20): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/jobs/feed?page_size=${perPage}`,
      { headers: this.headers }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async getMatches(limit = 20, minScore = 0.0): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/jobs/matches?limit=${limit}&min_score=${minScore}`,
      { headers: this.headers }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async swipeJob(jobId: string, action: 'right' | 'left'): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/jobs/${jobId}/swipe`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ action })
      }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async submitApplication(jobId: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/applications`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ job_id: jobId })
      }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // WebSocket connection
  connectWebSocket(token: string, connectionTypes: string[] = ['notifications']): WebSocket {
    const ws = new WebSocket(
      `${this.baseUrl.replace('http', 'ws')}/api/v1/ws/connect?token=${token}&connection_types=${connectionTypes.join(',')}`
    );
    
    ws.onopen = () => console.log('WebSocket connected');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
    };
    ws.onerror = (error) => console.error('WebSocket error:', error);
    ws.onclose = () => console.log('WebSocket disconnected');
    
    return ws;
  }
}

// Usage example
const client = new JobSwipeClient('https://api.jobswipe.app', undefined, 'your_jwt_token');
const jobs = await client.getJobs(1);
const ws = client.connectWebSocket('your_jwt_token', ['notifications', 'job_updates']);
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Authentication with JWT and API keys
- Job matching and application automation
- Real-time notifications via WebSocket
- Health check endpoints for all services
