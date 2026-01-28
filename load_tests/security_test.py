#!/usr/bin/env python3
"""
Simple Security Headers Test Script

This script provides a simple way to test security headers on running endpoints.
"""

import sys
import requests

def test_single_endpoint(url):
    """Test security headers on a single endpoint"""
    print(f"\nTesting: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return False
        
        # List of security headers to check
        security_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-XSS-Protection",
            "X-Content-Type-Options",
            "Referrer-Policy"
        ]
        
        print(f"✅ HTTP 200 OK")
        
        all_passed = True
        
        for header in security_headers:
            if header in response.headers:
                print(f"✅ {header}: {response.headers[header]}")
            else:
                print(f"❌ {header}: MISSING")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_tests():
    """Run security headers tests"""
    print("Security Headers Test Suite")
    print("=" * 50)
    
    # Test local endpoint if available
    success_count = 0
    total_tests = 0
    
    # Test 1: Health check endpoint
    print("\n" + "-" * 50)
    print("Test 1: Health Check")
    total_tests += 1
    if test_single_endpoint("http://localhost:8000/health"):
        success_count += 1
    
    # Test 2: Root endpoint
    print("\n" + "-" * 50)
    print("Test 2: Root Endpoint")
    total_tests += 1
    if test_single_endpoint("http://localhost:8000/"):
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
