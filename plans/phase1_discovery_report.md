# JobSwipe Phase 1: Discovery & Mapping Analysis

## Project Overview

JobSwipe is a production-ready job search application with a Tinder-like swipe interface, powered by AI matching and automation. The project features:

- AI-Powered Job Matching using embeddings and BM25 algorithms
- Automated Application System with browser automation
- Cross-Platform Mobile App (Flutter-based iOS and Android)
- Comprehensive FastAPI Backend with 15+ services
- Security-First architecture with PII encryption, MFA, and OAuth2

**Readiness Score: ~70%**
- Backend: Production Ready
- Mobile App: In Development (basic structure created)
- Infrastructure: Production deployment on Fly.io

---

## Root Directory Structure

```
/home/brooketogo98/jobswipe/
├── backend/                 # FastAPI backend application
├── mobile-app/             # Flutter cross-platform mobile app
├── flutter/                # Flutter SDK for development
├── tools/                  # Utility scripts and deployment tools
├── backup/                 # Database backup and disaster recovery
├── .github/                # CI/CD workflows
├── packages/               # Shared packages (not explored)
├── plans/                  # Project plans and documentation
├── security/               # Security-related files
├── monitoring/             # Monitoring and observability
├── docker-compose.yml      # Local development orchestration
├── docker-compose.production.yml  # Production orchestration
├── Dockerfile              # Root Docker configuration
├── fly.toml                # Fly.io deployment config
├── Procfile                # Process manager configuration
├── README.md               # Project documentation
├── requirements.txt        # Root Python dependencies
└── [.env files]           # Environment configurations
```

---

## Technology Stack Analysis

### Frontend (Mobile App) - `/home/brooketogo98/jobswipe/mobile-app/`

**Framework & Language:**
- Flutter 3.24.0 (Dart 3.x)
- Cross-platform: iOS & Android

**Key Dependencies:**
- **State Management:** flutter_bloc ^8.1.3, equatable ^2.0.5
- **Networking:** dio ^5.4.0, pretty_dio_logger ^1.3.1, dio_smart_retry ^6.0.1
- **Local Storage:** shared_preferences, flutter_secure_storage, sqflite, hive
- **UI Components:** flutter_card_swiper, shimmer, lottie animations
- **Firebase Integration:** firebase_core, firebase_messaging, firebase_analytics, firebase_crashlytics
- **Utilities:** connectivity_plus, local_auth (biometrics), permission_handler

**Architecture:**
- BLoC pattern for state management
- Service Locator for dependency injection
- Clean architecture with data, domain, and presentation layers

**Build Configuration:**
- Android: Fastlane for deployment
- iOS: Fastlane with App Store Connect
- Multiple environments: Production, Staging, Development

---

### Backend - `/home/brooketogo98/jobswipe/backend/`

**Framework & Language:**
- FastAPI 0.109.1+ (Python 3.12)
- Uvicorn ASGI server
- Gunicorn for production

**Core Dependencies:**
- **Database:** SQLAlchemy 2.0.23, Alembic 1.13.1, psycopg2-binary
- **Cache:** Redis 5.0.1
- **Task Queue:** Celery 5.3.6 (RabbitMQ broker, Redis backend)
- **AI/ML:** Ollama 1.14+ (Llama 3.2:3b, nomic-embed-text)
- **Security:** python-jose (JWT), passlib (bcrypt), cryptography
- **Automation:** Playwright 1.40.0 for browser automation
- **Storage:** MinIO/S3 integration
- **Monitoring:** Prometheus, OpenTelemetry, Jaeger
- **Text Processing:** spaCy 3.7.2, scikit-learn, sentence-transformers
- **Parsing:** python-docx, PyMuPDF, pytesseract
- **APIs:** httpx, kafka-python

**API Architecture:**
- **Routers (9+):** auth, jobs, applications, profile, analytics, ingestion, automation, deduplication, categorization
- **Middleware Stack:** CORS, rate limiting, input sanitization, output encoding, compression, error handling
- **Validation:** Pydantic 2.5.0+
- **Security:** JWT authentication, MFA (TOTP), OAuth2 (Google, LinkedIn), API key authentication

---

### Database & Storage

**Primary Database:** PostgreSQL 15
- SQLAlchemy ORM with Alembic migrations
- Encrypted PII fields using Fernet encryption
- Key models: User, CandidateProfile, Job, ApplicationTask, Notification, ApiKey

**Cache:** Redis 7
- Rate limiting
- Session management
- Celery result backend

**Search & Analytics:** OpenSearch 2.11.0
- Search indexing
- Analytics and visualization via OpenSearch Dashboards

**Object Storage:** MinIO/S3 compatible
- Resume storage
- Application artifacts

**Secrets Management:** HashiCorp Vault
- Secure storage for API keys and secrets

---

### Infrastructure & Deployment

**Orchestration:**
- **Local Development:** Docker Compose (3.8)
- **Production:** Fly.io with auto-scaling

**Services in Docker Compose:**
- PostgreSQL: Port 5432
- Redis: Port 6379
- RabbitMQ: Ports 5672, 15672
- OpenSearch: Ports 9200, 9300
- OpenSearch Dashboards: Port 5601
- Prometheus: Port 9090
- Grafana: Port 3000
- Jaeger: Port 16686
- Vault: Port 8200
- Ollama: Port 11434

**Backend Deployment (Fly.io):**
- Primary region: iad (Virginia)
- App process: 1 vCPU, 1GB RAM
- Worker process: 1 vCPU, 2GB RAM
- Auto-scaling: Min 1 machine running
- Health check: `/health` endpoint

---

### CI/CD Pipeline - `.github/workflows/`

**Backend CI/CD** (`backend-ci-cd.yml`):
1. Secrets scan (TruffleHog)
2. Dependency review (GitHub Dependency Review)
3. Tests (pytest with coverage)
4. Database migration tests (Alembic)
5. CodeQL analysis
6. Security scan (Trivy)
7. Docker build
8. Docker image scan (Trivy)
9. Deploy to Staging (on develop branch push)
10. Deploy to Production (on main branch push)
11. Smoke tests after deployment

**Mobile CI/CD** (`mobile-ci-cd.yml`):
1. Flutter analyze
2. Flutter tests with coverage
3. Build Android APK and App Bundle
4. Build iOS IPA
5. Deploy to Staging (TestFlight + Internal Testing)
6. Deploy to Production (App Store + Play Store)

---

### Entry Points & Initialization

**Backend Entry Point:** `/home/brooketogo98/jobswipe/backend/api/main.py`
- Initializes FastAPI app with all middleware
- Sets up CORS, rate limiting, tracing, metrics
- Includes all API routers
- Health check endpoints: `/`, `/health`, `/ready`, `/metrics`
- Startup validation of environment configuration

**Backend Worker Entry Point:** `/home/brooketogo98/jobswipe/backend/workers/app_agent_worker.py`
- Celery worker for application automation
- Handles browser automation tasks via Playwright

**Mobile App Entry Point:** `/home/brooketogo98/jobswipe/mobile-app/lib/main.dart`
- Initializes Flutter app
- Sets up dependency injection
- Configures BLoC providers
- Handles routing

---

### Configuration Files

**Environment Variables:**
- `.env.example` - Example configuration
- `.env.development` - Development environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment
- `.env` - Current environment (gitignored)

**Backend Config:** `/home/brooketogo98/jobswipe/backend/config.py`
- Pydantic Settings with validation
- Environment-specific validation for production
- CORS configuration
- Secrets validation (prevents dev values in production)

**Fly.io Configs:**
- `fly.toml` - Root Fly.io config
- `backend/fly.toml` - Backend deployment config
- `backend/fly.staging.toml` - Staging deployment config

**Docker:**
- `Dockerfile` - Root Docker configuration
- `backend/Dockerfile` - Backend multi-stage build
- `backend/Dockerfile.api` - API-specific Dockerfile
- `backend/Dockerfile.automation` - Automation worker Dockerfile

---

### Module Dependencies Graph

```mermaid
graph TD
    A[Mobile App<br/>(Flutter)] -->|HTTP API| B[FastAPI Backend]
    
    B -->|Database| C[PostgreSQL]
    B -->|Cache/Queue| D[Redis]
    B -->|Message Broker| E[RabbitMQ]
    B -->|AI Services| F[Ollama LLM]
    B -->|Search| G[OpenSearch]
    B -->|Secrets| H[Vault]
    
    B -->|Automation Tasks| I[Celery Workers]
    I -->|Browser Automation| J[Playwright]
    
    K[Prometheus] -->|Metrics| B
    L[Grafana] -->|Visualization| K
    M[Jaeger] -->|Tracing| B
    
    N[GitHub Actions] -->|CI/CD| O[Fly.io Deployment]
    O -->|Hosting| B
```

---

### Key Services & Features

**Backend Services** (`/home/brooketogo98/jobswipe/backend/services/`):

1. **Authentication Service** - JWT, MFA, OAuth2
2. **User/Profile Service** - Profile management, resume parsing
3. **Job Matching Service** - AI-powered matching with embeddings
4. **Job Ingestion Service** - Greenhouse, Lever, RSS feed integration
5. **Job Deduplication** - Fuzzy matching for duplicate jobs
6. **Job Categorization** - spaCy-based categorization
7. **Application Automation** - Playwright browser automation
8. **Analytics Service** - User behavior and matching analytics
9. **Notification Service** - Push notifications (APNs/FCM), email
10. **Embedding Service** - Ollama-based text embeddings
11. **OpenAI Service** - (Disabled - replaced with Ollama)
12. **Storage Service** - S3/MinIO integration
13. **Domain Service** - ATS type detection, rate limiting
14. **Captcha Detector** - Human-in-the-loop captcha solving
15. **Cover Letter Service** - AI-generated cover letters

---

### Security Architecture

**Authentication:**
- JWT tokens with configurable expiration
- Multi-factor authentication (TOTP + backup codes)
- OAuth2 (Google, LinkedIn)
- Account lockout after failed attempts

**Encryption:**
- PII encryption using Fernet (symmetric encryption)
- API key hashing with bcrypt
- Encrypted secret storage via Vault

**Rate Limiting:**
- Redis-backed rate limiting
- Different limits per endpoint type (auth: 5/min, api: 60/min, public: 100/min)

**Input Validation:**
- Pydantic schema validation
- Input sanitization middleware
- Output encoding middleware

**Monitoring:**
- Comprehensive audit logging
- Security event logging to `security.log`
- Failed authentication tracking
- Rate limit violation tracking

---

### Testing & Quality

**Backend Tests** (`/home/brooketogo98/jobswipe/backend/tests/`):
- Unit tests for all services
- Integration tests for API endpoints
- E2E user flow tests
- Performance tests (database connection pooling)
- Concurrency tests

**Mobile Tests:**
- Widget tests
- Integration tests (API connectivity)

**Code Quality:**
- Black code formatter
- Flake8 linting
- Pylint for Python
- Flutter analyze for Dart

---

### Data Flow

**Job Matching Flow:**
1. Jobs ingested from external sources (Greenhouse, Lever, RSS)
2. Jobs indexed with embeddings
3. User profiles parsed and embedded
4. Matching algorithm (BM25 + embeddings) finds relevant jobs
5. Jobs returned as swipeable cards
6. User swipes left/right on jobs
7. Swipe actions stored as UserJobInteraction

**Application Automation Flow:**
1. User selects job to apply for
2. Application task created in queue
3. Celery worker picks up task
4. Playwright browser automation visits job page
5. Fills application form using profile data
6. Handles captcha via human-in-the-loop
7. Submits application
8. Stores application status and audit log

---

### External Integrations

**Job Boards:**
- Greenhouse API
- Lever API
- Custom RSS feeds

**Social Platforms:**
- Google OAuth2
- LinkedIn OAuth2

**Cloud Services:**
- Fly.io (Hosting, Postgres, Redis)
- AWS S3/MinIO (Storage)
- Firebase Cloud Messaging (Push notifications)
- Apple Push Notification service (APNs)

---

### Observability

**Metrics:** Prometheus endpoints at `/metrics`
- API request rate, latency
- Database connection pool usage
- Celery task queue size
- Ollama inference time
- Job matching performance

**Tracing:** Jaeger distributed tracing
- Request tracing across services
- Database query tracing
- External API call tracing

**Logging:** Structured JSON logging
- Application logs: `logs/app.log`
- Security logs: `logs/security.log`
- File rotation: 10MB per file, 5 backups

**Alerting:** Grafana dashboards and alerts
- Health check failures
- High error rates
- Rate limit violations
- Database connection issues

---

## Summary

JobSwipe is a well-architected, production-ready job search platform with:

1. **Comprehensive Backend**: FastAPI with 15+ modular services, extensive security measures, and AI integration
2. **Cross-Platform Mobile App**: Flutter-based app with BLoC architecture (in development)
3. **Scalable Infrastructure**: Fly.io deployment with auto-scaling, managed databases, and observability
4. **Robust CI/CD**: Automated testing, security scanning, and multi-environment deployment
5. **Security-First Design**: JWT, MFA, OAuth2, PII encryption, rate limiting, and comprehensive auditing
6. **AI-Powered Features**: Ollama-based embeddings, job matching, and cover letter generation
7. **Automation**: Playwright-based browser automation for job applications

The backend is fully production-ready, while the mobile app is in early development with basic structure complete but UI/features pending implementation.
