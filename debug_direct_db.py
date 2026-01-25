
from backend.db.database import engine, Base, get_db
from backend.db import models

# Clean the database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Try to create a user directly using SQLAlchemy
db = next(get_db())
try:
    new_user = models.User(email="test@example.com", password_hash="test-hash")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print("User created successfully:", new_user.id, new_user.email)
    
    # Query the user to verify it exists
    user = db.query(models.User).filter(models.User.email == "test@example.com").first()
    print("User from database:", user)
    if user:
        print("User ID:", user.id)
        print("Email:", user.email)
        print("Password hash:", user.password_hash)
        print("Created at:", user.created_at)
        
finally:
    db.close()
