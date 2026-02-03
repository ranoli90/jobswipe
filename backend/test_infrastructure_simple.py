#!/usr/bin/env python3
"""
Simple test script to verify infrastructure tests without requiring full context
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def test_backup_manager_import():
    """Test that backup manager module can be imported"""
    print("\nTesting backup manager import...")

    try:
        print("✓ Backup manager imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import backup manager: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_dynamic_rate_limiter_import():
    """Test that dynamic rate limiter module can be imported"""
    print("\nTesting dynamic rate limiter import...")

    try:
        print("✓ DynamicRateLimiter imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import DynamicRateLimiter: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_metrics_collector_import():
    """Test that metrics collector module can be imported"""
    print("\nTesting metrics collector import...")

    try:
        print("✓ MetricsCollector imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import MetricsCollector: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_prometheus_metrics_import():
    """Test that metrics module can be imported"""
    print("\nTesting metrics module import...")

    try:
        print("✓ Metrics module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import metrics module: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def run_basic_import_tests():
    """Run all basic import tests"""
    print("=" * 50)
    print("JobSwipe Infrastructure Tests - Basic Import Tests")
    print("=" * 50)

    tests = [
        ("backup_manager", test_backup_manager_import),
        ("dynamic_rate_limiter", test_dynamic_rate_limiter_import),
        ("metrics_collector", test_metrics_collector_import),
        ("prometheus_metrics", test_prometheus_metrics_import)
    ]

    all_passed = True
    for name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"\n❌ Error running {name} test: {str(e)}")
            import traceback
            print(traceback.format_exc())
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL BASIC IMPORT TESTS PASSED")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_basic_import_tests()
    sys.exit(0 if success else 1)
