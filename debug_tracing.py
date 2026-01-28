#!/usr/bin/env python3
"""
Simple debugging script to verify the tracing module importability and basic functionality.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

def test_tracing_import():
    """Test that the tracing module can be imported"""
    try:
        from tracing import setup_tracing, get_tracer
        print("✅ Tracing module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import tracing module: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tracer_creation():
    """Test that we can create a tracer instance"""
    try:
        from tracing import get_tracer
        tracer = get_tracer(__name__)
        print(f"✅ Tracer created successfully: {tracer}")
        return True
    except Exception as e:
        print(f"❌ Failed to create tracer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tracing_setup():
    """Test that tracing setup works (will skip in development)"""
    try:
        from tracing import setup_tracing
        setup_tracing()
        print("✅ Tracing setup completed (may have been skipped in development)")
        return True
    except Exception as e:
        print(f"❌ Failed to setup tracing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tracing_config():
    """Test configuration detection"""
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"ℹ️  Current environment: {environment}")
    print(f"ℹ️  Tracing enabled in: ['production', 'staging']")
    
    if environment in ["production", "staging"]:
        print("✅ Tracing should be enabled")
    else:
        print("ℹ️  Tracing will be disabled (enable with ENVIRONMENT=staging)")
    
    return True

def test_otel_imports():
    """Test that OpenTelemetry modules are available"""
    try:
        import opentelemetry
        import opentelemetry.trace
        import opentelemetry.instrumentation.celery
        import opentelemetry.exporter.jaeger.thrift
        import opentelemetry.sdk.trace
        
        print("✅ OpenTelemetry modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ OpenTelemetry module not available: {e}")
        return False

def test_celery_import():
    """Test that Celery is available"""
    try:
        from celery import Celery
        print(f"✅ Celery module available: {Celery}")
        return True
    except Exception as e:
        print(f"❌ Celery module not available: {e}")
        return False

def test_celery_app_import():
    """Test that celery_app can be imported"""
    try:
        from workers.celery_app import celery_app
        print(f"✅ Celery app imported successfully")
        print(f"ℹ️  Celery broker: {celery_app.conf.broker_url}")
        print(f"ℹ️  Celery backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("JobSwipe Tracing Debug Script")
    print("=" * 50)
    
    tests = [
        ("Tracing module import", test_tracing_import),
        ("Tracer creation", test_tracer_creation), 
        ("Tracing setup", test_tracing_setup),
        ("Configuration detection", test_tracing_config),
        ("OpenTelemetry imports", test_otel_imports),
        ("Celery import", test_celery_import),
        ("Celery app import", test_celery_app_import),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"{'✅' if success else '❌'} {test_name} {'passed' if success else 'failed'}")
        except Exception as e:
            print(f"❌ Error in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for name, result in results if result)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total:.1%}")
    
    failures = [name for name, result in results if not result]
    if failures:
        print("\nFailed tests:")
        for name in failures:
            print(f"  - {name}")
    
    if passed == total:
        print("\n🎉 All tests passed! Tracing system is ready.")
        print("\nNext steps:")
        print("1. Start Jaeger service: docker start jobswipe-jaeger")
        print("2. Start Celery worker with tracing enabled:")
        print("   export ENVIRONMENT=staging")
        print("   celery -A backend.workers.celery_app worker --loglevel=info")
        print("3. Run full test suite: python scripts/test_celery_tracing.py")
        print("4. Check Jaeger UI: http://localhost:16686")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())