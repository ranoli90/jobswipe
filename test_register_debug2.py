import sys
import os

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, 'backend'))

from fastapi.testclient import TestClient
from backend.api.main import app

# Try to delete any existing users (since test_register_duplicate_email might be leaving them)
# Since we don't have a delete user endpoint, let's just reset the DB by deleting test.db and initializing again
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

test_data = {'email': 'test@example.com', 'password': '123'}
response = client.post("/v1/auth/register", json=test_data)
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

# Try login now
login_response = client.post("/v1/auth/login", data={'username': test_data['email'], 'password': test_data['password']})
print(f"\nLogin Status Code: {login_response.status_code}")
print(f"Login Response Text: {login_response.text}")
