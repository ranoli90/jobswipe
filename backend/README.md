# JobSwipe Backend API

Last deployed: 2026-02-03

The JobSwipe backend is a comprehensive FastAPI-based API server that powers the JobSwipe job search application. It provides AI-powered job matching, automated application systems, user management, and analytics services.

## Features

### 1. Authentication & User Management
- JWT-based authentication with configurable expiration
- Multi-factor authentication (TOTP + backup codes)
- OAuth2 integration (Google, LinkedIn)
- Account lockout and failed login tracking
- Encrypted PII storage with Fernet

### 2. Job Management & Matching
- AI-powered job matching using embeddings and BM25
- Job ingestion from RSS feeds, Greenhouse, and Lever APIs
- Fuzzy deduplication and categorization services
- Personalized job recommendations
- Search indexing with embeddings

### 3. Application Automation
- Playwright-based browser automation
- Captcha detection and human-in-the-loop systems
- Domain-specific rate limiting
- Audit logging for transparency
- Automated cover letter generation

### 4. Analytics & Reporting
- Matching accuracy metrics
- User behavior analytics
- Application success tracking
- Report generation (JSON/CSV)
- Performance monitoring with Prometheus

### 5. Notification System
- Push notifications (APNs/FCM integration)
- Email notifications with templates
- In-app notification management
- Scheduled and event-based notifications

### 6. Profile Management
- Resume parsing (PDF/DOCX)
- Skills extraction and matching
- Work experience tracking
- Profile completion analytics

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/mfa/setup` - MFA setup
- `POST /api/v1/auth/oauth2/google` - Google OAuth2 login

### Jobs
- `GET /api/v1/feed` - Get personalized job feed with matching
- `GET /api/v1/matches` - Get job matches with scores
- `GET /api/v1/jobs/search` - Search jobs with filters
- `GET /api/v1/jobs/{job_id}` - Get job details
- `POST /api/v1/jobs/{job_id}/swipe` - Record swipe action
- `POST /api/v1/jobs/{job_id}/save` - Save/unsave job
- `GET /api/v1/jobs/saved` - Get saved jobs

### Applications
- `GET /api/v1/applications` - Get user applications
- `POST /api/v1/applications` - Create application
- `GET /api/v1/applications/{job_id}/status` - Check application status
- `GET /api/v1/applications/{job_id}/audit` - Get application audit log
- `POST /api/v1/applications/{job_id}/cancel` - Cancel application
- `PUT /api/v1/applications/{job_id}` - Update application status
- `DELETE /api/v1/applications/{job_id}` - Delete application

### Profile
- `GET /api/v1/profile` - Get user profile
- `PUT /api/v1/profile` - Update profile
- `POST /api/v1/profile/resume` - Upload resume

### Notifications
- `GET /api/v1/notifications` - Get user notifications
- `GET /api/v1/notifications/unread-count` - Get unread notification count
- `PUT /api/v1/notifications/{id}/read` - Mark notification as read
- `PUT /api/v1/notifications/mark-all-read` - Mark all notifications as read
- `GET /api/v1/notifications/preferences` - Get notification preferences
- `PUT /api/v1/notifications/preferences` - Update notification preferences

### Analytics
- `GET /api/v1/analytics/metrics` - Get analytics metrics
- `POST /api/v1/analytics/generate-report` - Generate analytics report

### Ingestion (Admin)
- `POST /api/v1/ingestion/jobs` - Submit jobs for ingestion
- `POST /api/v1/ingestion/sources/greenhouse/sync` - Sync Greenhouse jobs
- `POST /api/v1/ingestion/sources/lever/sync` - Sync Lever jobs
- `POST /api/v1/ingestion/sources/rss/sync` - Sync RSS feeds

### Job Deduplication (Admin)
- `GET /api/v1/deduplicate/find` - Find duplicate jobs
- `POST /api/v1/deduplicate/remove` - Remove duplicate jobs
- `POST /api/v1/deduplicate/run` - Run deduplication process

### Job Categorization (Admin)
- `POST /api/v1/categorize/all` - Categorize all jobs
- `GET /api/v1/categorize/distribution` - Get category distribution
- `POST /api/v1/categorize/run` - Run categorization process

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /ready` - Readiness check
- `GET /health/detailed` - Comprehensive health check
- `GET /metrics` - Prometheus metrics

## Configuration

### Environment Variables

The backend uses comprehensive environment configuration for production deployment:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/jobswipe

# Redis
REDIS_URL=redis://host:6379

# JWT Authentication
SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption
ENCRYPTION_KEY=your-fernet-key

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# AI Services
OLLAMA_BASE_URL=http://ollama:11434

# Storage
MINIO_ENDPOINT=minio.example.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key

# API Keys for Internal Services
INGESTION_API_KEY=your-ingestion-api-key
DEDUPLICATION_API_KEY=your-deduplication-api-key
CATEGORIZATION_API_KEY=your-categorization-api-key
ANALYTICS_API_KEY=your-analytics-api-key
```

### API Keys Audit Results

**Audit Status: ✅ PASSED**

- **Validation**: All API keys validated via `tools/validate_secrets.py`
- **Management**: Secure storage using Fly.io secrets with production validation
- **Rotation**: Policy implemented for regular key rotation
- **Access Control**: Keys scoped to specific services with audit logging
- **Encryption**: All keys encrypted at rest and in transit
- **Monitoring**: Failed authentication attempts logged and monitored

**Recommendations Implemented:**
- No hardcoded API keys in codebase
- Environment-specific key validation
- Automated secret rotation reminders
- Comprehensive audit logging for key usage

### Security Configuration

- **Rate Limiting**: Redis-backed with different limits per endpoint
- **CORS**: Configured for mobile app origins
- **Security Headers**: CSP, HSTS, X-Frame-Options enabled
- **Input Validation**: Comprehensive sanitization and validation
- **PII Encryption**: Fernet encryption for sensitive user data

## Installation

### Dependencies

The system requires the following Python packages:

```
fastapi
uvicorn
pydantic
psycopg2-binary
sqlalchemy
alembic
redis
celery
httpx
playwright
beautifulsoup4
lxml
numpy
scipy
scikit-learn
spaCy
pytest
pytest-asyncio
pytest-cov
python-jose[cryptography]
passlib[bcrypt]
python-magic
minio
openai
python-dotenv
hypothesis
kafka-python
pymupdf
python-docx
pandas
numpy
fuzzywuzzy
python-Levenshtein
feedparser
```

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

### Database

The system uses PostgreSQL for storage. Make sure you have PostgreSQL installed and running. You can create the database tables using the SQL migration scripts in `/backend/db/migrations/`.

### SpaCy Model

The categorization service uses the spaCy library. You need to download the English language model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

### Starting the Server

To start the server, run:

```bash
uvicorn backend.api.main:app --reload
```

The server will be available at `http://localhost:8000`.

### API Documentation

API documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Testing

To run the tests, run:

```bash
pytest backend/tests/test_job_ingestion.py -v
```

This will run the tests for the job ingestion service.

## Architecture

The JobSwipe backend follows a modular, service-oriented architecture:

### Core Components

1. **API Layer** (`backend/api/`)
   - **Routers**: 9 API routers handling different domains (auth, jobs, applications, etc.)
   - **Middleware**: Comprehensive security and validation middleware stack
   - **Validators**: Pydantic-based request/response validation

2. **Service Layer** (`backend/services/`)
   - **15+ Services**: Modular business logic implementation
   - **AI Integration**: Ollama for embeddings and text processing
   - **Automation**: Playwright-based application automation
   - **External APIs**: Integration with job boards and social platforms

3. **Data Layer** (`backend/db/`)
   - **SQLAlchemy ORM**: Object-relational mapping with PostgreSQL
   - **Alembic Migrations**: Database schema versioning
   - **Models**: 10 core models with proper relationships
   - **Encryption**: Fernet-based PII encryption

4. **Infrastructure** (`backend/`)
   - **Configuration**: Pydantic-based settings management
   - **Metrics**: Prometheus integration for monitoring
   - **Tracing**: Distributed tracing setup
   - **Vault**: Secrets management integration

### Security Architecture

- **Authentication**: JWT with MFA and OAuth2
- **Authorization**: Role-based access control
- **Rate Limiting**: Redis-backed distributed rate limiting
- **Encryption**: End-to-end encryption for sensitive data
- **Audit Logging**: Comprehensive security event logging

### Deployment Architecture

- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Fly.io with auto-scaling
- **Databases**: PostgreSQL primary, Redis cache
- **AI Services**: Self-hosted Ollama for ML workloads
- **Monitoring**: Health checks, metrics, and alerting

## Codebase Analysis

Based on the [CODEBASE_ANALYSIS_REPORT.md](../CODEBASE_ANALYSIS_REPORT.md), the backend codebase has several areas for improvement:

### Key Findings
- **API Layer**: Well-structured with proper authentication and validation
- **Services**: 15+ modular services with AI integration (Ollama)
- **Database**: SQLAlchemy ORM with Alembic migrations
- **Security**: Comprehensive middleware stack (rate limiting, PII encryption)

### Areas for Improvement
- **Unused Code**: Remove unused imports, variables, and functions
- **Complex Code**: Refactor matching service and resume parser
- **Syntax Issues**: Fix syntax issues in several files
- **Testing**: Improve test structure to reduce redundancy

### Complex Code Areas
1. **Matching Service** (`matching.py`): Contains complex BM25 scoring and AI integration
2. **Resume Parser** (`resume_parser.py`): Complex text processing logic
3. **Database Models** (`models.py`): Intricate relationships between users, jobs, applications

## License

This project is licensed under the MIT License.