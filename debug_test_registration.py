
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.db.database import engine, Base
from backend.db import models

# Clean the test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Test user data
user_data = {"email": "test@example.com", "password": "TestPass123!"}

# Register a user
print("Registering user...")
response = client.post("/v1/auth/register", json=user_data)
print(f"Register response status: {response.status_code}")
print(f"Register response body: {response.json()}")

# Check if user exists in the database
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
print(f"\nUser in database: {user}")
if user:
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Password hash: {user.password_hash}")
    print(f"Created at: {user.created_at}")
db.close()
