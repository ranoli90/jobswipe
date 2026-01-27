import os
import sys

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, "backend"))

from backend.db import models
from backend.db.database import Base, engine, init_db

# Call init_db() again
init_db()

# Reflect tables
metadata = Base.metadata
metadata.reflect(bind=engine)

print("Tables in database:")
for table_name in metadata.tables:
    print("  -", table_name)

print("\nUsers table schema:")
users_table = metadata.tables.get("users")
if users_table:
    for column in users_table.columns:
        print(f"  - {column.name}: {column.type}")
else:
    print("Users table not found")
