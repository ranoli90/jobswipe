#!/usr/bin/env python3
import sys
import os
from unittest.mock import patch

# Add the backend directory to Python path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, '..'))

from backend.db.database import Base
from sqlalchemy.orm.clsregistry import _MultipleClassMarker

# Patch the attempt_get method to print out the contents
original_attempt_get = _MultipleClassMarker.attempt_get

def patched_attempt_get(self, path, key):
    if len(self.contents) > 1:
        print(f"Multiple classes found for {'.'.join(path + [key])}:")
        for cls_ref in self.contents:
            cls = cls_ref()
            if cls is not None:
                print(f"  - {cls.__name__} from module {cls.__module__}")
    return original_attempt_get(self, path, key)

_MultipleClassMarker.attempt_get = patched_attempt_get

# Now run the test
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.db.database import engine, Base

# Clean database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

try:
    response = client.post("/v1/auth/register", json={"email": "test@example.com", "password": "123"})
    print(f"Response: {response}")
    print(f"Response JSON: {response.json()}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
    import traceback
    print(traceback.format_exc())
