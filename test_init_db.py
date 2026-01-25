import sys
import os

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, 'backend'))

from backend.db.database import engine, init_db
from backend.db import models

TEST_DB_PATH = os.path.join(SORCE_DIR, 'test.db')
try:
    os.remove(TEST_DB_PATH)
    print("Deleted test.db")
except:
    print("test.db does not exist")

print("Calling init_db")
init_db()

print("\nEngine URL", engine.url)
print("\nModel metadata tables:", list(models.Base.metadata.tables.keys()))
