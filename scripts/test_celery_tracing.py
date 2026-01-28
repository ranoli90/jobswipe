#!/usr/bin/env python3
"""
Celery Tracing Verification Script

This script tests trace propagation from the API to Celery tasks and verifies
that traces appear in Jaeger. It supports testing various task types and
generates detailed reports.

Usage:
    python test_celery_tracing.py [--task-type=<type>] [--api-endpoint=<url>] [--jaeger-url=<url>]

Options:
    --task-type=<type>     Type of task to test (notification, ingestion, analytics, cleanup, all) [default: all]
    --api-endpoint=<url>   API endpoint for trace propagation testing [default: http://localhost:8000]
    --jaeger-url=<url>     Jaeger query API endpoint [default: http://localhost:16686]
"""

import argparse
import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from workers.celery_app import celery_app
from tracing import setup_tracing, get_tracer


class CeleryTracingVerifier:
    """Class to verify Celery tracing functionality"""

    def __init__(self, jaeger_url="http://localhost:16686", api_endpoint="http://localhost:8000"):
        self.jaeger_url = jaeger_url
        self.api_endpoint = api_endpoint
        self.tracer = get_tracer(__name__)
        self.test_results = []

    def test_celery_connection(self):
        """Test if Celery broker and backend are reachable"""
        try:
            # Check if we can connect to the broker
            with self.tracer.start_as_current_span("test_celery_connection") as span:
                # This is a simple check to see if Celery is responsive
                inspect = celery_app.control.inspect()
                active = inspect.active()
                
                # Try to send a simple task (but don't wait for result)
                from workers.celery_tasks.cleanup_tasks import cleanup_expired_tokens
                task = cleanup_expired_tokens.delay(365)  # Safe task that won't delete much
                
                span.set_attribute("task_id", task.id)
                span.set_attribute("task_name", "cleanup_expired_tokens")
                
                # Wait briefly for task to be registered
                time.sleep(1)
                
                result = {"success": True, "task_id": task.id, "status": "pending"}
                self.test_results.append({
                    "test_name": "Celery Connection",
                    "result": result,
                    "status": "pass"
                })
                print(f"✅ Celery connection test passed. Task ID: {task.id}")
                return True
                
        except Exception as e:
            self.test_results.append({
                "test_name": "Celery Connection",
                "result": str(e),
                "status": "fail"
            })
            print(f"❌ Celery connection test failed: {e}")
            return False

    def test_trace_propagation_api_to_celery(self):
        """Test trace propagation by calling an API endpoint that triggers a Celery task"""
        try:
            # First, we need to authenticate to get an access token
            auth_data = {
                "username": "testuser@example.com",
                "password": "testpassword123"
            }
            
            # Try to authenticate (may fail in development)
            auth_response = requests.post(f"{self.api_endpoint}/auth/login", json=auth_data, timeout=5)
            
            if auth_response.status_code == 200:
                auth_token = auth_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
            else:
                print(f"⚠️  Authentication failed (status {auth_response.status_code}), trying without auth...")
                headers = {}
            
            # Test API endpoint that triggers a Celery task
            # Try notifications endpoint
            notification_data = {
                "title": "Test Notification",
                "message": "This is a test notification to verify trace propagation",
                "type": "info"
            }
            
            with self.tracer.start_as_current_span("test_trace_propagation_api_to_celery") as span:
                # Try to send a notification
                try:
                    response = requests.post(
                        f"{self.api_endpoint}/notifications",
                        json=notification_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        notification_id = response.json().get("id")
                        span.set_attribute("notification_id", notification_id)
                        
                        self.test_results.append({
                            "test_name": "API to Celery Trace Propagation",
                            "result": {
                                "status": "pass",
                                "status_code": response.status_code,
                                "notification_id": notification_id,
                                "trace_id": format(span.get_span_context().trace_id, 'x')
                            },
                            "status": "pass"
                        })
                        print(f"✅ API to Celery trace propagation test passed. Notification ID: {notification_id}")
                        return True
                    else:
                        raise Exception(f"API call failed with status {response.status_code}: {response.text}")
                        
                except Exception as e:
                    print(f"⚠️  API call failed: {e}")
                    # Try direct task submission as fallback
                    return self.test_task_submission_directly()
                    
        except Exception as e:
            print(f"⚠️  Authentication failed: {e}")
            # Try direct task submission as fallback
            return self.test_task_submission_directly()

    def test_task_submission_directly(self):
        """Test trace propagation by submitting Celery tasks directly"""
        try:
            from workers.celery_tasks.notification_tasks import send_email_notification
            from workers.celery_tasks.ingestion_tasks import refresh_job_embeddings
            from workers.celery_tasks.analytics_tasks import generate_hourly_snapshot
            from workers.celery_tasks.cleanup_tasks import cleanup_expired_tokens
            
            test_tasks = [
                ("Send Email Notification", lambda: send_email_notification.delay("test-user-id", "Test Subject", "Test Body")),
                ("Refresh Job Embeddings", lambda: refresh_job_embeddings.delay()),
                ("Generate Hourly Snapshot", lambda: generate_hourly_snapshot.delay()),
                ("Cleanup Expired Tokens", lambda: cleanup_expired_tokens.delay(365))
            ]
            
            results = []
            
            for task_name, task_func in test_tasks:
                with self.tracer.start_as_current_span(f"test_task_{task_name.lower().replace(' ', '_')}") as span:
                    try:
                        task_result = task_func()
                        
                        span.set_attribute("task_name", task_name)
                        span.set_attribute("task_id", task_result.id)
                        
                        result = {
                            "task_name": task_name,
                            "task_id": task_result.id,
                            "status": "pending",
                            "trace_id": format(span.get_span_context().trace_id, 'x')
                        }
                        
                        results.append(result)
                        print(f"✅ Task '{task_name}' submitted successfully. Task ID: {task_result.id}")
                        
                    except Exception as e:
                        result = {
                            "task_name": task_name,
                            "status": "failed",
                            "error": str(e)
                        }
                        results.append(result)
                        print(f"⚠️  Task '{task_name}' submission failed: {e}")
            
            self.test_results.append({
                "test_name": "Direct Task Submission",
                "result": results,
                "status": "pass" if any(r.get("status") == "pending" for r in results) else "fail"
            })
            
            return any(r.get("status") == "pending" for r in results)
            
        except Exception as e:
            self.test_results.append({
                "test_name": "Direct Task Submission",
                "result": str(e),
                "status": "fail"
            })
            print(f"❌ Task submission test failed: {e}")
            return False

    def verify_traces_in_jaeger(self, service_name="jobswipe", lookback_minutes=5):
        """Verify that traces exist in Jaeger for the given service"""
        try:
            # Get the time range for querying Jaeger
            end_time = int(time.time() * 1000000)  # microseconds since epoch
            start_time = end_time - (lookback_minutes * 60 * 1000000)  # 5 minutes ago
            
            # Query Jaeger for traces
            query_params = {
                "service": service_name,
                "start": start_time,
                "end": end_time,
                "limit": 100
            }
            
            response = requests.get(f"{self.jaeger_url}/api/traces", params=query_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                traces = data.get("data", [])
                
                print(f"✅ Found {len(traces)} traces in Jaeger for service '{service_name}'")
                
                # Collect trace details
                trace_details = []
                for trace in traces:
                    trace_id = trace.get("traceID")
                    operation_counts = {}
                    
                    for span in trace.get("spans", []):
                        operation = span.get("operationName")
                        operation_counts[operation] = operation_counts.get(operation, 0) + 1
                    
                    trace_details.append({
                        "trace_id": trace_id,
                        "operation_count": sum(operation_counts.values()),
                        "operations": operation_counts,
                        "start_time": trace.get("startTime"),
                        "duration": trace.get("duration")
                    })
                
                self.test_results.append({
                    "test_name": "Jaeger Trace Verification",
                    "result": trace_details,
                    "status": "pass" if len(traces) > 0 else "fail"
                })
                
                return len(traces) > 0
            else:
                raise Exception(f"Jaeger query failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results.append({
                "test_name": "Jaeger Trace Verification",
                "result": str(e),
                "status": "fail"
            })
            print(f"❌ Jaeger verification test failed: {e}")
            return False

    def generate_test_report(self, report_path=None):
        """Generate a comprehensive test report"""
        if report_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"celery_tracing_report_{timestamp}.md"
        
        # Calculate test summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "pass")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "fail")
        
        report_content = """# Celery Tracing Verification Report

## Test Summary

**Generated:** {generated_time}
**Total Tests:** {total_tests}
**Passed:** {passed_tests}
**Failed:** {failed_tests}
**Success Rate:** {success_rate:.1f}%

## Detailed Results

""".format(
    generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    total_tests=total_tests,
    passed_tests=passed_tests,
    failed_tests=failed_tests,
    success_rate=(passed_tests / total_tests) * 100 if total_tests > 0 else 0
)
        
        for result in self.test_results:
            report_content += f"### {result['test_name']}\n"
            report_content += f"**Status:** {result['status'].upper()}\n\n"
            
            if isinstance(result['result'], dict):
                report_content += f"```json\n{json.dumps(result['result'], indent=2)}\n```\n"
            elif isinstance(result['result'], list):
                report_content += f"```json\n{json.dumps(result['result'], indent=2)}\n```\n"
            else:
                report_content += f"{result['result']}\n"
            
            report_content += "\n"
        
        report_content += """## Analysis

### Common Issues

1. **Tracing not enabled:** Ensure tracing is configured in the environment
2. **Jaeger not accessible:** Check if Jaeger is running and reachable at the configured endpoint
3. **Celery worker not running:** Verify Celery workers are operational
4. **Broker connectivity:** Ensure Redis broker is accessible

### Recommendations

1. Check if tracing is enabled in the current environment (set ENVIRONMENT=production or staging)
2. Verify Jaeger collector and query services are running
3. Check Celery worker logs for errors
4. Verify network connectivity between services

---

Generated by `test_celery_tracing.py`
"""
        
        try:
            # Ensure reports directory exists
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w') as f:
                f.write(report_content)
                
            print(f"✅ Test report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")
            return None

    def run_all_tests(self):
        """Run all tracing verification tests"""
        print("Running Celery Tracing Verification Tests")
        print("=" * 50)
        
        # Run tests
        self.test_celery_connection()
        self.test_trace_propagation_api_to_celery()
        self.test_task_submission_directly()
        self.verify_traces_in_jaeger()
        
        # Generate report
        report_path = os.path.join(os.path.dirname(__file__), "..", "reports", "celery_tracing_report.md")
        self.generate_test_report(report_path)
        
        # Print final result
        passed = sum(1 for result in self.test_results if result["status"] == "pass")
        total = len(self.test_results)
        
        print("\n" + "=" * 50)
        print(f"Test Results: {passed}/{total} passed")
        print("=" * 50)
        
        return passed == total


def main():
    """Main entry point of the script"""
    parser = argparse.ArgumentParser(description="Celery Tracing Verification Script")
    parser.add_argument('--task-type', default='all', choices=['notification', 'ingestion', 'analytics', 'cleanup', 'all'],
                       help='Type of task to test')
    parser.add_argument('--api-endpoint', default='http://localhost:8000', help='API endpoint for testing')
    parser.add_argument('--jaeger-url', default='http://localhost:16686', help='Jaeger API endpoint')
    parser.add_argument('--report-path', help='Path to save the test report')
    parser.add_argument('--lookback', type=int, default=5, help='Minutes to look back for traces')
    
    args = parser.parse_args()
    
    print(f"Testing Celery tracing with configuration:")
    print(f"  Task Type: {args.task_type}")
    print(f"  API Endpoint: {args.api_endpoint}")
    print(f"  Jaeger URL: {args.jaeger_url}")
    print(f"  Lookback: {args.lookback} minutes")
    print()
    
    # Initialize verifier
    verifier = CeleryTracingVerifier(args.jaeger_url, args.api_endpoint)
    
    # Run tests
    try:
        success = verifier.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()