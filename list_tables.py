import sys
import os
import sqlite3

SORCE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, SORCE_DIR)
sys.path.insert(0, os.path.join(SORCE_DIR, 'backend'))

from backend.db.database import engine, init_db

# Call init_db() again
init_db()

conn = sqlite3.connect(os.path.join(SORCE_DIR, 'test.db'))
cursor = conn.cursor()

print("Tables in test.db:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print("  -", table[0])

print("\nUsers table schema:")
try:
    cursor.execute("PRAGMA table_info(users);")
    print(cursor.fetchall())
except Exception as e:
    print(f"Error: {e}")

conn.close()
