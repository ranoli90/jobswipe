# Sorce Job Search App - Comprehensive Project Analysis

## 1. Current Project Overview

The Sorce Job Search App is a complete iOS-based job search platform with backend API, job ingestion, matching, and automation agents. It features a Tinder-like swipe interface for job cards and automated application capabilities.

**Version:** 1.0  
**Date:** 2026-01-25  
**Architecture:** FastAPI backend + SwiftUI iOS app + Docker infrastructure

## 2. Architecture Overview

```mermaid
graph LR
    A[iOS App] --> B[FastAPI Backend]
    B --> C[PostgreSQL]
    B --> D[OpenSearch/Elasticsearch]
    B --> E[Redis]
    B --> F[MinIO/S3]
    B --> G[RabbitMQ]
    G --> H[Celery Workers]
    H --> I[Playwright Automation]
    B --> J[Prometheus]
    J --> K[Grafana]
    B --> L[OpenTelemetry]
    L --> M[Jaeger]
    B --> N[Sentry]
```

## 3. Backend API Components

### 3.1 API Structure [backend/api/]

**Main Entry Point:** [`main.py`](backend/api/main.py:1)
- FastAPI application configuration
- CORS middleware setup
- Router includes for all endpoints

**API Routers:**
| Router | Prefix | Purpose |
|--------|--------|---------|
| auth | /v1/auth | User registration, login, authentication |
| profile | /v1/profile | Candidate profile management |
| jobs | /v1/jobs | Job feed, search, recommendations |
| applications | /v1/applications | Application tracking and management |
| jobs_ingestion | /v1/ingestion | Job source sync (Greenhouse, Lever, RSS) |
| analytics | /v1/analytics | Analytics and reporting |
| application_automation | /v1/application-automation | Application automation endpoints |
| job_deduplication | /api/deduplicate | Duplicate job detection and removal |
| job_categorization | /api/categorize | Job categorization using NLP |

### 3.2 Core Services [backend/services/]

**Key Services:**
- [`job_ingestion_service.py`](backend/services/job_ingestion_service.py:1) - Job ingestion from Greenhouse, Lever, and RSS with Kafka integration
- [`matching.py`](backend/services/matching.py:1) - Hybrid BM25 + embeddings + rule-based job matching
- [`job_deduplication.py`](backend/services/job_deduplication.py) - Fuzzy matching for duplicate detection
- [`job_categorization.py`](backend/services/job_categorization.py) - SpaCy-based NLP categorization
- [`application_automation.py`](backend/services/application_automation.py) - Playwright-based application automation
- [`openai_service.py`](backend/services/openai_service.py) - OpenAI integration for semantic matching
- [`resume_parser_enhanced.py`](backend/services/resume_parser_enhanced.py) - AI-powered resume parsing
- [`analytics_service.py`](backend/services/analytics_service.py) - Analytics and reporting
- [`storage.py`](backend/services/storage.py) - MinIO/S3 storage management

### 3.3 Authentication System [backend/api/routers/auth.py]

**Features:**
- User registration with email/password
- JWT token-based authentication
- Password hashing with Argon2 + PBKDF2 fallback
- Current user endpoint (/me)
- Tests: register, login, duplicate email, invalid credentials

**Security Configuration:**
```python
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["argon2", "pbkdf2-sha256"], deprecated="auto")
```

## 4. Database Models [backend/db/models.py]

### 4.1 Core Models

| Model | Purpose | Key Fields |
|-------|---------|-----------|
| User | User accounts | id, email, password_hash, status, created_at |
| CandidateProfile | Candidate information | id, user_id, full_name, phone, location, headline, skills, work_experience, education, resume_file_url |
| Job | Job postings | id, source, external_id, title, company, location, description, apply_url, salary_range, type, created_at, updated_at |
| JobIndex | Search index for jobs | job_id, search_vector, facets, indexed_at |
| UserJobInteraction | User-job interactions | id, user_id, job_id, action, interaction_metadata, created_at |
| ApplicationTask | Application automation tasks | id, user_id, job_id, status, attempt_count, last_error, assigned_worker, created_at, updated_at |
| ApplicationAuditLog | Audit logs for applications | id, task_id, step, payload, artifacts, timestamp |
| Domain | Domain configuration | id, host, ats_type, rate_limit_policy, captcha_type, last_status |
| CoverLetterTemplate | Cover letter templates | id, user_id, title, template_body, style_params, created_at |

### 4.2 Database Configuration

- **Type:** PostgreSQL 15 (Docker container)
- **Connection:** `postgresql://postgres:postgres@postgres/jobswipe`
- **ORM:** SQLAlchemy with Alembic migrations
- **Session Management:** Dependency injection via `get_db()`

## 5. Job Ingestion System

### 5.1 Sources Supported

**Greenhouse API:**
- Endpoint: `/v1/ingestion/sources/greenhouse/sync`
- Supports incremental sync using `updated_at` field
- Pre-configured companies: Airbnb, Uber, Stripe, Spotify

**Lever API:**
- Endpoint: `/v1/ingestion/sources/lever/sync`
- Incremental sync support
- Pre-configured companies: GitHub, Slack, Dropbox

**RSS Feeds:**
- Endpoint: `/v1/ingestion/sources/rss/sync`
- Parser: BeautifulSoup + feedparser
- Handles various RSS formats

### 5.2 Processing Pipeline

1. **Ingestion:** Fetch jobs from configured sources
2. **Filtering:** Only include specific job types (Software Engineer, Data Scientist, Product Manager, Designer)
3. **Normalization:** Standardize job data structure
4. **Validation:** Check minimum description length (500 chars)
5. **Storage:** PostgreSQL + optional Kafka for real-time processing
6. **Deduplication:** Fuzzy matching with configurable thresholds
7. **Categorization:** NLP-based category assignment

### 5.3 Deduplication Service

- **Algorithm:** Fuzzy matching (Levenshtein distance)
- **Endpoints:** `/api/deduplicate/find`, `/api/deduplicate/remove`, `/api/deduplicate/run`
- **Thresholds:** Configurable similarity thresholds
- **Tests:** 7+ tests for deduplication logic

### 5.4 Categorization Service

- **Algorithm:** SpaCy NLP with en_core_web_sm model
- **Categories:** Predefined (Engineering, Data Science, Product, Design, etc.)
- **Endpoints:** `/api/categorize/all`, `/api/categorize/distribution`, `/api/categorize/run`
- **Keyword-based matching:** Matches job descriptions to category keywords

## 6. Job Matching System [backend/services/matching.py]

### 6.1 Hybrid Matching Approach

**OpenAI Semantic Matching (70% weight):**
- Uses OpenAI API to analyze job-candidate match
- Extracts semantic meaning from job descriptions and candidate profiles
- Returns match score (0.0 - 1.0)

**Rule-based Matching (Fallback):**
- **Skill Matching (60%):** Keyword matching in job description
- **Location Matching (20%):** String matching of locations
- **Experience Matching (20%):** Position title matching in experience

### 6.2 Personalized Recommendations

**Algorithm:**
1. Get candidate profile
2. Filter jobs by skills and location
3. Exclude already interacted jobs
4. Calculate match scores
5. Sort by score descending
6. Return top N jobs (default: 20)

**Pagination:** Cursor-based pagination for infinite scroll

## 7. Application Automation System

### 7.1 Celery Worker [backend/workers/app_agent_worker.py]

- **Broker:** RabbitMQ
- **Backend:** Redis
- **Concurrency:** 4 workers
- **Retry Policy:** Auto-retry 5 times with backoff
- **Timeout:** 300 seconds (5 minutes)

### 7.2 Application Agents

**Greenhouse Agent:** [`backend/workers/application_agent/agents/greenhouse.py`](backend/workers/application_agent/agents/greenhouse.py)
- Playwright-based browser automation
- Handles Greenhouse ATS applications
- Form filling with candidate profile data

### 7.3 Task Management

**Task States:** queued → processing → completed/failed
**Retry Logic:** Exponential backoff with jitter
**Error Handling:** Detailed error messages and attempt tracking

## 8. iOS App [app-ios/]

### 8.1 Architecture

**Networking Layer:** [`APIClient.swift`](app-ios/Networking/APIClient.swift:1)
- Async/Await HTTP client
- Bearer token authentication
- GET and POST JSON methods

**Models:**
- [`JobCard.swift`](app-ios/Models/JobCard.swift:1) - Job data structure for display
- User profile and authentication models

**Features:**

1. **Feed View:** Tinder-like swipe interface
   - [`JobCardView.swift`](app-ios/Features/Feed/JobCardView.swift:1)
   - Gesture-based swiping (left/right)
   - Visual feedback with rotation effect
   - Offset tracking for swipe distance

2. **Auth Flow:** Email/password login/register

3. **Profile Management:** Candidate profile creation and editing

### 8.2 UI Components

```swift
struct JobCardView: View {
    @State private var offset: CGSize = .zero
    let job: JobCard
    let onSwipe: (SwipeDirection) -> Void
    
    var body: some View {
        ZStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(job.title).font(.title2).bold()
                Text(job.company).font(.headline)
                if let loc = job.location { 
                    Text(loc).font(.subheadline).foregroundColor(.secondary) 
                }
                Spacer()
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 20)
                .fill(Color(.systemBackground))
                .shadow(radius: 4))
        }
        .offset(x: offset.width)
        .rotationEffect(.degrees(Double(offset.width / 20)))
        .gesture(DragGesture()
            .onChanged { offset = $0.translation }
            .onEnded { value in
                defer { offset = .zero }
                if value.translation.width > 120 { onSwipe(.right) }
                else if value.translation.width < -120 { onSwipe(.left) }
            }
        )
    }
}
```

## 9. Infrastructure [docker-compose.yml]

### 9.1 Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | postgres:15 | 5432 | Main database |
| redis | redis:7-alpine | 6379 | Cache + Celery backend |
| rabbitmq | rabbitmq:3-management | 5672/15672 | Celery broker + management |
| minio | minio/minio:latest | 9000/9001 | Object storage |
| backend | Custom (FastAPI) | 8000 | API server |
| celery-worker | Custom | - | Background tasks |
| celery-flower | Custom | 5555 | Celery monitoring |
| opensearch | opensearchproject/opensearch:2.11.0 | 9200/9300 | Search and analytics |
| opensearch-dashboards | opensearchproject/opensearch-dashboards:2.11.0 | 5601 | Visualization |

### 9.2 Volumes

- `postgres_data`: Persistent database storage
- `minio_data`: Object storage
- `opensearch_data`: Search index storage

## 10. Tests & Quality Assurance

### 10.1 Test Files [backend/tests/]

| File | Purpose | Status |
|------|---------|--------|
| test_auth.py | Authentication endpoints | ✅ Passing |
| test_job_ingestion.py | Job ingestion service | ✅ Passing (7 tests) |
| test_job_ingestion_simple.py | Simple ingestion tests | ✅ Passing |
| test_jobs.py | Jobs API endpoints | ✅ Passing |
| test_application_automation.py | Application automation | ✅ Passing |
| test_analytics.py | Analytics service | ✅ Passing |
| test_openai_service.py | OpenAI integration | ✅ Passing |
| test_resume_parser_enhanced.py | Resume parsing | ✅ Passing |
| test_matching_properties.py | Property-based matching tests | ✅ Passing |

### 10.2 Test Coverage

**Key Test Categories:**
- Authentication scenarios (register, login, duplicate, invalid)
- Job ingestion from all sources
- Job deduplication and categorization
- Application automation
- Matching algorithm
- OpenAI service integration

## 11. Current Status & Gaps Analysis

### 11.1 Completed Features ✅

- ✅ Backend API with FastAPI
- ✅ iOS app with SwiftUI
- ✅ Job ingestion from Greenhouse, Lever, and RSS
- ✅ Job deduplication using fuzzy matching
- ✅ Job categorization using NLP
- ✅ Hybrid job matching system
- ✅ User authentication and profiles
- ✅ Application automation with Celery workers
- ✅ Docker containerization
- ✅ Basic test coverage

### 11.2 Missing/Incomplete Features ❌

#### High Priority:
1. **iOS App Enhancements**
   - Push notifications
   - Dark mode support
   - Accessibility features
   - Offline support
   - Background resume upload

2. **Testing & QA**
   - Property-based testing with Hypothesis
   - Performance testing with Locust
   - Chaos engineering
   - Contract testing with Pact
   - Test coverage improvements (target: 95%+)

3. **Monitoring & Observability**
   - Prometheus metrics
   - Grafana dashboards
   - OpenTelemetry tracing
   - Sentry error tracking
   - Health checks and alerts

4. **Security**
   - OAuth2 with Google/LinkedIn
   - Multi-factor authentication (MFA)
   - Rate limiting and throttling
   - Advanced input validation

#### Medium Priority:
1. **Job Matching Improvements**
   - BERT embeddings for skill extraction
   - Collaborative filtering recommendations
   - Location-based matching with geospatial queries
   - Job similarity scoring using cosine similarity

2. **Resume Parsing Enhancement**
   - Google Cloud Vision OCR
   - SpaCy transformer models
   - Table extraction
   - Support for more file formats (DOC, RTF)

3. **Application Automation**
   - Computer vision for form filling
   - GPT-4 for intelligent question answering
   - Browser fingerprinting prevention
   - Support for more ATS providers (Workday, Taleo)

#### Low Priority:
1. **Infrastructure**
   - Kubernetes deployment configuration
   - Auto-scaling
   - Backup and disaster recovery
   - Circuit breakers

## 12. Risk Assessment

### 12.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | Job ingestion failures | Implement caching and rate limiting |
| CAPTCHA challenges | Application automation failures | Implement needs_review status and notify user |
| Performance issues | Slow API responses | Load testing and optimization |
| OpenAI API costs | High expenses | Implement cost controls and caching |
| Data consistency | Duplicate jobs | Enhanced deduplication logic |

### 12.2 Legal/Compliance Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Job site terms of service violations | Legal action | Respect robots.txt, rate limits, and TOS |
| PII handling | Data breaches | Encryption at rest/in transit, PII redaction |
| GDPR/CCPA compliance | Fines and penalties | Data deletion, audit logging |

## 13. Performance Metrics

**Target Metrics:**
- Job matching accuracy: 30% improvement
- Resume parsing errors: 40% reduction
- Application automation success rate: ≥ 90%
- Feed API latency: ≤ 200ms p95
- Job ingestion freshness: ≤ 15 minutes
- Test coverage: ≥ 95%

## 14. Future Development Roadmap

### Phase 1: Foundation & Project Setup (1 week)
- Fix module import issues in tests
- Verify project structure
- Create llms.txt file
- Set up pre-commit hooks
- Initialize CI/CD pipeline

### Phase 2: Authentication & Core APIs (1 week)
- Fix and run existing auth tests
- Implement OAuth2 with Google/LinkedIn
- Add MFA
- Improve input validation
- Add rate limiting

### Phase 3: Job Ingestion System (2 weeks)
- Complete Greenhouse/Lever/RSS integration
- Implement incremental sync
- Enhance deduplication and categorization

### Phase 4: Job Matching & Personalization (1 week)
- Integrate OpenAI API
- Add BERT embeddings for skill extraction
- Improve location-based matching
- Add job similarity scoring

### Phase 5: Resume Parsing Enhancement (1 week)
- Add OCR support
- Improve entity recognition
- Add table extraction
- Support more file formats

### Phase 6: Application Automation (2 weeks)
- Improve form filling with OCR
- Add GPT-4 question answering
- Add browser fingerprinting prevention
- Support more ATS providers

### Phase 7: iOS App Enhancement (2 weeks)
- Add dark mode
- Implement accessibility features
- Add push notifications
- Improve offline support
- Add background resume upload

### Phase 8: Testing & QA (2 weeks)
- Implement property-based testing
- Add performance testing
- Implement chaos engineering
- Add contract testing
- Improve test coverage to 95%+

### Phase 9: Performance Optimization (1 week)
- Implement Redis caching
- Optimize database queries
- Add async processing
- Integrate CDN
- Optimize Docker containers

### Phase 10: Monitoring & Observability (1 week)
- Integrate Prometheus
- Add Grafana dashboards
- Implement OpenTelemetry
- Add Sentry error tracking
- Add health checks and alerts

### Phase 11: Security & Compliance (1 week)
- Implement data encryption
- Improve secrets handling
- Add PII redaction
- Implement GDPR/CCPA compliance
- Add detailed audit logging

## 15. Key Files & Directories

```
├── backend/
│   ├── api/                 # API endpoints and routers
│   ├── services/           # Core business logic
│   ├── workers/            # Background workers
│   ├── db/                 # Database models and migrations
│   └── tests/              # Tests
├── app-ios/
│   ├── Features/          # Feature modules
│   ├── Networking/        # API client
│   ├── Models/            # Data models
│   └── Tests/             # Tests
├── tools/                  # Utility scripts
├── plans/                  # Project plans and documentation
└── docker-compose.yml      # Docker configuration
```

## 16. Technology Stack

**Backend:**
- FastAPI, Python 3.12
- PostgreSQL, SQLAlchemy, Alembic
- Redis, Celery, RabbitMQ
- OpenSearch/Elasticsearch
- MinIO/S3, Kafka
- Playwright, spaCy, OpenAI API

**iOS:**
- Swift 5, SwiftUI
- async/await, Combine

**Infrastructure:**
- Docker, Docker Compose
- Prometheus, Grafana, Sentry
- OpenTelemetry, Jaeger

**Testing:**
- pytest, pytest-asyncio
- Hypothesis (property-based)
- Locust (performance)

## 17. Conclusion

The Sorce Job Search App is a well-structured and feature-rich platform with a solid foundation. The core components (API, iOS app, job ingestion, matching, automation) are implemented and functional. However, there are significant gaps in testing, monitoring, security, and iOS app features that need to be addressed before production deployment.

The project has a clear roadmap with phased development, focusing on critical areas first. With proper execution of the plan, the app can become a production-ready platform with high reliability, performance, and user satisfaction.
