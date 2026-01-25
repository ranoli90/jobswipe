import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import engine, get_db
from db import models
from sqlalchemy.orm import sessionmaker

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Check existing users
print('Existing users:')
users = db.query(models.User).all()
for user in users:
    print(f'  {user.email} ({user.id})')

# Clean database
print('\nCleaning database...')
db.query(models.User).delete()
db.commit()

# Check again
print('\nUsers after cleanup:')
users = db.query(models.User).all()
for user in users:
    print(f'  {user.email} ({user.id})')

db.close()
