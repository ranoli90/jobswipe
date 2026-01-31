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
curl -H "Authorization: Bearer <your_jwt_token>" https://api.jobswipe.app/v1/jobs
```

### API Key

```bash
curl -H "X-API-Key: <your_api_key>" https://api.jobswipe.app/v1/jobs
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
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {}
  },
  "request_id": "unique-request-id"
}
```

## Authentication Endpoints

### Register User

```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
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

### Login

```http
POST /v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
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

### Refresh Token

```http
POST /v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "ref_tok_..."
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "new_ref_tok_...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /v1/auth/me
Authorization: Bearer <access_token>
```

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

## Jobs Endpoints

### Get Job Feed

```http
GET /v1/jobs/feed?cursor=optional_cursor&page_size=20
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `cursor` (string): Optional cursor for pagination
- `page_size` (int): Number of jobs to return per page (default: 20)

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
GET /v1/jobs/matches?limit=20&offset=0&min_score=0.0
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (int): Number of matches to return (1-100, default: 20)
- `offset` (int): Offset for pagination (default: 0)
- `min_score` (float): Minimum score threshold (0.0-1.0, default: 0.0)

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

### List Jobs

```http
GET /v1/jobs?page=1&per_page=20&location=Remote&type=full_time
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
GET /v1/jobs/{job_id}
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

### Swipe Job

```http
POST /v1/jobs/{job_id}/swipe
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "action": "right"  // or "left"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Successfully swiped right",
  "job_id": "job-uuid"
}
```

### Get Job Matches

```http
GET /v1/jobs/matches
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
GET /v1/profile
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
PUT /v1/profile
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
POST /v1/profile/resume
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
POST /v1/profile/work_experience
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
POST /v1/profile/education
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
PUT /v1/profile/skills
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
POST /v1/applications
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
GET /v1/applications?status=submitted&page=1
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
GET /v1/applications/{application_id}
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
GET /v1/analytics/user
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
GET /v1/analytics/platform
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
GET /v1/notifications?unread_only=true&page=1
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
PUT /v1/notifications/{notification_id}/read
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
PUT /v1/notifications/read_all
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
GET /v1/notifications/preferences
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
PUT /v1/notifications/preferences
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

### Get Notification Statistics (Admin Only)

```http
GET /v1/notifications/stats
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
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

**Response (403 Forbidden - Non-Admin):**

```json
{
  "success": false,
  "error": {
    "code": "AUTHORIZATION_ERROR",
    "message": "Only admin users can access this endpoint"
  }
}
```

## Job Deduplication Endpoints

### Find Duplicate Jobs

```http
GET /v1/deduplicate/find
Authorization: Bearer <admin_access_token>
```

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
POST /v1/deduplicate/remove
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Removed 2 duplicate jobs from 1 groups",
  "duplicate_groups_found": 1,
  "duplicates_removed": 2
}
```

### Run Deduplication Process

```http
POST /v1/deduplicate/run
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Removed 5 duplicate jobs from 3 groups",
  "duplicate_groups_found": 3,
  "duplicates_removed": 5
}
```

## Job Categorization Endpoints

### Categorize All Jobs

```http
POST /v1/categorize/all
Authorization: Bearer <admin_access_token>
```

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
GET /v1/categorize/distribution
Authorization: Bearer <admin_access_token>
```

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
POST /v1/categorize/run
Authorization: Bearer <admin_access_token>
```

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

## API Keys Management Endpoints

### Create API Key

```http
POST /v1/admin/api-keys
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

### List API Keys

```http
GET /v1/admin/api-keys?service_type=ingestion&active_only=true
Authorization: Bearer <admin_access_token>
```

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
GET /v1/admin/api-keys/{key_id}
Authorization: Bearer <admin_access_token>
```

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

### Revoke API Key

```http
POST /v1/admin/api-keys/{key_id}/revoke
Authorization: Bearer <admin_access_token>
```

**Response (204 No Content):**

### Rotate API Key

```http
POST /v1/admin/api-keys/{key_id}/rotate
Authorization: Bearer <admin_access_token>
```

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
GET /v1/admin/api-keys/{key_id}/stats?since=2024-01-01
Authorization: Bearer <admin_access_token>
```

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

## Job Ingestion Endpoints

### Sync Greenhouse Board

```http
POST /v1/ingestion/sources/greenhouse/sync?board_token=abc123&incremental=true
Authorization: Bearer <admin_access_token>
```

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
POST /v1/ingestion/sources/lever/sync?org_slug=tech-corp&incremental=true
Authorization: Bearer <admin_access_token>
```

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
POST /v1/ingestion/sources/rss/sync?feed_url=https%3A%2F%2Fexample.com%2Fjobs.rss
Authorization: Bearer <admin_access_token>
```

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
POST /v1/ingestion/ingest
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "sources": ["greenhouse", "lever"],
  "interval_seconds": 3600
}
```

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
GET /v1/ingestion/status
Authorization: Bearer <admin_access_token>
```

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
POST /v1/ingestion/start-periodic
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "sources": ["greenhouse", "lever"],
  "interval_seconds": 3600
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Periodic ingestion started with interval 3600 seconds"
}
```

### Stop Periodic Ingestion

```http
POST /v1/ingestion/stop-periodic
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Periodic ingestion stopped"
}
```

### Get Ingestion Sources

```http
GET /v1/ingestion/sources
Authorization: Bearer <admin_access_token>
```

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
POST /v1/application-automation/auto-apply
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "task_id": "task-uuid",
  "headless": true
}
```

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

### Auto Apply to All Jobs

```http
POST /v1/application-automation/auto-apply-all
Authorization: Bearer <access_token>
```

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
GET /v1/application-automation/tasks/pending
Authorization: Bearer <access_token>
```

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
GET /v1/application-automation/tasks/history
Authorization: Bearer <access_token>
```

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
GET /v1/application-automation/stats
Authorization: Bearer <access_token>
```

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
POST /v1/application-automation/tasks/{task_id}/cancel
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Task cancelled successfully"
}
```

### Generate Cover Letter

```http
POST /v1/application-automation/cover-letter/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid",
  "custom_instructions": "Focus on Python and FastAPI skills"
}
```

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

### Regenerate Cover Letter

```http
POST /v1/application-automation/cover-letter/regenerate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": "job-uuid",
  "previous_letter": "Dear Hiring Manager...",
  "feedback": "Make it more concise",
  "custom_instructions": "Focus on Python and FastAPI skills"
}
```

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
POST /v1/webhooks
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
            f"{self.base_url}/v1/jobs",
            headers=self.headers,
            params={"page": page, "per_page": per_page}
        )
        return response.json()
    
    def submit_application(self, job_id: str, resume_id: str):
        response = requests.post(
            f"{self.base_url}/v1/applications",
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
      `${this.baseUrl}/v1/jobs?page=${page}&per_page=${perPage}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async submitApplication(jobId, resumeId) {
    const response = await fetch(
      `${this.baseUrl}/v1/applications`,
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
