# Jobswipe Backend Audit - Complete Task List

## High Severity Issues

### Security Vulnerabilities
- [ ] Fix API key authentication bypass in `api_key_auth.py` - implement proper Bearer token extraction
- [ ] Remove hardcoded API key defaults in `config.py` - require explicit production configuration
- [ ] Fix missing asyncio import in `embedding_service.py`
- [ ] Replace hardcoded encryption key default in `vault_secrets.py`
- [ ] Fix log injection vulnerability in `auth.py` - use proper string formatting

### Performance Issues
- [ ] Fix database session management in `application_service.py` - use context managers
- [ ] Add Redis connection configuration in `embedding_cache.py` - use settings.redis_url
- [ ] Replace nested event loops in `ingestion_tasks.py` - use async Celery tasks

### Architectural Issues
- [ ] Refactor `application_service.py` to split responsibilities (God class pattern)
- [ ] Fix tight coupling in `auth.py` - extract security configuration to separate module

## Medium Severity Issues

### Code Quality Issues
- [ ] Extract duplicate `_profile_to_text` methods from `openai_service.py` and `embedding_service.py` to shared utility module
- [ ] Remove unused parameters (`screenshot`, `site_url`) from `captcha_detector.py`
- [ ] Replace debug print statement with logging in `application_service.py`
- [ ] Fix inconsistent error handling in `storage.py` - raise exceptions instead of returning None
- [ ] Add configuration for rate limiting in `api_key_auth.py` - remove magic numbers

### Testing Issues
- [ ] Add comprehensive test coverage for edge cases in `test_auth.py` (lockout, MFA, refresh tokens)
- [ ] Remove unnecessary print statements from `test_auth.py`

### Configuration Issues
- [ ] Improve configuration hierarchy in `config.py` and `vault_secrets.py` - single source of truth
- [ ] Update passlib configuration in `auth.py` - use argon2 as primary hashing scheme

## Low Severity Issues (Pylint Findings)

### Formatting and Style
- [ ] Fix indentation issues in `matching.py`
- [ ] Fix line length issues in `matching.py`, `captcha_detector.py`, and `storage.py`
- [ ] Remove trailing whitespace in multiple files
- [ ] Fix import order and unused imports in `matching.py`
- [ ] Fix logging format in `matching.py` - use lazy % formatting

### Minor Code Improvements
- [ ] Fix parsing errors in `embedding_worker.py`, `greenhouse.py`, and `lever.py` (indentation issues)
- [ ] Fix unused import in `captcha_detector.py` (typing.Any)
- [ ] Fix unused import in `embedding_service.py` (typing.Optional)

## Quick Fixes (< 5 minutes each)
1. [ ] Add `import asyncio` to `embedding_service.py`
2. [ ] Fix log injection in `auth.py` (line 296)
3. [ ] Replace print statements with logging in `application_service.py` and `test_auth.py`
4. [ ] Remove unused parameters from `captcha_detector.py`

## Performance Optimization Tasks
- [ ] Configure database connection pooling
- [ ] Implement cache invalidation strategies
- [ ] Add indexes to frequently queried database fields
- [ ] Optimize async task handling in Celery

## Security Hardening Tasks
- [ ] Rotate all default API keys and secrets in production
- [ ] Implement proper environment segregation
- [ ] Configure secrets management using HashiCorp Vault or AWS Secrets Manager
- [ ] Add logging and alerting for authentication failures

## Code Quality Improvements
- [ ] Enforce pylint in CI pipeline
- [ ] Add type hints to all functions and methods
- [ ] Improve docstrings with examples and error handling
- [ ] Add integration tests for all API endpoints

## Total Issues: 30+ tasks (10 high, 10 medium, 10+ low/quick fixes)