
from backend.api.routers.auth import verify_password, get_password_hash

# Test password verification
password = "TestPass123!"
hashed_password = get_password_hash(password)
print(f"Password: {password}")
print(f"Hashed password: {hashed_password}")
print(f"Verification result: {verify_password(password, hashed_password)}")

# Test with incorrect password
incorrect_password = "WrongPass123!"
print(f"Verification with incorrect password: {verify_password(incorrect_password, hashed_password)}")
