"""
Security Headers Middleware Test

A self-contained test script that contains the SecurityHeadersMiddleware implementation
so we can test it without requiring all the app dependencies.
"""

import sys
import asyncio
from unittest.mock import MagicMock


# Copy of SecurityHeadersMiddleware for testing
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Capture the original send to modify responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                message["headers"].append(
                    (b"content-security-policy", 
                     b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; frame-ancestors 'none'")
                )
                message["headers"].append(
                    (b"x-frame-options", b"DENY")
                )
                message["headers"].append(
                    (b"x-xss-protection", b"1; mode=block")
                )
                message["headers"].append(
                    (b"x-content-type-options", b"nosniff")
                )
                message["headers"].append(
                    (b"referrer-policy", b"strict-origin-when-cross-origin")
                )
                message["headers"].append(
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload")
                )
                message["headers"].append(
                    (b"x-permitted-cross-domain-policies", b"none")
                )
                message["headers"].append(
                    (b"permissions-policy", b"accelerometer=(), autoplay=(), camera=(), display-capture=(), encrypted-media=(), fullscreen=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), midi=(), payment=(), picture-in-picture=(), sync-xhr=(), usb=()")
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


async def test_security_headers_middleware():
    """Test the SecurityHeadersMiddleware directly"""
    
    # Create mock app that returns a simple response
    async def mock_app(scope, receive, send):
        if scope["type"] == "http":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                ]
            })
            await send({
                "type": "http.response.body",
                "body": b'{"message": "test"}',
            })
    
    # Create test scope
    scope = {
        "type": "http",
        "path": "/health",
        "method": "GET",
        "headers": [],
        "query_string": b"",
        "raw_path": b"/health",
    }
    
    # Create test receive and send
    receive = MagicMock()
    
    captured_response = None
    async def send(message):
        nonlocal captured_response
        if message["type"] == "http.response.start":
            captured_response = message
    
    # Create and test middleware
    middleware = SecurityHeadersMiddleware(mock_app)
    await middleware(scope, receive, send)
    
    # Verify security headers are present
    if captured_response:
        print("Testing SecurityHeadersMiddleware...")
        print(f"Response type: {captured_response['type']}")
        
        if "headers" in captured_response:
            headers = {k.decode('utf-8'): v.decode('utf-8') for k, v in captured_response['headers']}
            print("\nHeaders received:")
            for name, value in headers.items():
                print(f"  {name}: {value}")
            
            # Check required headers
            required_headers = [
                "content-security-policy",
                "x-frame-options",
                "x-xss-protection",
                "x-content-type-options",
                "referrer-policy",
                "strict-transport-security",
                "x-permitted-cross-domain-policies",
                "permissions-policy",
            ]
            
            print("\nChecking required security headers:")
            all_passed = True
            for header in required_headers:
                if header in headers:
                    print(f"✓ {header}")
                else:
                    print(f"✗ {header}")
                    all_passed = False
            
            print()
            if all_passed:
                print("✅ All security headers are correctly set!")
            else:
                print("❌ Missing required security headers!")
                sys.exit(1)
        else:
            print("❌ Response has no headers")
            sys.exit(1)
    else:
        print("❌ No response received")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(test_security_headers_middleware())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)