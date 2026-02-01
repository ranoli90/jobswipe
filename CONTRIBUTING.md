# Contributing to JobSwipe

Thank you for your interest in contributing to JobSwipe! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [Questions](#questions)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Accept responsibility and apologize when mistakes are made

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your feature or bug fix

```bash
# Clone your fork
git clone https://github.com/yourusername/jobswipe.git
cd jobswipe

# Add upstream remote
git remote add upstream https://github.com/original/jobswipe.git

# Create a new branch
git checkout -b feature/your-feature-name
```

## Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn backend.api.main:app --reload
```

### Mobile App Setup

```bash
cd mobile-app

# Install Flutter dependencies
flutter pub get

# Run the app
flutter run
```

## Project Structure

```
jobswipe/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes and routers
│   ├── db/                 # Database models and migrations
│   ├── services/           # Business logic services
│   ├── workers/            # Celery background workers
│   └── tests/              # Backend tests
├── mobile-app/             # Flutter mobile application
│   ├── lib/
│   │   ├── config/         # App configuration
│   │   ├── core/           # Core utilities, datasources, repositories
│   │   ├── models/         # Data models
│   │   └── presentation/   # BLoCs, screens, widgets
│   └── test/               # Mobile app tests
├── .github/                # GitHub Actions workflows
└── docs/                   # Documentation
```

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters
- Use `black` for code formatting
- Use `isort` for import sorting

```bash
# Format code
black backend/
isort backend/

# Run linting
flake8 backend/
mypy backend/
```

### Dart (Mobile)

- Follow the [Effective Dart](https://dart.dev/guides/language/effective-dart) style guide
- Use `flutter analyze` to check for issues
- Format code with `dart format`
- Use meaningful variable and function names

```bash
# Format code
dart format lib/

# Analyze code
flutter analyze

# Run tests
flutter test
```

## Making Changes

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions or updates

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semi colons, etc)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(auth): add OAuth2 login support

fix(api): resolve race condition in job matching

docs(readme): update installation instructions
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Mobile Tests

```bash
cd mobile-app

# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Run specific test file
flutter test test/bloc/auth_bloc_test.dart
```

### Integration Tests

```bash
# Backend integration tests
cd backend
pytest tests/integration/

# Mobile integration tests
cd mobile-app
flutter test integration_test/
```

## Submitting Changes

1. Ensure all tests pass
2. Update documentation if needed
3. Add entries to CHANGELOG.md
4. Commit your changes with a clear message
5. Push to your fork
6. Create a Pull Request

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Review Process

1. All pull requests require at least one review
2. CI checks must pass before merging
3. Address review comments promptly
4. Squash commits before merging if requested
5. Maintainers will merge approved PRs

## Questions

If you have questions or need help:

- Check existing [issues](https://github.com/yourusername/jobswipe/issues)
- Create a new issue with the `question` label
- Join our community discussions

## License

By contributing to JobSwipe, you agree that your contributions will be licensed under the same license as the project.