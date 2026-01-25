# Sorce-like Job Search App (iOS)

A complete iOS job search app with backend API, job ingestion, matching, and automation agents.

## Features

- **iOS App**: SwiftUI-based app with Tinder-like swipe interface for job cards
- **Backend API**: FastAPI-based API with authentication, profile management, and job feed
- **Job Ingestion**: Automated ingestion from Greenhouse, Lever, and RSS feeds
- **Matching System**: Hybrid BM25 + embeddings + rule-based matching
- **Application Automation**: Playwright-based agents that apply to jobs on behalf of users
- **Observability**: Complete monitoring and logging system

## Project Structure

```
├── backend/                  # FastAPI backend
│   ├── api/                 # API endpoints
│   │   ├── main.py         # API entry point
│   │   └── routers/        # API routers
│   ├── workers/            # Background workers
│   │   ├── ingestion/      # Job ingestion workers
│   │   └── application_agent/ # Application automation agents
│   ├── db/                 # Database models and migrations
│   ├── services/           # Core business logic
│   └── tests/              # Tests
├── app-ios/                # iOS app
│   ├── Networking/        # API client
│   ├── Features/          # Feature modules
│   │   ├── Auth/
│   │   ├── Feed/
│   │   └── Applications/
│   ├── Models/            # Data models
│   └── Tests/             # Tests
├── tools/                  # Utility scripts
└── docker-compose.yml      # Docker configuration
```

## Getting Started

### Backend Setup

```bash
# Clone the repository
git clone <repo-url>
cd sorce-job-search-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the API
uvicorn api.main:app --reload
```

### iOS App Setup

```bash
# Install dependencies
cd app-ios
pod install

# Open Xcode
open SorceJobSearch.xcworkspace

# Run the app
```

## API Documentation

API documentation is available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

## Technologies

- **Backend**: FastAPI, Python 3.12, PostgreSQL, Redis, Celery, Playwright
- **iOS**: Swift 5, SwiftUI, async/await
- **Search**: OpenSearch/Elasticsearch
- **Storage**: S3/MinIO
- **Queue**: RabbitMQ
- **Observability**: Prometheus, Grafana, ELK

## Compliance

- Respect robots.txt and Terms of Service for all job sources
- No CAPTCHA bypass or anti-bot measures
- PII encryption at rest
- Strict rate limiting

## License

Internal use only. Do not use to violate any site's Terms of Service.
