#!/usr/bin/env python3
"""Test script to check if the API endpoints are accessible"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from backend.api.main import app

def test_api_endpoints():
    """Test if API endpoints are accessible"""
    print("Testing API endpoints...")
    
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing health endpoint:")
    try:
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test root endpoint
    print("\n2. Testing root endpoint:")
    try:
        response = client.get("/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test API docs
    print("\n3. Testing API docs:")
    try:
        response = client.get("/docs")
        print(f"   Status: {response.status_code}")
        print(f"   Response contains 'FastAPI'? {b'FastAPI' in response.content}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test redoc
    print("\n4. Testing ReDoc:")
    try:
        response = client.get("/redoc")
        print(f"   Status: {response.status_code}")
        print(f"   Response contains 'ReDoc'? {b'ReDoc' in response.content}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test authentication endpoints
    print("\n5. Testing authentication endpoints:")
    print("   Note: These endpoints require valid data")
    
    # Test register (with invalid data to see if endpoint exists)
    try:
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "short"
        })
        print(f"   Register endpoint status: {response.status_code}")
    except Exception as e:
        print(f"   Register endpoint error: {e}")
    
    # Test login (with invalid data to see if endpoint exists)
    try:
        response = client.post("/api/v1/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        print(f"   Login endpoint status: {response.status_code}")
    except Exception as e:
        print(f"   Login endpoint error: {e}")
    
    # Print all available routes
    print("\n6. Available routes:")
    try:
        for route in app.routes:
            if hasattr(route, "path"):
                print(f"   {route.path}")
    except Exception as e:
        print(f"   Error listing routes: {e}")

if __name__ == "__main__":
    test_api_endpoints()
