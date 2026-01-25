import sys
import os

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, 'backend'))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

test_data = {'email': 'testdebug@example.com', 'password': '123'}
response = client.post("/v1/auth/register", json=test_data)
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
