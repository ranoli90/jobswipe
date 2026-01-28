# Email Notification Test Report

**Generated:** 2026-01-27T19:43:53.351597
**API Base URL:** https://api.example.com

## Summary
- Total Tests: 8
- Passed: 1
- Failed: 7

## Errors
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/register (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))
- HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

## Detailed Results
### ❌ Register and verify email for test@example.com
- Status: failed
- Time: 2026-01-27T19:43:53.877710
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/register (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Password reset request for test@example.com
- Status: failed
- Time: 2026-01-27T19:43:53.883575
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Password reset request for jobswipe.test@gmail.com
- Status: failed
- Time: 2026-01-27T19:43:53.887827
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Password reset request for jobswipe.test@outlook.com
- Status: failed
- Time: 2026-01-27T19:43:53.890212
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Password reset request for jobswipe.test@yahoo.com
- Status: failed
- Time: 2026-01-27T19:43:53.892057
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Password reset request for jobswipe.test@icloud.com
- Status: failed
- Time: 2026-01-27T19:43:53.893712
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ❌ Rate limiting on password reset endpoint
- Status: failed
- Time: 2026-01-27T19:43:53.895500
- Error: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded with url: /api/v1/auth/request-password-reset (Caused by NameResolutionError("HTTPSConnection(host='api.example.com', port=443): Failed to resolve 'api.example.com' ([Errno -5] No address associated with hostname)"))

### ✅ Email template rendering
- Status: passed
- Time: 2026-01-27T19:43:53.895726

