# JobSwipe Security & Quality Fix Plan

**Generated from:** `ranoli90_jobswipe (1).xlsx`  
**Date:** 2026-01-27  
**Mode:** Architect - Planning Phase

---

## Executive Summary

This document provides a comprehensive fix plan for all issues identified in the security and code quality analysis report. Issues are categorized by priority and include specific file paths, line numbers, and recommended fixes.

| Priority | Count | Description |
|----------|-------|-------------|
| 🔴 CRITICAL | 4 | SCA vulnerabilities requiring immediate upgrade |
| 🟠 HIGH | 9 | Secrets detection + SCA High + Infrastructure |
| 🟡 MEDIUM | 39 | SCA Medium + Infrastructure Security |
| 🟢 LOW | 7 | Swift Logger privacy issues |
| ⚪ MINOR | ~500+ | Code antipatterns and docstrings |

---

## 🔴 PRIORITY 1: CRITICAL SCA Vulnerabilities

### 1.1 Upgrade `python-jose` ≥ 3.4.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 3.3.0  
**Vulnerabilities:**
- `GHSA-h4pw-wxh7-4vjj` - DoS via compressed JWE content
- `GHSA-6c5p-j8vq-pqhj` - Algorithm confusion with OpenSSH ECDSA keys
- `GHSA-cjwg-qfpm-7377` - DoS via crafted JWT token

**Fix:**
```diff
- python-jose==3.3.0
+ python-jose>=3.4.0
```

---

### 1.2 Upgrade `pillow` ≥ 10.3.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 10.0.0  
**Vulnerabilities:**
- `GHSA-44wm-f244-xhp3` - Buffer overflow in `_imagingcms.c`
- `GHSA-3f63-hfp8-52jq` - Arbitrary Code Execution via `PIL.ImageMath.eval`
- `GHSA-j7hp-h8jx-5ppr` - OOB write in libwebp BuildHuffmanTable

**Fix:**
```diff
- pillow==10.0.0
+ pillow>=10.3.0
```

---

## 🟠 PRIORITY 2: HIGH - Secrets Detection (6 issues)

All secrets must be removed and replaced with environment variable references.

### 2.1 Remove Basic Auth credentials from `.env.example`

**File:** [`.env.example`](.env.example)

| Line | Issue | Action |
|------|-------|--------|
| 5 | Basic Auth Username | Replace with `BASIC_AUTH_USERNAME_PLACEHOLDER` |
| 11 | Basic Auth Password | Replace with `BASIC_AUTH_PASSWORD_PLACEHOLDER` |

**Recommended:**
```bash
# Lines 5, 11 should be removed or commented
# BASIC_AUTH_USERNAME=your_username_here
# BASIC_AUTH_PASSWORD=your_password_here
```

---

### 2.2 Remove credentials from `docker-compose.yml`

**File:** [`docker-compose.yml`](docker-compose.yml)

| Line | Issue | Action |
|------|-------|--------|
| 57 | Basic Auth Username | Remove or use `${BASIC_AUTH_USER}` |
| 58 | Basic Auth Password | Remove or use `${BASIC_AUTH_PASS}` |

**Current context (lines 57-58):**
```yaml
# Remove or replace with environment variables:
- BASIC_AUTH_USER=${BASIC_AUTH_USER}
- BASIC_AUTH_PASS=${BASIC_AUTH_PASS}
```

---

### 2.3 Remove credentials from `locustfile.py`

**File:** [`locustfile.py`](locustfile.py)

| Line | Issue | Action |
|------|-------|--------|
| 365 | Basic Auth Credentials | Remove hardcoded credentials, use environment variables |

**Fix:**
```python
# Replace hardcoded credentials with:
auth = (os.getenv("BASIC_AUTH_USER"), os.getenv("BASIC_AUTH_PASS"))
```

---

### 2.4 Remove secret keyword from `monitoring/grafana-fly.toml`

**File:** [`monitoring/grafana-fly.toml`](monitoring/grafana-fly.toml)

| Line | Issue | Action |
|------|-------|--------|
| 8 | Secret Keyword | Remove or replace with placeholder |

---

## 🟠 PRIORITY 3: HIGH SCA Vulnerabilities

### 3.1 Upgrade `python-multipart` ≥ 0.0.22

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 0.0.6  
**Vulnerabilities:**
- `GHSA-wp53-j4wj-2cfg` - Arbitrary File Write via Path Traversal
- `GHSA-59g5-xgcq-4qw3` - DoS via boundary deformation
- `GHSA-2jv5-9r88-3w3p` - Content-Type Header ReDoS

**Fix:**
```diff
- python-multipart==0.0.6
+ python-multipart>=0.0.22
```

---

### 3.2 Upgrade `fastapi` and related packages

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 0.104.1  
**Vulnerability:** `GHSA-qf9m-vfgh-m389` - Content-Type Header ReDoS

**Fix:**
```diff
- fastapi==0.104.1
+ fastapi>=0.109.1
```

---

### 3.3 Upgrade `gunicorn` ≥ 22.0.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 21.2.0  
**Vulnerabilities:**
- `GHSA-hc5x-x2vx-497g` - HTTP Request/Response Smuggling
- `GHSA-w3h3-4rj7-4ph4` - Request smuggling leading to endpoint bypass

**Fix:**
```diff
- gunicorn==21.2.0
+ gunicorn>=22.0.0
```

---

### 3.4 Upgrade `cryptography` ≥ 42.0.4

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 41.0.0  
**Vulnerabilities:**
- `GHSA-cf7p-gm2m-833m` - SSH certificates mishandling
- `GHSA-6vqw-3v5j-54x4` - NULL pointer dereference
- `GHSA-9v9h-cgj8-h64p` - NULL dereference in PKCS12 parsing
- `GHSA-3ww4-gg4f-jr7f` - Bleichenbacher timing oracle attack
- `GHSA-jfhm-5ghh-2f97` - NULL-dereference when loading PKCS7 certificates
- `GHSA-h4gh-qq45-vh27` - Vulnerable OpenSSL in wheels

**Fix:**
```diff
- cryptography==41.0.0
+ cryptography>=42.0.4
```

---

### 3.5 Upgrade `authlib` ≥ 1.6.6

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 1.3.0  
**Vulnerabilities:**
- `GHSA-fg6f-75jq-6523` - 1-click Account Takeover
- `GHSA-g7f3-828f-7h7m` - JWE zip=DEF decompression bomb
- `GHSA-pq5p-34cr-23v9` - DoS via Oversized JOSE Segments
- `GHSA-9ggr-2464-2j32` - JWS/JWT accepts unknown crit headers
- `GHSA-5357-c2jx-v7qh` - Algorithm confusion with asymmetric public keys

**Fix:**
```diff
- authlib==1.3.0
+ authlib>=1.6.6
```

---

### 3.6 Upgrade `brotli` ≥ 1.2.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 1.1.0  
**Vulnerability:** `GHSA-2qfp-q593-8484` - DoS attack via brotli decompression

**Fix:**
```diff
- brotli==1.1.0
+ brotli>=1.2.0
```

---

## 🟡 PRIORITY 4: MEDIUM SCA Vulnerabilities

### 4.1 Upgrade `black` ≥ 24.3.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 22.0  
**Vulnerability:** `GHSA-fj7x-q9j7-g6q6` - ReDoS via `lines_with_leading_tabs_expanded`

**Fix:**
```diff
- black==22.0
+ black>=24.3.0
```

---

### 4.2 Upgrade `scikit-learn` ≥ 1.5.0

**Files to modify:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`requirements.txt`](requirements.txt)

**Current version:** 1.3.2  
**Vulnerability:** `GHSA-jw8x-6495-233v` - Sensitive data leakage in TfidfVectorizer

**Fix:**
```diff
- scikit-learn==1.3.2
+ scikit-learn>=1.5.0
```

---

## 🟡 PRIORITY 5: Infrastructure Security (7 issues)

### 5.1 Fix GitHub Actions Workflows

#### 5.1.1 `.github/workflows/deploy-ios.yml`

| Issue | Line | Fix |
|-------|------|-----|
| Remove workflow_dispatch inputs | 8-15 | Remove all `inputs:` under `workflow_dispatch:` |
| Fix write-all permissions | 0-1 | Change `permissions: contents: write-all` to `contents: read` |

**Current (problematic):**
```yaml
on:
  workflow_dispatch:
    inputs:
      # Remove all inputs here
permissions:
  contents: write-all  # Change to read
```

**Fix:**
```yaml
on:
  workflow_dispatch: {}  # Empty inputs

permissions:
  contents: read
```

---

#### 5.1.2 `.github/workflows/deploy-android.yml`

| Issue | Line | Fix |
|-------|------|-----|
| Remove workflow_dispatch inputs | 8-20 | Remove all `inputs:` under `workflow_dispatch:` |
| Fix write-all permissions | 0-1 | Change to minimal required permissions |

---

#### 5.1.3 `.github/workflows/build_ios.yml`

| Issue | Line | Fix |
|-------|------|-----|
| Remove write-all permissions | 0-1 | Change to minimal required permissions |

---

#### 5.1.4 `.github/workflows/mobile-ci-cd.yml`

| Issue | Line | Fix |
|-------|------|-----|
| Remove write-all permissions | 0-1 | Change to minimal required permissions |

---

#### 5.1.5 `.github/workflows/backend-ci-cd.yml`

| Issue | Line | Fix |
|-------|------|-----|
| Remove write-all permissions | 0-1 | Change to minimal required permissions |

---

## 🟢 PRIORITY 6: LOW - Security Issues (7 issues)

### 6.1 Fix Logger Privacy in Swift Files

**File:** [`packages/JobSwipeCore/Sources/Networking/CacheManager.swift`](packages/JobSwipeCore/Sources/Networking/CacheManager.swift)

| Line | Issue | Fix |
|------|-------|-----|
| 36 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 77 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 109 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 120 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 138 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 153 | Logger without privacy config | Add `.privacy(.private)` to Logger |
| 164 | Logger without privacy config | Add `.privacy(.private)` to Logger |

**Example Fix:**
```swift
// Before
let logger = Logger(subsystem: "com.jobswipe", category: "CacheManager")

// After
let logger = Logger(subsystem: "com.jobswipe", category: "CacheManager")
logger.logLevel = .debug
// Or use privacy: 
// Logger(subsystem: "com.jobswipe", category: "CacheManager").log(level: .debug, "message")
```

---

## ⚪ PRIORITY 7: Code Antipatterns

### 7.1 Fix C++ Memory Issues in Windows Runner

**File:** [`mobile-app/windows/runner/win32_window.cpp`](mobile-app/windows/runner/win32_window.cpp)

| Line | Issue | Severity |
|------|-------|----------|
| 16 | Replace macro with const/enum | Critical |
| 8 | Add name to namespace | Major |
| 30 | Global variables should be const | Critical |
| 30 | Remove redundant "static" specifier | Minor |
| 66 | Replace `new` with automatic memory management | Critical |

---

### 7.2 Fix Constants in `locustfile.py`

**File:** [`locustfile.py`](locustfile.py)

| Line | Issue | Fix |
|------|-------|-----|
| 122 | Duplicate literal "/api/jobs/personalized" 4 times | Define constant `PERSONALIZED_JOBS_ENDPOINT` |
| 111 | Duplicate literal "/api/profile/" 3 times | Define constant `PROFILE_ENDPOINT` |

**Example Fix:**
```python
# Add at top of file
PERSONALIZED_JOBS_ENDPOINT = "/api/jobs/personalized"
PROFILE_ENDPOINT = "/api/profile/"

# Then use the constants instead of string literals
```

---

### 7.3 Fix `datetime` Usage in `resume_parser.py`

**File:** [`backend/services/resume_parser.py`](backend/services/resume_parser.py)

| Line | Issue |
|------|-------|
| 499 | Don't use `datetime.datetime.utcnow()` |

**Fix:**
```python
# Before
from datetime import datetime
created_at = datetime.utcnow()

# After (Python 3.11+)
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)

# Or use pendulum library if available
```

---

## ⚪ PRIORITY 8: Documentation - Add Docstrings (52 functions)

### 8.1 Backend Service Functions

| File | Function | Line |
|------|----------|------|
| [`backend/services/oauth2_service.py`](backend/services/oauth2_service.py) | `__init__` | 43 |
| [`backend/services/notification_service.py`](backend/services/notification_service.py) | `__init__` | 46 |
| [`backend/services/push_notification_service.py`](backend/services/push_notification_service.py) | `__init__` | 238 |
| [`backend/api/main.py`](backend/api/main.py) | `__call__` | 128 |
| [`backend/api/main.py`](backend/api/main.py) | `startup` | 173 |
| [`backend/api/main.py`](backend/api/main.py) | `rate_limit_exceeded_handler` | 213 |
| [`backend/api/main.py`](backend/api/main.py) | `__call__` | 263 |
| [`backend/api/main.py`](backend/api/main.py) | `global_exception_handler` | 370 |
| [`backend/api/main.py`](backend/api/main.py) | `wrapped_send` | 268 |
| [`backend/api/main.py`](backend/api/main.py) | `SecurityHeadersMiddleware` | 259 |
| [`backend/api/websocket_manager.py`](backend/api/websocket_manager.py) | `__init__` | 54 |
| [`backend/api/validators.py`](backend/api/validators.py) | `validate_string` | 43 |
| [`backend/api/validators.py`](backend/api/validators.py) | `validate_email` | 59 |
| [`backend/api/validators.py`](backend/api/validators.py) | `validate_phone` | 74 |
| [`backend/api/middleware/api_key_auth.py`](backend/api/middleware/api_key_auth.py) | `check_permissions` | 208 |
| [`backend/api/middleware/file_validation.py`](backend/api/middleware/file_validation.py) | `__init__` | 76 |
| [`backend/api/middleware/input_sanitization.py`](backend/api/middleware/input_sanitization.py) | `__init__` | 19 |
| [`backend/api/middleware/input_sanitization.py`](backend/api/middleware/input_sanitization.py) | `dispatch` | 38 |
| [`backend/api/middleware/compression.py`](backend/api/middleware/compression.py) | `dispatch` | 86 |
| [`backend/api/middleware/error_handling.py`](backend/api/middleware/error_handling.py) | `__init__` | 29 |
| [`backend/api/middleware/error_handling.py`](backend/api/middleware/error_handling.py) | `__init__` | 144 |
| [`backend/config.py`](backend/config.py) | `validate_secrets` | 105 |
| [`backend/config.py`](backend/config.py) | `Settings` | 7 |
| [`backend/metrics.py`](backend/metrics.py) | `__call__` | 692 |
| [`backend/workers/embedding_worker.py`](backend/workers/embedding_worker.py) | `__init__` | 32 |

### 8.2 Backend Alembic Migration Functions

| File | Function | Line |
|------|----------|------|
| [`backend/alembic/versions/005_add_api_keys_tables.py`](backend/alembic/versions/005_add_api_keys_tables.py) | `upgrade` | 20 |

### 8.3 Security and Tools Functions

| File | Function | Line |
|------|----------|------|
| [`security/security_dashboard.py`](security/security_dashboard.py) | `SecurityDashboard` | 13 |
| [`tools/rotate_secrets.py`](tools/rotate_secrets.py) | `main` | 103 |
| [`tools/validate_secrets.py`](tools/validate_secrets.py) | `main` | 174 |
| [`tools/validate_secrets.py`](tools/validate_secrets.py) | `SecretValidator` | 20 |

### 8.4 Mobile App C++ Functions

| File | Function | Line |
|------|----------|------|
| [`mobile-app/windows/runner/utils.cpp`](mobile-app/windows/runner/utils.cpp) | `CreateAndAttachConsole` | 10 |
| [`mobile-app/windows/runner/utils.cpp`](mobile-app/windows/runner/utils.cpp) | `GetCommandLineArguments` | 24 |
| [`mobile-app/windows/runner/utils.cpp`](mobile-app/windows/runner/utils.cpp) | `Utf8FromUtf16` | 44 |
| [`mobile-app/windows/runner/main.cpp`](mobile-app/windows/runner/main.cpp) | `APIENTRY wWinMain` | 8 |
| [`mobile-app/windows/runner/flutter_window.cpp`](mobile-app/windows/runner/flutter_window.cpp) | `FlutterWindow::OnCreate` | 12 |
| [`mobile-app/windows/runner/flutter_window.cpp`](mobile-app/windows/runner/flutter_window.cpp) | `FlutterWindow::MessageHandler` | 50 |

### 8.5 Mobile App Dart Functions

| File | Function | Line |
|------|----------|------|
| [`mobile-app/lib/models/notification.dart`](mobile-app/lib/models/notification.dart) | `copyWith` | 56 |

---

## Implementation Order

### Phase 1: Immediate (Critical & High Priority)
1. ✅ Remove all hardcoded secrets from files
2. ✅ Upgrade `python-jose` to ≥ 3.4.0
3. ✅ Upgrade `pillow` to ≥ 10.3.0
4. ✅ Upgrade `python-multipart` to ≥ 0.0.22
5. ✅ Upgrade all other critical SCA packages

### Phase 2: Short-term (Medium Priority)
1. Fix GitHub Actions workflow permissions
2. Remove workflow_dispatch inputs
3. Upgrade remaining SCA packages
4. Fix Swift Logger privacy issues

### Phase 3: Medium-term (Code Quality)
1. Fix C++ memory issues in Windows runner
2. Fix datetime usage patterns
3. Add constants to eliminate duplicates
4. Fix logging lazy formatting

### Phase 4: Long-term (Documentation)
1. Add docstrings to all 52 identified functions
2. Consider adding automated docstring generation

---

## Files Modified Summary

| Category | Files Count | Priority |
|----------|-------------|----------|
| Secrets Removal | 4 files | 🔴 HIGH |
| SCA Vulnerabilities | 2-3 files | 🔴 CRITICAL |
| GitHub Actions | 5 files | 🟡 MEDIUM |
| Swift Logger | 1 file | 🟢 LOW |
| C++ Antipatterns | 1 file | ⚪ MINOR |
| Python Antipatterns | 3-5 files | ⚪ MINOR |
| Docstrings | 25+ files | ⚪ MINOR |

---

## Verification Steps

After implementing fixes:

1. **Secrets:** Run `trufflehog` or similar to verify no secrets remain
2. **SCA:** Run `safety check` or `pip-audit` to verify vulnerabilities are fixed
3. **Infrastructure:** Run `checkov` on GitHub Actions workflows
4. **Code Quality:** Run `pylint`/`flake8` to verify antipatterns are fixed
5. **Security:** Run Swift static analyzer for Logger issues

---

## Notes

- Always test after upgrading dependencies
- Review breaking changes in upgrade notes
- Consider creating a security rotation script for leaked credentials
- Document all environment variables that replace hardcoded values
