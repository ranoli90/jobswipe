import sys
import os

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, 'backend'))

from fastapi.testclient import TestClient
from backend.api.main import app

# Clean up test db
TEST_DB_PATH = os.path.join(SORCE_DIR, 'test.db')
try:
    os.remove(TEST_DB_PATH)
    print("Deleted existing test.db at", TEST_DB_PATH)
except FileNotFoundError:
    print("test.db not found, will create new one")
    pass

# Initialize database
from backend.db.database import init_db
init_db()

client = TestClient(app)

test_data = {'email': 'duplicate@example.com', 'password': 'test123'}

# First registration - should pass
response1 = client.post("/v1/auth/register", json=test_data)
print(f"First registration: {response1.status_code} - {response1.text}")

# Second registration with same email - should fail
response2 = client.post("/v1/auth/register", json=test_data)
print(f"Second registration: {response2.status_code} - {response2.text}")
