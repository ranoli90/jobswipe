"""
Simple Security Headers Test

A minimal test script to directly test the SecurityHeadersMiddleware without
requiring all the app dependencies.
"""

import sys
import asyncio
from unittest.mock import MagicMock

# Add the backend directory to Python path
sys.path.insert(0, '/home/brooketogo98/jobswipe/backend')

from api.main import SecurityHeadersMiddleware


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