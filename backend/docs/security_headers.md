# Security Headers Documentation

## Overview

The JobSwipe API implements comprehensive security headers to protect against common web vulnerabilities. These headers are set by the `SecurityHeadersMiddleware` in the FastAPI application.

## Security Headers Implementation

The following security headers are implemented:

### 1. Content Security Policy (CSP)
```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:
```

**Directives Explained:**
- `default-src 'self'`: Default policy for all resources is to only load from the same origin
- `script-src 'self' 'unsafe-inline' 'unsafe-eval'`: Allows scripts from same origin, inline scripts, and eval (for debugging purposes)
- `style-src 'self' 'unsafe-inline'`: Allows styles from same origin and inline styles
- `img-src 'self' data:`: Allows images from same origin and data URLs
- `font-src 'self' data:`: Allows fonts from same origin and data URLs

### 2. X-Frame-Options
```http
X-Frame-Options: DENY
```
Prevents the API from being embedded in iframes, protecting against clickjacking attacks.

### 3. X-XSS-Protection
```http
X-XSS-Protection: 1; mode=block
```
Enables browser XSS protection and configures it to block malicious scripts rather than sanitizing.

### 4. X-Content-Type-Options
```http
X-Content-Type-Options: nosniff
```
Prevents browsers from interpreting files as a different MIME type than what is specified in the Content-Type header, protecting against MIME type confusion attacks.

### 5. Referrer Policy
```http
Referrer-Policy: strict-origin-when-cross-origin
```
Controls how much referrer information is included with requests. Sends full URL for same-origin requests, but only sends origin for cross-origin requests.

## Implementation Details

The security headers are set in the `SecurityHeadersMiddleware` class in `/backend/api/main.py`. This middleware wraps all HTTP responses and adds the security headers.

```python
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message["headers"].append(
                    (b"content-security-policy", 
                     b"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:")
                )
                message["headers"].append((b"x-frame-options", b"DENY"))
                message["headers"].append((b"x-xss-protection", b"1; mode=block"))
                message["headers"].append((b"x-content-type-options", b"nosniff"))
                message["headers"].append((b"referrer-policy", b"strict-origin-when-cross-origin"))
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

## Testing

### Unit Tests

A self-contained test script is available at `/backend/tests/security_headers_test.py` that tests the middleware directly without requiring all app dependencies.

To run the test:
```bash
python3 backend/tests/security_headers_test.py
```

### Integration Tests

Integration tests are available at `/backend/tests/test_security_headers.py` that test the middleware through the actual API endpoints.

To run the tests:
```bash
pytest backend/tests/test_security_headers.py -v
```

## Modifying Security Headers

If you need to update or modify the security headers:

1. Edit the `SecurityHeadersMiddleware` class in `/backend/api/main.py`
2. Update the test script in `/backend/tests/security_headers_test.py`
3. Run the tests to verify the changes
4. Update this documentation file if necessary

## Considerations

- The CSP is currently configured with `unsafe-inline` and `unsafe-eval` to support development and debugging. For production environments, these should be removed if possible.
- The security headers are applied to all HTTP responses from the API.
- CORS headers should be configured separately if the API is accessed from browsers on different origins.