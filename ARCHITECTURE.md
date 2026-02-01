# JobSwipe Architecture Documentation

## Overview

JobSwipe is a production-ready job search application with a Tinder-like swipe interface, powered by AI matching and automation. This document describes the high-level architecture, design patterns, and key components of the system.

## Table of Contents

- [System Architecture](#system-architecture)
- [Backend Architecture](#backend-architecture)
- [Mobile App Architecture](#mobile-app-architecture)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Technology Stack](#technology-stack)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        JobSwipe System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Mobile     │      │    Backend   │      │   External   │  │
│  │     App      │◄────►│     API      │◄────►│   Services   │  │
│  │  (Flutter)   │      │   (FastAPI)  │      │              │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                     │                      │         │
│         │                     │                      │         │
│  ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐    │
│  │  Local DB   │      │  PostgreSQL │      │    Ollama   │    │
│  │   (Hive)    │      │    Redis    │      │    AI/ML    │    │
│  └─────────────┘      └─────────────┘      └─────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Architecture

### Overview

The backend is built with FastAPI and follows a layered architecture:

```
backend/
├── api/                    # API Layer
│   ├── main.py            # Application entry point
│   ├── dependencies.py    # Dependency injection
│   └── routers/           # API route handlers
├── services/              # Business Logic Layer
├── db/                    # Data Access Layer
│   ├── models.py         # SQLAlchemy models
│   └── database.py       # Database connection
├── workers/               # Background Workers (Celery)
└── config.py             # Configuration management
```

### API Layer

- **Framework**: FastAPI with async support
- **Authentication**: JWT tokens with OAuth2
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Middleware**: CORS, rate limiting, request logging

### Business Logic Layer

Key services include:
- **Auth Service**: User authentication and authorization
- **Job Service**: Job listing management and matching
- **Application Service**: Job application processing
- **Matching Service**: AI-powered job matching
- **Automation Service**: Browser automation for applications
- **Notification Service**: Push notifications and emails

### Data Access Layer

- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic
- **Caching**: Redis for session and rate limiting
- **Storage**: MinIO/S3 for file uploads

### Background Workers

Celery workers handle:
- Job matching calculations
- Email notifications
- Resume parsing
- Data ingestion from external sources

## Mobile App Architecture

### Overview

The mobile app is built with Flutter and follows the BLoC (Business Logic Component) pattern:

```
mobile-app/lib/
├── main.dart              # Application entry point
├── app.dart              # App configuration
├── config/               # Environment configuration
├── core/                 # Core functionality
│   ├── datasources/     # Data sources (API, local storage)
│   ├── data/            # Repository implementations
│   ├── models/          # Data models
│   ├── di/              # Dependency injection
│   └── theme/           # App theming
└── presentation/        # UI Layer
    ├── bloc/           # BLoC state management
    ├── screens/        # Screen widgets
    ├── widgets/        # Reusable widgets
    └── router/         # Navigation routing
```

### BLoC Pattern

The app uses BLoC (Business Logic Component) pattern for state management:

```
┌─────────────────────────────────────────────────────────────┐
│                      BLoC Pattern                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   UI Layer          BLoC Layer         Data Layer          │
│   ┌─────────┐      ┌─────────┐       ┌─────────────┐      │
│   │ Screen  │─────►│  Event  │       │ Repository  │      │
│   │ Widget  │      └────┬────┘       └──────┬──────┘      │
│   └────┬────┘           │                    │            │
│        │                ▼                    ▼            │
│        │           ┌─────────┐       ┌─────────────┐      │
│        │           │  BLoC   │◄─────►│   API/DB    │      │
│        │           └────┬────┘       └─────────────┘      │
│        │                │                                  │
│        │                ▼                                  │
│   ┌────▼────┐      ┌─────────┐                           │
│   │ Rebuild │◄─────│  State  │                           │
│   │   UI    │      └─────────┘                           │
│   └─────────┘                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### State Management Migration

The project migrated from using the `Either` type (from `dartz` package) to using try/catch patterns:

**Before (with Either):**
```dart
Future<Either<Failure, List<Job>>> getJobs() async {
  try {
    final jobs = await apiClient.getJobs();
    return Right(jobs);
  } catch (e) {
    return Left(ServerFailure(e.toString()));
  }
}
```

**After (with try/catch):**
```dart
Future<List<Job>> getJobs() async {
  try {
    final jobs = await apiClient.getJobs();
    return jobs;
  } catch (e) {
    rethrow;
  }
}
```

This simplifies the code and removes the dependency on the `dartz` package.

### Dependency Injection

Uses `get_it` for service location and dependency injection:

```dart
// Register services
getIt.registerLazySingleton<ApiClient>(() => ApiClient());
getIt.registerFactory<AuthBloc>(() => AuthBloc(getIt<AuthRepository>()));

// Use in widgets
final authBloc = getIt<AuthBloc>();
```

### Local Storage

- **Secure Storage**: For tokens and sensitive data
- **Hive**: For offline caching
- **SharedPreferences**: For app settings

## Data Flow

### Authentication Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───►│  Login  │───►│  Auth   │───►│  Token  │
│         │    │ Screen  │    │  BLoC   │    │ Storage │
└─────────┘    └────┬────┘    └────┬────┘    └─────────┘
                    │              │
                    │              ▼
                    │         ┌─────────┐
                    │         │  Auth   │
                    └────────►│   API   │
                              └─────────┘
```

### Job Matching Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───►│  Swipe  │───►│  Jobs   │───►│ Matching│
│ Action  │    │  Screen │    │  BLoC   │    │ Service │
└─────────┘    └─────────┘    └────┬────┘    └────┬────┘
                                   │              │
                                   │         ┌────▼────┐
                                   │         │ Ollama  │
                                   │         │   AI    │
                                   │         └────┬────┘
                                   │              │
                                   ▼              ▼
                              ┌─────────┐    ┌─────────┐
                              │  Jobs   │◄───│ Scores  │
                              │ Display │    │         │
                              └─────────┘    └─────────┘
```

## Security Architecture

### Authentication & Authorization

- **JWT Tokens**: Short-lived access tokens with refresh tokens
- **OAuth2**: Social login support (Google, LinkedIn)
- **MFA**: Time-based one-time passwords (TOTP)
- **Rate Limiting**: Redis-backed rate limiting per endpoint

### Data Protection

- **PII Encryption**: Fernet encryption for sensitive user data
- **Secure Storage**: Flutter Secure Storage for mobile tokens
- **HTTPS**: All API communication over TLS
- **Input Validation**: Pydantic models for request validation

### Security Headers

```python
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jobswipe.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Deployment Architecture

### Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                      Fly.io Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Backend    │  │   Worker     │  │   Ollama     │      │
│  │     API      │  │   Celery     │  │     AI       │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                   │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │   MinIO      │      │
│  │   Database   │  │    Cache     │  │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Push   │───►│   CI    │───►│   CD    │───►│ Deploy  │
│  Code   │    │  Tests  │    │  Build  │    │ to Fly  │
└─────────┘    └────┬────┘    └────┬────┘    └─────────┘
                    │              │
                    ▼              ▼
              ┌─────────┐    ┌─────────┐
              │  Lint   │    │ Docker  │
              │  Test   │    │  Push   │
              │ Coverage│    │         │
              └─────────┘    └─────────┘
```

## Technology Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Cache | Redis |
| Task Queue | Celery |
| AI/ML | Ollama |
| Testing | pytest |
| Deployment | Fly.io |

### Mobile

| Component | Technology |
|-----------|------------|
| Framework | Flutter 3.24 |
| Language | Dart |
| State Management | BLoC (flutter_bloc) |
| HTTP Client | Dio |
| DI | get_it |
| Local DB | Hive |
| Secure Storage | flutter_secure_storage |
| Testing | flutter_test |

### DevOps

| Component | Technology |
|-----------|------------|
| CI/CD | GitHub Actions |
| Container | Docker |
| Monitoring | Prometheus |
| Secrets | Fly.io Secrets |

## API Endpoints

### Authentication

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Jobs

- `GET /api/jobs/feed` - Get job feed
- `GET /api/jobs/matches` - Get matched jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/{id}/swipe` - Swipe on job

### Applications

- `GET /api/applications` - List applications
- `POST /api/applications` - Create application
- `GET /api/applications/{id}` - Get application details
- `PUT /api/applications/{id}` - Update application
- `DELETE /api/applications/{id}` - Delete application

### Profile

- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update profile
- `POST /api/profile/resume` - Upload resume

## Future Enhancements

- [ ] GraphQL API layer
- [ ] Real-time updates with WebSockets
- [ ] Machine learning model training pipeline
- [ ] Multi-region deployment
- [ ] Mobile app offline-first architecture
- [ ] Advanced analytics dashboard

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.