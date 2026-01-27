# JobSwipe

A production-ready job search application with a Tinder-like swipe interface, powered by AI matching and automation.

## Features

- **AI-Powered Job Matching**: Advanced matching using embeddings and BM25 algorithms
- **Automated Application System**: Browser automation for seamless job applications
- **Cross-Platform Mobile App**: Flutter-based iOS and Android app with swipe interface
- **Comprehensive Backend**: FastAPI backend with 15+ services and 9 API routers
- **Security-First**: PII encryption, rate limiting, MFA, and OAuth2 integration
- **Production Infrastructure**: Deployed on Fly.io with PostgreSQL, Redis, and Ollama AI

## Project Structure

- `backend/` - FastAPI backend with comprehensive API services
- `mobile-app/` - Flutter cross-platform mobile app (iOS & Android) - Basic structure created, implementation in progress
- `tools/` - Utility scripts and deployment tools
- `backup/` - Database backup and disaster recovery scripts
- `flutter/` - Flutter SDK for development and building
- `.github/` - CI/CD workflows for automated builds and deployments

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

### Mobile App
```bash
cd mobile-app
flutter pub get
flutter run
```

## Architecture

### Backend Architecture
- **Framework**: FastAPI with comprehensive middleware stack
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Cache**: Redis for rate limiting and session management
- **AI Services**: Ollama for embeddings and text processing
- **Security**: JWT authentication, MFA, OAuth2 (Google, LinkedIn)
- **Monitoring**: Prometheus metrics and structured logging

### Mobile Architecture
- **Framework**: Flutter with BLoC pattern (planned)
- **State Management**: BLoC for all features (Auth, Jobs, Applications, Profile) (to be implemented)
- **Networking**: Dio HTTP client with environment-based configuration (to be implemented)
- **Storage**: Flutter Secure Storage for sensitive data (to be implemented)
- **UI**: Material Design with custom swipe interface (to be implemented)

## Deployment

### Backend
Run `./tools/deploy_backend.sh` to deploy to Fly.io with automated secret validation.

### Mobile App
Use the GitHub Actions workflow in `.github/workflows/build_ios.yml` for building iOS IPAs without a Mac. For Android, run `./tools/deploy_mobile.sh` to build for production and deploy to app stores.

## External Services

- **Database**: PostgreSQL (Fly.io)
- **Cache**: Redis (Fly.io)
- **Storage**: MinIO/S3 compatible
- **AI/ML**: Ollama (self-hosted on Fly.io)
- **Deployment**: Fly.io with auto-scaling
- **Monitoring**: Prometheus metrics collection

## API Keys and Security

### API Keys Audit Results
- **Validation**: Automated secret validation via `tools/validate_secrets.py`
- **Management**: Fly.io secrets with production-specific validation
- **Encryption**: PII data encrypted using Fernet
- **Rate Limiting**: Redis-backed with configurable limits per endpoint
- **Audit Logging**: Comprehensive security event logging

### Security Features
- JWT authentication with configurable expiration
- Multi-factor authentication (TOTP + backup codes)
- OAuth2 social login (Google, LinkedIn)
- Account lockout mechanism after failed attempts
- Input sanitization and output encoding middleware
- CORS configuration and security headers

## Development

- Backend developed on Linux with Python 3.12/FastAPI
- Mobile app built with Flutter 3.x (cross-platform: iOS & Android)
- Testing: pytest for backend, Flutter test for mobile
- CI/CD: Automated testing and deployment pipelines

## Documentation

- [`PRODUCTION_DEPLOYMENT_GUIDE.md`](PRODUCTION_DEPLOYMENT_GUIDE.md) - Comprehensive deployment guide
- [`PRODUCTION_READINESS_SUMMARY.md`](PRODUCTION_READINESS_SUMMARY.md) - Production readiness checklist
- [`backend/README.md`](backend/README.md) - Backend API documentation
- [`backend_audit_report.md`](backend_audit_report.md) - Backend architecture audit
- [`infrastructure_audit_report.md`](infrastructure_audit_report.md) - Infrastructure audit
- [`mobile_app_audit_report.md`](mobile_app_audit_report.md) - Mobile app audit with build strategies

## Status

✅ **Backend**: Production Ready - Complete implementation with all features functional, security audited, and infrastructure deployed.

🔄 **Mobile App**: In Development - Basic Flutter structure created; requires implementation of UI, BLoC pattern, and data layer as detailed in `mobile_app_audit_report.md`

**Readiness Score: ~70%**
- Backend: Fully implemented with 15 services and comprehensive API
- Mobile App: Basic Flutter app structure; implementation in progress
- Infrastructure: Production deployment on Fly.io with monitoring
- Security: Comprehensive security measures and API key management
- Testing: Automated validation and deployment scripts
