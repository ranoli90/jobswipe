# JobSwipe Security Remediation - Detailed Implementation Plan

## Executive Summary

This document provides a comprehensive, step-by-step implementation plan to address all critical and warning-level security findings identified in the codebase review. Each remediation item includes technical specifications, code examples, testing requirements, and deployment considerations.

**Total Estimated Effort:** 3-4 developer weeks
**Critical Path:** 1 week (P0 items)
**Recommended Team:** 2 backend engineers, 1 mobile engineer, 1 DevOps engineer

---

## Phase 1: Critical Security Fixes (Week 1)

### P0-1: Firebase API Key Security Remediation

#### Current State
- Firebase API key hardcoded in `mobile-app/android/app/google-services.json`
- File committed to version control
- API key exposed in APK/IPA builds

#### Target State
- Firebase configuration managed via environment-specific files
- API keys injected at build time via CI/CD
- Original key rotated and revoked

#### Implementation Steps

**Step 1.1: Immediate Key Rotation (Day 1)**
```bash
# Actions to perform immediately:
1. Log into Google Cloud Console
2. Navigate to APIs & Services > Credentials
3. Find the Firebase API key
4. Click "Delete" or "Restrict Key"
5. Create new API key with restricted permissions
6. Update Firebase project settings
```

**Step 1.2: Create Environment Configuration Structure**
```
mobile-app/
├── config/
│   ├── firebase/
│   │   ├── google-services.json.development    # Template only
│   │   ├── google-services.json.staging        # Template only
│   │   └── google-services.json.production     # Template only
│   └── .gitignore                              # Ignore all real configs
```

**Step 1.3: Create Configuration Template**
```json
// mobile-app/config/firebase/google-services.json.template
{
  "project_info": {
    "project_number": "${FIREBASE_PROJECT_NUMBER}",
    "project_id": "${FIREBASE_PROJECT_ID}",
    "storage_bucket": "${FIREBASE_STORAGE_BUCKET}"
  },
  "client": [
    {
      "client_info": {
        "mobilesdk_app_id": "${FIREBASE_MOBILESDK_APP_ID}",
        "android_client_info": {
          "package_name": "${ANDROID_PACKAGE_NAME}"
        }
      },
      "oauth_client": [],
      "api_key": [
        {
          "current_key": "${FIREBASE_API_KEY}"
        }
      ],
      "services": {
        "appinvite_service": {
          "other_platform_oauth_client": []
        }
      }
    }
  ],
  "configuration_version": "1"
}
```

**Step 1.4: Create Build Configuration Script**
```dart
// mobile-app/tools/setup_firebase.dart
import 'dart:io';

void main() {
  final env = Platform.environment['ENV'] ?? 'development';
  final templateFile = File('config/firebase/google-services.json.template');
  final outputFile = File('android/app/google-services.json');
  
  if (!templateFile.existsSync()) {
    stderr.writeln('Firebase template not found');
    exit(1);
  }
  
  var content = templateFile.readAsStringSync();
  
  // Replace environment variables
  final replacements = {
    r'${FIREBASE_PROJECT_NUMBER}': Platform.environment['FIREBASE_PROJECT_NUMBER'] ?? '',
    r'${FIREBASE_PROJECT_ID}': Platform.environment['FIREBASE_PROJECT_ID'] ?? '',
    r'${FIREBASE_STORAGE_BUCKET}': Platform.environment['FIREBASE_STORAGE_BUCKET'] ?? '',
    r'${FIREBASE_MOBILESDK_APP_ID}': Platform.environment['FIREBASE_MOBILESDK_APP_ID'] ?? '',
    r'${ANDROID_PACKAGE_NAME}': Platform.environment['ANDROID_PACKAGE_NAME'] ?? 'com.jobswipe.jobswipe',
    r'${FIREBASE_API_KEY}': Platform.environment['FIREBASE_API_KEY'] ?? '',
  };
  
  replacements.forEach((key, value) {
    content = content.replaceAll(key, value);
  });
  
  outputFile.writeAsStringSync(content);
  print('Firebase configuration generated for $env environment');
}
```

**Step 1.5: Update CI/CD Pipeline**
```yaml
# .github/workflows/build_android.yml
jobs:
  build:
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Firebase Config
        env:
          FIREBASE_API_KEY: ${{ secrets.FIREBASE_API_KEY }}
          FIREBASE_PROJECT_NUMBER: ${{ secrets.FIREBASE_PROJECT_NUMBER }}
          FIREBASE_PROJECT_ID: ${{ secrets.FIREBASE_PROJECT_ID }}
          FIREBASE_STORAGE_BUCKET: ${{ secrets.FIREBASE_STORAGE_BUCKET }}
          FIREBASE_MOBILESDK_APP_ID: ${{ secrets.FIREBASE_MOBILESDK_APP_ID }}
        run: dart tools/setup_firebase.dart
      
      - name: Build APK
        run: flutter build apk --dart-define=ENV=production
```

**Step 1.6: Add .gitignore Rules**
```gitignore
# mobile-app/.gitignore additions
android/app/google-services.json
ios/Runner/GoogleService-Info.plist
config/firebase/*.json
!config/firebase/*.template
```

**Step 1.7: Remove Existing Key from Git History**
```bash
# Use git-filter-repo or BFG Repo-Cleaner
# WARNING: This rewrites history - coordinate with team

# Option 1: Using git-filter-repo
git filter-repo --path mobile-app/android/app/google-services.json --invert-paths

# Option 2: Using BFG
bfg --delete-files google-services.json

# Force push after team coordination
git push --force
```

#### Testing Requirements
- [ ] Verify build fails without environment variables
- [ ] Verify build succeeds with valid environment variables
- [ ] Verify Firebase services work in built app
- [ ] Verify API key is not present in APK (use `apktool d` to inspect)

#### Rollback Plan
- Keep old API key active for 48 hours after deployment
- Monitor Firebase console for any rejected requests
- Have team on standby for hotfix if needed

---

### P0-2: Secrets Management Overhaul

#### Current State
- Auto-generated secrets when environment variables missing
- Different keys on every restart
- No production validation

#### Target State
- Strict validation in production
- Clear error messages on missing secrets
- Support for secret rotation

#### Implementation Steps

**Step 2.1: Create Environment Validator**
```python
# backend/core/environment_validator.py
import os
from typing import List, Optional
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class SecretRequirement:
    def __init__(
        self,
        name: str,
        min_length: int = 32,
        required_in: List[Environment] = None,
        validator: Optional[callable] = None
    ):
        self.name = name
        self.min_length = min_length
        self.required_in = required_in or [Environment.PRODUCTION]
        self.validator = validator

class EnvironmentValidator:
    REQUIRED_SECRETS = [
        SecretRequirement("SECRET_KEY", min_length=32),
        SecretRequirement("DATABASE_URL", min_length=20),
        SecretRequirement("ENCRYPTION_PASSWORD", min_length=32),
        SecretRequirement("ENCRYPTION_SALT", min_length=16),
        SecretRequirement("OAUTH_STATE_SECRET", min_length=32),
        SecretRequirement("REDIS_URL", min_length=10),
    ]
    
    FORBIDDEN_PATTERNS = [
        "dev-", "test-", "example", "placeholder",
        "change-me", "your-", "xxx", "password123"
    ]
    
    @classmethod
    def validate(cls, environment: str) -> List[str]:
        errors = []
        env = Environment(environment)
        
        for secret in cls.REQUIRED_SECRETS:
            value = os.getenv(secret.name)
            
            # Check if required in this environment
            if env in secret.required_in:
                if not value:
                    errors.append(f"{secret.name} is required in {environment}")
                    continue
                
                # Check minimum length
                if len(value) < secret.min_length:
                    errors.append(
                        f"{secret.name} must be at least {secret.min_length} characters"
                    )
                
                # Check forbidden patterns
                value_lower = value.lower()
                for pattern in cls.FORBIDDEN_PATTERNS:
                    if pattern in value_lower:
                        errors.append(
                            f"{secret.name} contains forbidden pattern: {pattern}"
                        )
                
                # Run custom validator if provided
                if secret.validator:
                    try:
                        secret.validator(value)
                    except ValueError as e:
                        errors.append(f"{secret.name} validation failed: {e}")
        
        return errors
    
    @classmethod
    def validate_or_raise(cls, environment: str):
        errors = cls.validate(environment)
        if errors:
            raise RuntimeError(
                f"Environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
```

**Step 2.2: Update Settings Class**
```python
# backend/config.py
from backend.core.environment_validator import EnvironmentValidator

class Settings(BaseSettings):
    # ... existing fields ...
    
    @model_validator(mode='after')
    def validate_environment(self):
        """Validate all required secrets are present in production"""
        EnvironmentValidator.validate_or_raise(self.environment)
        return self
    
    # Remove auto-generation for critical secrets
    secret_key: str = Field(..., env="SECRET_KEY")  # Required, no default
    encryption_password: str = Field(..., env="ENCRYPTION_PASSWORD")
    encryption_salt: str = Field(..., env="ENCRYPTION_SALT")
    oauth_state_secret: str = Field(..., env="OAUTH_STATE_SECRET")
    
    # Development-only fallbacks
    @field_validator('secret_key', 'encryption_password', 'encryption_salt', 'oauth_state_secret')
    def allow_dev_fallback(cls, v, info):
        env = os.getenv('ENVIRONMENT', 'development')
        if v is None and env == 'development':
            # Only in development, generate a warning
            import warnings
            warnings.warn(f"{info.field_name} not set, using insecure fallback")
            return secrets.token_urlsafe(32)
        return v
```

**Step 2.3: Create Secret Generation Tool**
```python
# backend/tools/generate_secrets.py
#!/usr/bin/env python3
"""Generate secure secrets for production deployment"""

import secrets
import sys

def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure secret"""
    return secrets.token_urlsafe(length)

def main():
    print("# JobSwipe Production Secrets")
    print("# Add these to your Fly.io secrets or environment:")
    print()
    
    secrets_to_generate = {
        "SECRET_KEY": 32,
        "ENCRYPTION_PASSWORD": 32,
        "ENCRYPTION_SALT": 16,
        "OAUTH_STATE_SECRET": 32,
        "ANALYTICS_API_KEY": 32,
        "INGESTION_API_KEY": 32,
        "DEDUPLICATION_API_KEY": 32,
        "CATEGORIZATION_API_KEY": 32,
        "AUTOMATION_API_KEY": 32,
    }
    
    for name, length in secrets_to_generate.items():
        value = generate_secret(length)
        print(f"{name}={value}")
    
    print()
    print("# Set in Fly.io:")
    print("# flyctl secrets set SECRET_KEY=<value> ENCRYPTION_PASSWORD=<value> ...")

if __name__ == "__main__":
    main()
```

**Step 2.4: Update Startup Validation**
```python
# backend/api/main.py
@app.on_event("startup")
async def startup():
    logger.info("Validating environment configuration...")
    
    if settings:
        try:
            # Run validation
            EnvironmentValidator.validate_or_raise(settings.environment)
            logger.info("✅ Environment configuration validation successful")
            logger.info("Environment: %s", settings.environment)
        except RuntimeError as e:
            logger.error("❌ Environment validation failed: %s", e)
            # In production, fail fast
            if settings.environment == "production":
                sys.exit(1)
            else:
                logger.warning("Continuing despite validation errors in non-production")
    else:
        logger.error("Settings not available - cannot start")
        sys.exit(1)
```

#### Testing Requirements
- [ ] Unit tests for EnvironmentValidator
- [ ] Integration test: App fails to start with missing secrets in production
- [ ] Integration test: App starts with warnings in development
- [ ] Test secret generation script output

---

### P0-3: Remove Debug Print Statements

#### Implementation Steps

**Step 3.1: Create Logging Audit Script**
```python
# backend/tools/audit_logging.py
#!/usr/bin/env python3
"""Audit codebase for improper logging patterns"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

class LoggingAuditor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Tuple[str, int, str]] = []
    
    def visit_Call(self, node):
        # Check for print statements
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.issues.append((self.current_file, node.lineno, "print() statement found"))
        
        # Check for logger calls with tuple arguments (format string bug)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['info', 'debug', 'warning', 'error', 'critical']:
                # Check if any argument is a tuple
                for arg in node.args[1:] if len(node.args) > 1 else []:
                    if isinstance(arg, ast.Tuple):
                        self.issues.append(
                            (self.current_file, node.lineno, 
                             f"Logger call with tuple argument: {node.func.attr}()")
                        )
        
        self.generic_visit(node)
    
    def audit_file(self, filepath: Path) -> List[Tuple[str, int, str]]:
        self.current_file = str(filepath)
        self.issues = []
        
        try:
            tree = ast.parse(filepath.read_text())
            self.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
        
        return self.issues

def main():
    backend_dir = Path(__file__).parent.parent
    auditor = LoggingAuditor()
    all_issues = []
    
    for pyfile in backend_dir.rglob("*.py"):
        if "__pycache__" in str(pyfile):
            continue
        issues = auditor.audit_file(pyfile)
        all_issues.extend(issues)
    
    if all_issues:
        print("Logging issues found:")
        for file, line, issue in all_issues:
            print(f"  {file}:{line} - {issue}")
        sys.exit(1)
    else:
        print("No logging issues found!")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Step 3.2: Fix Identified Issues**

Replace in `backend/db/database.py`:
```python
# BEFORE:
print(f"DEBUG: Engine created successfully: {engine}", file=sys.stderr)

# AFTER:
logger.debug("Database engine created successfully")
```

Replace in `backend/services/application_service.py`:
```python
# BEFORE:
logger.debug("DEBUG: job.source = '%s', type = %s", getattr(job, 'source', 'NONE'), type(getattr(job, 'source', 'NONE')))

# AFTER:
logger.debug("Processing job - source: %s, type: %s", 
             getattr(job, 'source', 'NONE'), 
             type(getattr(job, 'source', 'NONE')).__name__)
```

**Step 3.3: Add Pre-commit Hook**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: audit-logging
        name: Audit logging patterns
        entry: python backend/tools/audit_logging.py
        language: system
        pass_filenames: false
        always_run: true
```

---

### P0-4: Fix Email Validation

#### Implementation Steps

**Step 4.1: Update Validators**
```python
# backend/api/validators.py
from pydantic import EmailStr
from email_validator import validate_email, EmailNotValidError

def email_validator():
    """Validator for email fields with proper validation"""
    
    def validate_email_field(cls, v):
        if not v or len(v) > 255:
            raise ValueError("Email must be between 1 and 255 characters")
        
        try:
            # Use email_validator library for RFC-compliant validation
            validation = validate_email(v, check_deliverability=False)
            return validation.email  # Returns normalized email
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email format: {str(e)}")
    
    return validator("email", pre=True, allow_reuse=True)(validate_email_field)
```

**Step 4.2: Add email-validator to Requirements**
```
email-validator>=2.1.0
```

---

### P0-5: Fix Log Format String Bugs

#### Implementation Steps

**Step 5.1: Fix in job_ingestion_service.py**
```python
# BEFORE:
logger.info("Ingested %s jobs from %s", ('jobs_ingested', 'source_name'))

# AFTER:
logger.info("Ingested %s jobs from %s", jobs_ingested, source_name)
```

**Step 5.2: Fix in ingestion_tasks.py**
```python
# BEFORE:
logger.info("Ingested %s jobs from %s", ('jobs_ingested', 'source_name'))
logger.error("Failed to ingest jobs from %s: %s", ('source_name', 'e'))

# AFTER:
logger.info("Ingested %s jobs from %s", jobs_ingested, source_name)
logger.error("Failed to ingest jobs from %s: %s", source_name, str(e))
```

---

## Phase 2: High-Priority Fixes (Week 2)

### P1-1: Fix JWT Refresh Token Logic

#### Implementation
```python
# backend/api/routers/auth.py

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token with longer expiration"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### P1-2: Fix Request Deduplication Redis URL

#### Implementation
```python
# backend/api/middleware/request_deduplication.py

async def get_redis(self) -> Optional[redis.Redis]:
    """Get or create Redis client"""
    if self._redis is None:
        try:
            self._redis = redis.from_url(
                settings.redis_url,  # Fixed: was settings.REDIS_URL
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            pass
    return self._redis
```

### P1-3: Add CORS Production Validation

#### Implementation
```python
# backend/config.py

@field_validator('cors_allow_origins')
def validate_cors_in_production(cls, v):
    env = os.getenv('ENVIRONMENT', 'development')
    if env == 'production':
        for origin in v:
            if 'localhost' in origin or '127.0.0.1' in origin:
                raise ValueError(
                    f"localhost/127.0.0.1 not allowed in production CORS: {origin}"
                )
            if origin.startswith('http://'):
                raise ValueError(
                    f"HTTP not allowed in production CORS, use HTTPS: {origin}"
                )
    return v
```

---

## Phase 3: Medium-Priority Improvements (Week 3)

### P2-1: Comprehensive Health Checks

#### Implementation
```python
# backend/api/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import redis.asyncio as redis
from typing import Dict, Any
import asyncio

router = APIRouter()

async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        from backend.db.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "response_time_ms": 0}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        from backend.config import settings
        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_ollama() -> Dict[str, Any]:
    """Check Ollama AI service"""
    try:
        from backend.services.openai_service import OpenAIService
        is_available = OpenAIService.is_available()
        return {
            "status": "ok" if is_available else "degraded",
            "available": is_available
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_ollama(),
    )
    
    results = {
        "database": checks[0],
        "redis": checks[1],
        "ollama": checks[2],
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Overall status
    all_ok = all(c["status"] == "ok" for c in checks)
    any_error = any(c["status"] == "error" for c in checks)
    
    if any_error:
        results["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=results)
    elif not all_ok:
        results["status"] = "degraded"
    else:
        results["status"] = "healthy"
    
    return results

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness check"""
    db_check = await check_database()
    if db_check["status"] != "ok":
        raise HTTPException(status_code=503, detail={"ready": False})
    return {"ready": True}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness check"""
    return {"alive": True}
```

### P2-2: Mobile Certificate Pinning

#### Implementation
```dart
// mobile-app/lib/core/datasources/remote/api_client.dart
import 'package:dio/io.dart';
import 'dart:io';

class ApiClient {
  final Dio _dio;
  
  ApiClient(this._dio, this._secureStorage) {
    _setupInterceptors();
    _setupCertificatePinning();
  }
  
  void _setupCertificatePinning() {
    if (AppConfig.isProduction) {
      (_dio.httpClientAdapter as IOHttpClientAdapter).onHttpClientCreate =
          (client) {
        client.badCertificateCallback =
            (X509Certificate cert, String host, int port) {
          // Pin specific certificate SHA-256 hashes
          final pinnedCerts = [
            'SHA256_HASH_OF_PROD_CERT_1',
            'SHA256_HASH_OF_PROD_CERT_2',
          ];
          
          final certHash = sha256.convert(cert.der).toString();
          return pinnedCerts.contains(certHash);
        };
        return client;
      };
    }
  }
}
```

### P2-3: Circuit Breaker Pattern

#### Implementation
```python
# backend/core/circuit_breaker.py
from enum import Enum
from typing import Callable, Optional
from datetime import datetime, timedelta
import asyncio
import functools

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpen("Circuit breaker is OPEN")
            
            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.half_open_max_calls:
                    raise CircuitBreakerOpen("Circuit breaker half-open limit reached")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(
            seconds=self.recovery_timeout
        )
    
    async def _on_success(self):
        async with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

class CircuitBreakerOpen(Exception):
    pass

# Usage decorator
def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60
):
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Phase 4: Low-Priority Improvements (Week 4)

### P3-1: API Key Rate Limiting

#### Implementation
```python
# backend/api/middleware/api_key_rate_limiting.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from backend.config import settings

class APIKeyRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limits = {
            "default": (100, 3600),  # 100 requests per hour
            "internal": (1000, 3600),  # 1000 requests per hour
        }
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to API key authenticated routes
        if not request.url.path.startswith("/api/v1/internal/"):
            return await call_next(request)
        
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)
        
        # Check rate limit
        key = f"rate_limit:api_key:{api_key}"
        
        if self.redis:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 3600)
            
            limit, _ = self.rate_limits["internal"]
            if current > limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"API key rate limit exceeded. Limit: {limit}/hour"
                )
        
        return await call_next(request)
```

### P3-2: Request ID in Error Responses

#### Implementation
```python
# backend/api/middleware/error_handling.py (update)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "message": "An unexpected error occurred. Please try again later."
        }
    )
```

---

## Testing Strategy

### Unit Tests
```python
# backend/tests/test_security_remediation.py

class TestEnvironmentValidator:
    def test_missing_required_secret_in_production(self):
        with pytest.raises(RuntimeError) as exc_info:
            with patch.dict(os.environ, {'ENVIRONMENT': 'production'}, clear=True):
                EnvironmentValidator.validate_or_raise('production')
        assert 'SECRET_KEY is required' in str(exc_info.value)
    
    def test_forbidden_pattern_detected(self):
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'dev-secret-key-123'
        }):
            errors = EnvironmentValidator.validate('production')
            assert any('dev-' in e for e in errors)

class TestCircuitBreaker:
    async def test_opens_after_threshold(self):
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Simulate failures
        for _ in range(3):
            try:
                await breaker.call(async_func_that_fails)
            except:
                pass
        
        with pytest.raises(CircuitBreakerOpen):
            await breaker.call(async_func_that_succeeds)
```

### Integration Tests
```python
# backend/tests/integration/test_security.py

class TestSecurityIntegration:
    async def test_app_fails_without_secrets_in_prod(self):
        # Start app with production env but no secrets
        # Should exit with error code
        pass
    
    async def test_health_check_comprehensive(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert data["status"] in ["healthy", "degraded"]
```

### Security Tests
```python
# backend/tests/security/test_api_security.py

class TestAPISecurity:
    def test_cors_blocks_localhost_in_production(self):
        # Simulate production CORS config
        # Make request from localhost origin
        # Should be rejected
        pass
    
    def test_rate_limiting_on_api_keys(self):
        # Make requests exceeding limit
        # Should receive 429 response
        pass
    
    def test_request_deduplication(self):
        # Send identical requests rapidly
        # Second should be rejected or deduplicated
        pass
```

---

## Deployment Plan

### Pre-Deployment Checklist
- [ ] All P0 items completed and tested
- [ ] Security audit script passes
- [ ] Integration tests pass
- [ ] Load testing completed
- [ ] Rollback plan documented

### Deployment Sequence
1. **Phase 0 (Day 1)**: Rotate Firebase API key immediately
2. **Phase 1 (Week 1)**: Deploy P0 fixes
3. **Phase 2 (Week 2)**: Deploy P1 fixes
4. **Phase 3 (Week 3)**: Deploy P2 improvements
5. **Phase 4 (Week 4)**: Deploy P3 improvements

### Rollback Procedures
```bash
# Emergency rollback script
#!/bin/bash
# rollback.sh

echo "Rolling back to previous version..."

# 1. Restore previous Fly deployment
flyctl deploy --image-ref jobswipe:previous

# 2. Restore previous secrets (if changed)
# Secrets should be versioned in secure storage

# 3. Verify rollback
curl https://api.jobswipe.com/health

echo "Rollback complete"
```

---

## Monitoring & Alerting

### Metrics to Track
```python
# Add to backend/metrics.py

# Security-related metrics
security_validation_failures = Counter(
    "security_validation_failures_total",
    "Security validation failures",
    ["type"]
)

circuit_breaker_state_changes = Counter(
    "circuit_breaker_state_changes_total",
    "Circuit breaker state changes",
    ["service", "from_state", "to_state"]
)

api_key_rate_limit_hits = Counter(
    "api_key_rate_limit_hits_total",
    "API key rate limit hits",
    ["key_prefix"]
)
```

### Alerts
```yaml
# alerts.yml
groups:
  - name: security
    rules:
      - alert: HighSecurityValidationFailures
        expr: rate(security_validation_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High rate of security validation failures"
      
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state_changes_total{to_state="open"} > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker opened for {{ $labels.service }}"
```

---

## Documentation Updates

### Developer Documentation
- Update `CONTRIBUTING.md` with security requirements
- Add `SECURITY.md` with vulnerability disclosure process
- Document secret management procedures

### Operations Documentation
- Update deployment runbooks
- Document monitoring and alerting setup
- Create incident response procedures

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Zero hardcoded secrets | 100% | Automated scan passes |
| Security validation | 100% | All P0/P1 items resolved |
| Test coverage | >80% | Coverage report |
| Deployment success | 100% | Zero rollbacks |
| Performance impact | <5% | Load test comparison |

---

## Appendix

### A. Secret Generation Commands
```bash
# Generate secure random secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# For Fly.io
flyctl secrets set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

### B. Testing Commands
```bash
# Run all security tests
pytest backend/tests/security/ -v

# Run with coverage
pytest --cov=backend --cov-report=html backend/tests/

# Security audit
python backend/tools/audit_logging.py
python backend/tools/audit_secrets.py
```

### C. Monitoring Queries
```promql
# Security validation failures
rate(security_validation_failures_total[5m])

# Circuit breaker states
circuit_breaker_state_changes_total

# API key rate limits
rate(api_key_rate_limit_hits_total[5m])
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-01*
*Owner: Security Team*