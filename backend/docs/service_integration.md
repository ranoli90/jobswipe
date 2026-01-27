# Service Integration Documentation

This document describes how to integrate with JobSwipe's internal services.

## Overview

JobSwipe is composed of several microservices that can be integrated with:

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Main REST API |
| Celery Workers | - | Background job processing |
| Metrics | 9090 | Prometheus metrics endpoint |
| Health | /health | Health check endpoint |

## Authentication Integration

### Using API Keys

For service-to-service authentication, use API keys:

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://api.jobswipe.app"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.get(
    f"{BASE_URL}/api/v1/jobs",
    headers=headers
)
```

### Using JWT Tokens

For user-context operations, use JWT tokens:

```python
import requests

ACCESS_TOKEN = "user_access_token"
BASE_URL = "https://api.jobswipe.app"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
```

## Job Ingestion Service

### Submitting Jobs for Ingestion

Jobs can be submitted via the ingestion API:

```http
POST /api/v1/ingestion/jobs
Content-Type: application/json
X-API-Key: <service_api_key>

{
  "source": "custom",
  "jobs": [
    {
      "external_id": "custom-123",
      "title": "Software Engineer",
      "company": "Example Corp",
      "location": "Remote",
      "description": "Job description...",
      "apply_url": "https://example.com/apply",
      "salary_range": "$100k - $150k",
      "type": "full_time"
    }
  ]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "ingestion_id": "ing-uuid",
    "jobs_received": 1,
    "jobs_queued": 1,
    "status": "processing"
  }
}
}

## Application Automation Service

### Triggering Application Submission

```http
POST /api/v1/automation/applications
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "job_id": "job-uuid",
  "resume_id": "resume-uuid",
  "cover_letter_template_id": "template-uuid",
  "answers": [
    {
      "question": "Years of experience?",
      "answer": "5"
    }
  ]
}
```

### Checking Application Status

```http
GET /api/v1/automation/applications/{task_id}
Authorization: Bearer <user_token>
```

## Matching Service

### Getting Job Matches

```http
POST /api/v1/matching/jobs
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "job_ids": ["job-uuid-1", "job-uuid-2", "job-uuid-3"]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "job_id": "job-uuid-1",
        "score": 0.92,
        "reason": "Skills match: Python, FastAPI",
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": ["AWS"]
      }
    ]
  }
}
```

### Updating Profile for Better Matching

```http
PUT /api/v1/matching/profile
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "skills": ["Python", "PostgreSQL", "AWS"],
  "experience_years": 5,
  "preferred_locations": ["Remote", "San Francisco"],
  "job_types": ["full_time", "contract"]
}
```

## Notification Service

### Sending Custom Notifications

```http
POST /api/v1/notifications/send
Content-Type: application/json
X-API-Key: <service_api_key>

{
  "user_id": "user-uuid",
  "type": "custom",
  "title": "New Job Match",
  "message": "We found a new job that matches your profile!",
  "channels": ["push", "email"],
  "metadata": {
    "job_id": "job-uuid",
    "match_score": 0.85
  }
}
```

### Notification Types

| Type | Description |
|------|-------------|
| `application_submitted` | Application was submitted |
| `application_completed` | Application process completed |
| `application_failed` | Application submission failed |
| `job_match_found` | New job match found |
| `captcha_detected` | CAPTCHA challenge encountered |
| `system` | System notification |

## Analytics Service

### Tracking Custom Events

```http
POST /api/v1/analytics/events
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "event_type": "custom_action",
  "properties": {
    "action": "button_click",
    "location": "job_list"
  }
}
```

### Querying Analytics

```http
POST /api/v1/analytics/query
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "metrics": ["jobs_viewed", "jobs_applied"],
  "dimensions": ["date", "source"],
  "filters": {
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "granularity": "day"
}
```

## Storage Service

### Generating Presigned URLs

```http
POST /api/v1/storage/presigned-url
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "filename": "resume.pdf",
  "content_type": "application/pdf",
  "operation": "upload"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "upload_url": "https://storage.example.com/presigned-url...",
    "file_url": "https://storage.example.com/files/resume.pdf",
    "expires_at": "2024-01-20T11:00:00Z"
  }
}
```

## Resume Parser Service

### Parsing Resume

```http
POST /api/v1/resume/parse
Content-Type: application/json
X-API-Key: <service_api_key>

{
  "resume_url": "https://storage.example.com/resume.pdf"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "parsed": true,
    "extracted_data": {
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "location": "San Francisco, CA",
      "work_experience": [...],
      "education": [...],
      "skills": ["Python", "SQL", "AWS"],
      "summary": "Experienced software engineer..."
    },
    "parsing_confidence": 0.95,
    "parsed_at": "2024-01-20T10:30:00Z"
  }
}
```

## Rate Limiting

All service integrations are subject to rate limiting:

| Plan | Requests/minute |
|------|-----------------|
| Free | 60 |
| Pro | 300 |
| Enterprise | 1000 |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705747200
```

## Error Handling

All services return errors in a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please retry after 60 seconds.",
    "retry_after": 60
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Invalid or missing API key |
| `INVALID_TOKEN` | 401 | Invalid or expired JWT |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Webhooks

### Setting Up Webhooks

```http
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "url": "https://your-server.com/webhook",
  "events": [
    "application.submitted",
    "application.completed",
    "application.failed"
  ],
  "secret": "webhook_secret_key"
}
```

### Webhook Signature Verification

Webhooks are signed using HMAC-SHA256. Verify the signature:

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## SDK Libraries

### Python SDK

```python
from jobswipe import JobSwipeClient

client = JobSwipeClient(
    api_key="your_api_key",
    base_url="https://api.jobswipe.app"
)

# List jobs
jobs = client.jobs.list(page=1, per_page=20)

# Submit application
result = client.applications.submit(
    job_id="job-uuid",
    resume_id="resume-uuid"
)

# Get matches
matches = client.matching.get_matches()
```

### JavaScript SDK

```javascript
import { JobSwipeClient } from '@jobswipe/sdk';

const client = new JobSwipeClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.jobswipe.app'
});

// List jobs
const jobs = await client.jobs.list({ page: 1, perPage: 20 });

// Submit application
const result = await client.applications.submit({
  jobId: 'job-uuid',
  resumeId: 'resume-uuid'
});
```

## Support

For integration support:
- Email: api-support@jobswipe.app
- Documentation: https://docs.jobswipe.app
- Status Page: https://status.jobswipe.app
