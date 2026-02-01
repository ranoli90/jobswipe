# Test Files Endpoint Path Fix Plan

## Summary

The report you provided is **ACCURATE**. I've verified the issue by examining:

1. **test_auth.py** - Contains inconsistent endpoint paths
2. **main.py** - Confirms routers are mounted with `/api/v1` prefix
3. **test_jobs.py** - Also has incorrect paths
4. **test_application_workflow.py** - Also has incorrect paths

## Root Cause

The backend API mounts routers with the prefix `/api/v1` (e.g., `/api/v1/auth/register`), but several test files incorrectly use `/v1/auth/register` (missing `/api`), causing 404 errors and KeyError crashes.

## Router Mounting Configuration (from backend/api/main.py)

```python
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(application_automation.router, prefix="/api/v1", tags=["application_automation"])
app.include_router(job_deduplication.router, prefix="/api/v1", tags=["deduplication"])
app.include_router(job_categorization.router, prefix="/api/v1", tags=["categorization"])
app.include_router(jobs_ingestion.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["api_keys"])
```

## Affected Files and Required Changes

### 1. backend/tests/test_auth.py
**Status:** MIXED (some correct, some incorrect)

| Line | Current Path | Correct Path |
|------|--------------|--------------|
| 16, 32, 38, 51, 59 | `/api/v1/auth/*` | ✅ Already correct |
| 78, 84 | `/v1/auth/*` | ❌ Should be `/api/v1/auth/*` |
| 97, 102, 109 | `/v1/auth/*` | ❌ Should be `/api/v1/auth/*` |

**Functions needing fixes:**
- `test_login_incorrect_password()` - Lines 77-88
- `test_get_me()` - Lines 96-113

### 2. backend/tests/test_jobs.py
**Status:** ALL INCORRECT

| Line | Current Path | Correct Path |
|------|--------------|--------------|
| 13 | `/v1/jobs/feed` | `/api/v1/jobs/feed` |
| 23, 28, 35 | `/v1/auth/*` | `/api/v1/auth/*` |
| 48, 53, 63 | `/v1/auth/*`, `/v1/jobs/*` | `/api/v1/auth/*`, `/api/v1/jobs/*` |
| 75, 80, 90 | `/v1/auth/*`, `/v1/jobs/*` | `/api/v1/auth/*`, `/api/v1/jobs/*` |

### 3. backend/tests/test_application_workflow.py
**Status:** ALL INCORRECT

| Line | Current Path | Correct Path |
|------|--------------|--------------|
| 53, 73, 83, 95, 108, 120 | `/v1/*` | `/api/v1/*` |
| 137, 159, 171, 191 | `/v1/*` | `/api/v1/*` |
| 210, 219, 233, 242, 251 | `/v1/auth/*` | `/api/v1/auth/*` |
| 267, 282, 296, 307 | `/v1/*` | `/api/v1/*` |

### 4. backend/tests/test_concurrency.py
**Status:** ALL CORRECT ✅

This file already uses `/api/v1/*` paths correctly.

## Additional Issues Found

Beyond the path issues, some tests have additional problems:

1. **test_login_incorrect_password()** in test_auth.py:
   - Uses `/v1/auth/register` and `/v1/auth/login` (wrong paths)
   - Doesn't check status codes before proceeding

2. **test_get_me()** in test_auth.py:
   - Uses `/v1/auth/*` paths
   - Line 106: `token = login_response.json()["access_token"]` will crash with KeyError if login fails

3. **test_application_workflow.py**:
   - Line 84, 243: Uses `json=` for login instead of `data=` (OAuth2PasswordRequestForm expects form data)
   - Many endpoints use `/v1/` instead of `/api/v1/`

## Recommended Fixes

### Fix 1: test_auth.py
Replace all `/v1/auth/` with `/api/v1/auth/` in:
- `test_login_incorrect_password()` (lines 77-88)
- `test_get_me()` (lines 96-113)

Add status code assertions before accessing JSON keys to prevent crashes.

### Fix 2: test_jobs.py
Replace all `/v1/` with `/api/v1/` throughout the file.

### Fix 3: test_application_workflow.py
Replace all `/v1/` with `/api/v1/` throughout the file.
Fix login requests to use `data=` instead of `json=` for OAuth2 form data.

## Verification

After fixes, all test files should:
1. Use `/api/v1/` prefix consistently
2. Check status codes before accessing response JSON
3. Use correct request format for OAuth2 endpoints (form data, not JSON)

## Files to Modify

1. `backend/tests/test_auth.py`
2. `backend/tests/test_jobs.py`
3. `backend/tests/test_application_workflow.py`

## Files Already Correct

- `backend/tests/test_concurrency.py` (uses correct `/api/v1/` paths)
