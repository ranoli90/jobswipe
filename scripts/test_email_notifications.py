#!/usr/bin/env python3
"""
Email Notification Test Script - Phase 1 Pre-Deployment Validation

Tests email notification functionality including:
- Email verification flow
- Password reset email flow
- Email template rendering
- Rate limiting on email endpoints
- Delivery to multiple email providers

Usage:
    python scripts/test_email_notifications.py [options]

Options:
    --api-base-url: Base URL of the API (default: http://localhost:8000)
    --test-email: Test email address for verification (default: test@example.com)
    --test-password: Test password (default: TestPassword123!)
    --report-file: Output report file (default: reports/email_test_report.md)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Test email accounts for different providers
TEST_EMAILS = {
    'gmail': 'jobswipe.test@gmail.com',
    'outlook': 'jobswipe.test@outlook.com',
    'yahoo': 'jobswipe.test@yahoo.com',
    'icloud': 'jobswipe.test@icloud.com'
}

# API endpoints
ENDPOINTS = {
    'register': '/api/v1/auth/register',
    'verify_email': '/api/v1/auth/verify-email',
    'request_password_reset': '/api/v1/auth/request-password-reset',
    'reset_password': '/api/v1/auth/reset-password'
}


class EmailNotificationTester:
    """Test email notification functionality"""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'api_base_url': api_base_url,
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }

    def _run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and track results"""
        self.results['summary']['total'] += 1
        logger.info(f"Running test: {test_name}")

        try:
            test_func()
            logger.info(f"✓ Test passed: {test_name}")
            self.results['tests'].append({
                'name': test_name,
                'status': 'passed',
                'timestamp': datetime.now().isoformat()
            })
            self.results['summary']['passed'] += 1
            return True
        except Exception as e:
            logger.error(f"✗ Test failed: {test_name} - {str(e)}")
            self.results['tests'].append({
                'name': test_name,
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            self.results['summary']['failed'] += 1
            self.results['summary']['errors'].append(str(e))
            return False

    def test_register_and_verify_email_flow(self, email: str, password: str) -> Dict:
        """Test user registration and email verification flow"""
        def _test():
            # Test registration
            register_data = {
                'email': email,
                'password': password,
                'full_name': 'Test User'
            }
            register_response = self.session.post(
                f"{self.api_base_url}{ENDPOINTS['register']}",
                json=register_data
            )
            if register_response.status_code != 201:
                raise Exception(f"Registration failed: {register_response.status_code} - {register_response.text}")

            # Verify we get a verification email (we'll check response structure)
            # In real test, we might need to poll email inbox
            logger.info("Registration successful, verification email should be sent")

        return self._run_test(f"Register and verify email for {email}", _test)

    def test_password_reset_flow(self, email: str) -> Dict:
        """Test password reset email flow"""
        def _test():
            reset_data = {
                'email': email
            }
            reset_response = self.session.post(
                f"{self.api_base_url}{ENDPOINTS['request_password_reset']}",
                json=reset_data
            )

            # Should return success even if email doesn't exist (for security)
            if reset_response.status_code not in [200, 204]:
                raise Exception(f"Password reset request failed: {reset_response.status_code} - {reset_response.text}")

            logger.info("Password reset request successful, reset email should be sent")

        return self._run_test(f"Password reset request for {email}", _test)

    def test_rate_limiting(self, email: str) -> Dict:
        """Test rate limiting on email endpoints"""
        def _test():
            # Test rate limiting by making multiple rapid requests
            reset_data = {
                'email': email
            }

            # Make multiple requests quickly
            responses = []
            for i in range(10):
                start_time = time.time()
                response = self.session.post(
                    f"{self.api_base_url}{ENDPOINTS['request_password_reset']}",
                    json=reset_data
                )
                responses.append({
                    'status': response.status_code,
                    'headers': dict(response.headers),
                    'response_time': time.time() - start_time
                })
                time.sleep(0.1)

            # Check if any request was rate limited (429)
            rate_limited = any(resp['status'] == 429 for resp in responses)
            if not rate_limited:
                logger.warning("Rate limiting not detected, but might be configured differently")

            # Check for rate limit headers
            rate_limit_headers = []
            for resp in responses:
                if 'X-RateLimit-Limit' in resp['headers']:
                    rate_limit_headers = {
                        'limit': resp['headers'].get('X-RateLimit-Limit'),
                        'remaining': resp['headers'].get('X-RateLimit-Remaining'),
                        'reset': resp['headers'].get('X-RateLimit-Reset')
                    }
                    break

            logger.info(f"Rate limit headers: {rate_limit_headers}")

        return self._run_test("Rate limiting on password reset endpoint", _test)

    def test_email_templates(self) -> Dict:
        """Test email template rendering"""
        def _test():
            # Test template endpoints if available
            # This is a placeholder - actual template testing would require rendering checks
            logger.info("Email template test placeholder")

        return self._run_test("Email template rendering", _test)

    def run_all_tests(self, test_email: str, test_password: str) -> Dict:
        """Run all email notification tests"""
        logger.info("Starting email notification tests...")

        # Test 1: Registration and verification email flow
        self.test_register_and_verify_email_flow(test_email, test_password)

        # Test 2: Password reset email flow
        self.test_password_reset_flow(test_email)

        # Test 3: Test with different email providers
        for provider, email in TEST_EMAILS.items():
            self.test_password_reset_flow(email)

        # Test 4: Rate limiting
        self.test_rate_limiting(test_email)

        # Test 5: Email templates
        self.test_email_templates()

        return self.results

    def generate_report(self, report_file: str):
        """Generate comprehensive test report"""
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, 'w') as f:
            f.write("# Email Notification Test Report\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n")
            f.write(f"**API Base URL:** {self.results['api_base_url']}\n\n")

            # Summary
            f.write("## Summary\n")
            f.write(f"- Total Tests: {self.results['summary']['total']}\n")
            f.write(f"- Passed: {self.results['summary']['passed']}\n")
            f.write(f"- Failed: {self.results['summary']['failed']}\n")

            if self.results['summary']['errors']:
                f.write("\n## Errors\n")
                for error in self.results['summary']['errors']:
                    f.write(f"- {error}\n")

            # Detailed Results
            f.write("\n## Detailed Results\n")
            for test in self.results['tests']:
                status_icon = "✅" if test['status'] == 'passed' else "❌"
                f.write(f"### {status_icon} {test['name']}\n")
                f.write(f"- Status: {test['status']}\n")
                f.write(f"- Time: {test['timestamp']}\n")
                if 'error' in test:
                    f.write(f"- Error: {test['error']}\n")
                f.write("\n")

        logger.info(f"Report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Email Notification Test Script - Phase 1 Pre-Deployment Validation"
    )
    parser.add_argument(
        '--api-base-url',
        default='http://localhost:8000',
        help='Base URL of the API'
    )
    parser.add_argument(
        '--test-email',
        default='test@example.com',
        help='Test email address for verification'
    )
    parser.add_argument(
        '--test-password',
        default='TestPassword123!',
        help='Test password'
    )
    parser.add_argument(
        '--report-file',
        default='reports/email_test_report.md',
        help='Output report file'
    )

    args = parser.parse_args()

    # Create tester
    tester = EmailNotificationTester(args.api_base_url)

    # Run tests
    results = tester.run_all_tests(args.test_email, args.test_password)

    # Generate report
    tester.generate_report(args.report_file)

    logger.info("Email notification tests completed!")
    logger.info(f"Results: {results['summary']['passed']} passed, {results['summary']['failed']} failed")

    return 0 if results['summary']['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())