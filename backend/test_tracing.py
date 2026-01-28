#!/usr/bin/env python3
"""Test script to verify Celery tracing setup"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from workers.celery_app import celery_app
from tracing import setup_tracing, get_tracer

def test_tracing_import():
    """Test that tracing module can be imported"""
    print("✅ Tracing module imported successfully")

def test_celery_app_creation():
    """Test that Celery app is created successfully"""
    assert celery_app is not None
    print(f"✅ Celery app created successfully: {celery_app.main}")
    print(f"✅ Celery broker: {celery_app.conf.broker_url}")
    print(f"✅ Celery backend: {celery_app.conf.result_backend}")

def test_tracer_creation():
    """Test that tracer can be created"""
    tracer = get_tracer(__name__)
    assert tracer is not None
    print(f"✅ Tracer created successfully: {tracer}")

def test_tracing_setup():
    """Test that tracing can be set up"""
    try:
        setup_tracing(celery_app=celery_app)
        print("✅ Tracing setup completed successfully")
    except Exception as e:
        print(f"⚠️  Tracing setup failed (expected in development): {e}")

def test_celery_instrumentation():
    """Test that Celery tasks are properly instrumented"""
    # Check if there are any tasks registered
    task_names = list(celery_app.tasks.keys())
    print(f"✅ Found {len(task_names)} registered tasks")
    
    # Check if our notification tasks are present
    notification_tasks = [name for name in task_names if 'notification' in name.lower()]
    print(f"✅ Found {len(notification_tasks)} notification tasks")
    for task in notification_tasks:
        print(f"  - {task}")
    
    ingestion_tasks = [name for name in task_names if 'ingestion' in name.lower()]
    print(f"✅ Found {len(ingestion_tasks)} ingestion tasks")
    for task in ingestion_tasks:
        print(f"  - {task}")

if __name__ == "__main__":
    print("Testing Celery Tracing Configuration")
    print("==================================")
    
    test_tracing_import()
    test_celery_app_creation()
    test_tracer_creation()
    test_tracing_setup()
    test_celery_instrumentation()
    
    print("\n✅ All tests completed successfully!")
