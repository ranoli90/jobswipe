
from backend.encryption import encrypt_pii, decrypt_pii

email = "test@example.com"
encrypted = encrypt_pii(email)
print(f"Original: {email}")
print(f"Encrypted: {encrypted}")
decrypted = decrypt_pii(encrypted)
print(f"Decrypted: {decrypted}")
assert decrypted == email, "Encryption/decryption failed!"
