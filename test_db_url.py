#!/usr/bin/env python3
"""Test script to verify SQLAlchemy URL parsing"""

from sqlalchemy import create_engine
import os
import sys

def test_url(url):
    try:
        engine = create_engine(url)
        print(f"✅ URL parsing successful: {url}")
        print(f"  Driver: {engine.driver}")
        return True
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        print(f"  URL: {repr(url)}")
        return False

# Test cases
if __name__ == "__main__":
    print("Testing SQLAlchemy URL parsing...")
    print("=" * 50)
    
    # Test standard URL formats
    test_url("sqlite:///./test.db")
    test_url("postgresql://user:password@localhost:5432/dbname")
    test_url("postgresql+psycopg2://user:password@localhost:5432/dbname")
    
    print("=" * 50)
    
    # Check if we have DATABASE_URL in environment
    if "DATABASE_URL" in os.environ:
        print("Testing DATABASE_URL from environment...")
        db_url = os.environ["DATABASE_URL"]
        test_url(db_url)
    else:
        print("⚠️  DATABASE_URL not found in environment variables")
        print("  Run with: DATABASE_URL='your-url' python test_db_url.py")

print("\nDone.")