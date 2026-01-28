"""
Security Headers Tests

Tests for the SecurityHeadersMiddleware to verify all security headers are properly set.
"""

import pytest
from fastapi.testclient import TestClient


def test_security_headers(client: TestClient):
    """Test that all security headers are present on HTTP responses"""
    
    # Make a test request to a public endpoint
    response = client.get("/health")
    
    assert response.status_code == 200
    
    # Check all required security headers
    assert "content-security-policy" in response.headers
    assert "x-frame-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "x-content-type-options" in response.headers
    assert "referrer-policy" in response.headers
    
    # Verify header values
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    
    # Verify Content Security Policy has basic directives
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "img-src 'self'" in csp
    assert "font-src 'self'" in csp


def test_security_headers_on_error(client: TestClient):
    """Test that security headers are present on error responses"""
    
    # Make a request to a non-existent endpoint to trigger 404
    response = client.get("/v1/non-existent-endpoint")
    
    assert response.status_code == 404
    
    # Check all required security headers are still present
    assert "x-frame-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "x-content-type-options" in response.headers
    assert "referrer-policy" in response.headers
    assert "content-security-policy" in response.headers