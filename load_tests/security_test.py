#!/usr/bin/env python3
"""
Simple Security Headers and Vulnerability Test Script

This script provides a simple way to test security headers and basic vulnerabilities on running endpoints.
"""

import sys
import requests
import os

# A simple payload for injection testing
INJECTION_PAYLOAD = "' OR 1=1; --"


def test_single_endpoint(base_url, endpoint, headers={}):
    """Test security headers on a single endpoint"""
    url = f"{base_url}{endpoint}"
    print(f"\nTesting: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # List of security headers to check with expected values (None means just check for presence)
        security_headers = {
            "Content-Security-Policy": None,
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": ["1; mode=block"],
            "X-Content-Type-Options": ["nosniff"],
            "Referrer-Policy": ["no-referrer", "strict-origin-when-cross-origin"],
            "Strict-Transport-Security": None # Often present, especially in prod
        }
        
        print(f"✅ HTTP {response.status_code}")
        
        all_passed = True
        
        for header, expected_values in security_headers.items():
            if header in response.headers:
                header_value = response.headers[header]
                if expected_values and header_value not in expected_values:
                    print(f"❌ {header}: {header_value} (Expected one of: {expected_values})")
                    all_passed = False
                else:
                    print(f"✅ {header}: {header_value}")
            else:
                print(f"❌ {header}: MISSING")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sql_injection(base_url, endpoint, headers={}):
    """Test for basic SQL injection vulnerabilities"""
    url = f"{base_url}{endpoint}{INJECTION_PAYLOAD}"
    print(f"\nTesting SQL Injection: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code >= 500:
            print(f"❌ SQL Injection Test Failed: Server returned {response.status_code}")
            return False
        elif "SQL" in response.text.upper() or "SYNTAX" in response.text.upper():
             print(f"❌ SQL Injection Test Failed: Possible SQL error in response body.")
             return False
        else:
            print("✅ SQL Injection Test Passed")
            return True
            
    except Exception as e:
        print(f"❌ Error during SQL Injection test: {e}")
        return False

def run_tests():
    """Run security tests"""
    print("Security Test Suite")
    print("=" * 50)

    base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    api_key = os.environ.get("API_KEY")

    auth_headers = {}
    if api_key:
        auth_headers["X-API-Key"] = api_key
    
    endpoints_to_test = ["/health", "/", "/api/v1/jobs/feed"]
    injection_endpoints = ["/api/v1/jobs/"] # Example endpoint that takes an ID

    success_count = 0
    total_tests = 0
    
    for endpoint in endpoints_to_test:
        total_tests += 1
        if test_single_endpoint(base_url, endpoint, headers=auth_headers):
            success_count += 1

    for endpoint in injection_endpoints:
        total_tests += 1
        if test_sql_injection(base_url, endpoint, headers=auth_headers):
            success_count += 1

    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
