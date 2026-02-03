#!/usr/bin/env python3
"""
Security Headers Validation Script

This script tests security headers on the JobSwipe API endpoints
and generates a comprehensive report of findings.
"""

import requests
import json
import csv
from datetime import datetime
import argparse
import sys
from typing import Dict, List, Tuple

# Configuration
STAGING_BASE_URL = "https://api.staging.jobswipe.app"
DEVELOPMENT_BASE_URL = "http://localhost:8000"
PRODUCTION_BASE_URL = "https://api.jobswipe.app"

# Security headers to check
REQUIRED_HEADERS = {
    "Content-Security-Policy": {
        "required": True,
        "description": "Content Security Policy to prevent XSS and data injection attacks",
        "expected": "default-src 'self'"
    },
    "X-Frame-Options": {
        "required": True,
        "description": "Prevents clickjacking attacks",
        "expected": "DENY"
    },
    "X-XSS-Protection": {
        "required": True,
        "description": "Enables browser XSS protection",
        "expected": "1; mode=block"
    },
    "X-Content-Type-Options": {
        "required": True,
        "description": "Prevents MIME type sniffing",
        "expected": "nosniff"
    },
    "Referrer-Policy": {
        "required": True,
        "description": "Controls referrer information",
        "expected": "strict-origin-when-cross-origin"
    },
    "Strict-Transport-Security": {
        "required": False,
        "description": "Enforces HTTPS connection",
        "expected": "max-age=31536000"
    },
    "X-Permitted-Cross-Domain-Policies": {
        "required": False,
        "description": "Controls Adobe Flash cross-domain policies",
        "expected": "none"
    },
    "Permissions-Policy": {
        "required": False,
        "description": "Controls browser permissions",
        "expected": None
    }
}

# Endpoints to test (from API documentation)
ENDPOINTS = [
    # Authentication endpoints
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/me",
    
    # Jobs endpoints
    "/api/v1/jobs",
    "/api/v1/jobs/matches",
    
    # Profile endpoints
    "/api/v1/profile",
    "/api/v1/profile/resume",
    
    # Applications endpoints
    "/api/v1/applications",
    
    # Health check
    "/health"
]

class SecurityHeadersValidator:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
    
    def test_endpoint(self, endpoint: str, method: str = "GET") -> Dict:
        """Test security headers for a specific endpoint"""
        url = f"{self.base_url}{endpoint}"
        result = {
            "endpoint": endpoint,
            "method": method,
            "url": url,
            "status_code": None,
            "headers_received": {},
            "headers_expected": {},
            "missing_headers": [],
            "mismatched_headers": [],
            "errors": []
        }
        
        try:
            if method == "GET":
                response = self.session.get(url, timeout=10)
            elif method == "POST":
                # For POST endpoints, send minimal valid data or empty body
                response = self.session.post(url, json={}, timeout=10)
            else:
                response = self.session.request(method, url, timeout=10)
            
            result["status_code"] = response.status_code
            
            # Check security headers
            for header_name, config in REQUIRED_HEADERS.items():
                header_lower = header_name.lower()
                if header_lower in [h.lower() for h in response.headers]:
                    received_value = response.headers.get(header_lower)
                    result["headers_received"][header_name] = received_value
                    
                    # Check if header value matches expected
                    if config["expected"] and config["expected"] not in received_value:
                        result["mismatched_headers"].append({
                            "name": header_name,
                            "expected": config["expected"],
                            "received": received_value
                        })
                else:
                    if config["required"]:
                        result["missing_headers"].append(header_name)
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run tests on all configured endpoints"""
        print("Testing security headers on %s" % self.base_url)
        print("=" * 80)
        
        for endpoint in ENDPOINTS:
            print("\nTesting: %s" % endpoint)
            
            # Test with GET method
            result = self.test_endpoint(endpoint, "GET")
            self.results.append(result)
            
            # For endpoints that should support POST
            if endpoint in ["/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/applications"]:
                post_result = self.test_endpoint(endpoint, "POST")
                self.results.append(post_result)
        
        return self.results
    
    def generate_report(self, output_file: str = "security_headers_report"):
        """Generate comprehensive reports"""
        self._generate_markdown_report(output_file + ".md")
        self._generate_csv_report(output_file + ".csv")
        self._print_summary()
    
    def _print_summary(self):
        """Print a summary of the results"""
        total_tests = len(self.results)
        passing_tests = 0
        total_missing = 0
        total_mismatched = 0
        
        for result in self.results:
            if not result["missing_headers"] and not result["mismatched_headers"] and not result["errors"]:
                passing_tests += 1
            
            total_missing += len(result["missing_headers"])
            total_mismatched += len(result["mismatched_headers"])
        
        print("\n" + "=" * 80)
        print("Test Summary:")
        print("Total endpoints tested: %d" % total_tests)
        print("Passing tests: %d" % passing_tests)
        print("Failing tests: %d" % (total_tests - passing_tests))
        print("Missing headers: %d" % total_missing)
        print("Mismatched headers: %d" % total_mismatched)
        print("=" * 80)
    
    def _generate_markdown_report(self, filename: str):
        """Generate Markdown report"""
        with open(filename, "w") as f:
            f.write("# Security Headers Validation Report\n\n")
            f.write("**Generated:** %s\n" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            f.write("**Target:** %s\n\n" % self.base_url)
            
            f.write("## Summary\n\n")
            f.write("- Total endpoints tested: %d\n" % len(self.results))
            f.write("- Endpoints with missing headers: %d\n" % sum(1 for r in self.results if r['missing_headers']))
            f.write("- Endpoints with mismatched headers: %d\n" % sum(1 for r in self.results if r['mismatched_headers']))
            f.write("- Endpoints with errors: %d\n\n" % sum(1 for r in self.results if r['errors']))
            
            f.write("## Detailed Results\n\n")
            
            for result in self.results:
                f.write("### %s %s\n\n" % (result['method'], result['endpoint']))
                
                if result['errors']:
                    f.write("**Errors:**\n")
                    for error in result['errors']:
                        f.write("- %s\n" % error)
                    f.write("\n")
                    continue
                
                f.write("**Status Code:** %s\n\n" % result['status_code'])
                
                if result['missing_headers']:
                    f.write("**Missing Headers:**\n")
                    for header in result['missing_headers']:
                        f.write("- %s\n" % header)
                    f.write("\n")
                
                if result['mismatched_headers']:
                    f.write("**Mismatched Headers:**\n")
                    for header in result['mismatched_headers']:
                        f.write("- %s: expected '%s', received '%s'\n" % (header['name'], header['expected'], header['received']))
                    f.write("\n")
                
                f.write("**Headers Received:**\n")
                for header_name, value in result['headers_received'].items():
                    f.write("- %s: %s\n" % (header_name, value))
                f.write("\n")
                f.write("---\n\n")
    
    def _generate_csv_report(self, filename: str):
        """Generate CSV report for spreadsheets"""
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Endpoint",
                "Method",
                "Status Code",
                "Missing Headers",
                "Mismatched Headers",
                "Errors"
            ])
            
            for result in self.results:
                writer.writerow([
                    result['endpoint'],
                    result['method'],
                    result['status_code'],
                    " | ".join(result['missing_headers']),
                    " | ".join(["%s: %s != %s" % (h['name'], h['expected'], h['received']) for h in result['mismatched_headers']]),
                    " | ".join(result['errors'])
                ])

def main():
    parser = argparse.ArgumentParser(
        description="Security Headers Validation Script for JobSwipe API"
    )
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="staging",
        help="Target environment to test (default: staging)"
    )
    parser.add_argument(
        "--output", "-o",
        default="reports/security_headers_report",
        help="Output file prefix for reports (default: reports/security_headers_report)"
    )
    
    args = parser.parse_args()
    
    # Determine target URL
    if args.environment == "development":
        base_url = DEVELOPMENT_BASE_URL
    elif args.environment == "staging":
        base_url = STAGING_BASE_URL
    elif args.environment == "production":
        base_url = PRODUCTION_BASE_URL
    
    # Run validation
    validator = SecurityHeadersValidator(base_url)
    results = validator.run_all_tests()
    validator.generate_report(args.output)
    
    # Return appropriate exit code based on results
    has_failures = any(r['missing_headers'] or r['mismatched_headers'] or r['errors'] 
                       for r in results)
    
    if has_failures:
        print("\n❌ Security headers validation failed - please fix the issues.")
        sys.exit(1)
    else:
        print("\n✅ All security headers are properly configured.")
        sys.exit(0)

if __name__ == "__main__":
    main()
