#!/usr/bin/env python3
"""Debug script to print DATABASE_URL in container"""

import os
import sys
from sqlalchemy import create_engine

print("Debugging DATABASE_URL:")
print("=" * 50)

# Print all relevant environment variables
for var in ["DATABASE_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]:
    value = os.environ.get(var, "NOT SET")
    print(f"{var} = {repr(value)}")

print("=" * 50)
print()

# Try to parse the URL
db_url = os.environ.get("DATABASE_URL")
if db_url:
    print("Testing SQLAlchemy URL parsing:")
    print("=" * 50)
    
    try:
        engine = create_engine(db_url)
        print(f"✅ Success! Engine created: {engine}")
        print(f"  Driver: {engine.driver}")
        print(f"  URL: {repr(db_url)}")
    except Exception as e:
        print(f"❌ Failed to parse URL: {type(e).__name__}: {e}")
        print(f"  URL: {repr(db_url)}")
        import traceback
        print("\nStack trace:")
        traceback.print_exc()
else:
    print("⚠️  DATABASE_URL not found in environment")

print("=" * 50)