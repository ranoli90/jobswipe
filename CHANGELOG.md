# Changelog

All notable changes to the JobSwipe project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with FastAPI backend and Flutter mobile app
- Comprehensive backend API with 15+ services
- BLoC pattern implementation for state management
- AI-powered job matching using embeddings and BM25 algorithms
- Automated job application system with browser automation
- Cross-platform mobile app (iOS & Android) with swipe interface
- Security features: PII encryption, rate limiting, MFA, OAuth2
- Production deployment on Fly.io with PostgreSQL, Redis, and Ollama AI
- CI/CD pipelines for automated testing and deployment
- Comprehensive documentation and audit reports

### Changed
- Migrated from Either type to try/catch pattern in BLoC files
- Standardized all backend imports to use absolute imports with `backend.` prefix
- Updated API endpoint configuration to use production URL
- Fixed import paths across all presentation layer files

### Fixed
- Fixed broken `_onProfileWorkExperienceUpdateRequested` method in ProfileBloc
- Fixed import inconsistencies in BLoC files
- Fixed service locator registration for BLoCs
- Removed duplicate dependencies from pubspec.yaml
- Standardized application ID to `com.jobswipe.jobswipe`

### Removed
- Removed unused `dartz` dependency
- Removed unused `flutter_riverpod` dependency
- Removed unused `riverpod_annotation` dependency
- Removed duplicate `numpy` from requirements.txt
- Deleted deprecated directories: `mobile-app/lib/data/`, `screens/`, `providers/`, `repositories/`
- Deleted deprecated `service_locator.dart` in `mobile-app/lib/core/`

## [1.0.0] - 2026-01-31

### Added
- Production-ready job search application
- Tinder-like swipe interface for job matching
- AI matching using embeddings and BM25 algorithms
- Browser automation for seamless job applications
- FastAPI backend with comprehensive middleware stack
- Flutter cross-platform mobile app
- JWT authentication with configurable expiration
- Multi-factor authentication (TOTP + backup codes)
- OAuth2 social login (Google, LinkedIn)
- Account lockout mechanism after failed attempts
- Input sanitization and output encoding middleware
- CORS configuration and security headers
- PostgreSQL database with SQLAlchemy ORM
- Redis for rate limiting and session management
- Ollama AI for embeddings and text processing
- MinIO/S3 compatible storage
- Prometheus metrics and structured logging
- Fly.io deployment with auto-scaling
- GitHub Actions CI/CD workflows

### Security
- PII data encryption using Fernet
- Rate limiting with Redis-backed configurable limits
- Comprehensive security event logging
- Automated secret validation
- API key management
- Security scanning in CI/CD pipeline

[Unreleased]: https://github.com/yourusername/jobswipe/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/jobswipe/releases/tag/v1.0.0