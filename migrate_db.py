#!/usr/bin/env python3

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy import text

# Connect to SQLite database
engine = create_engine('sqlite:///test.db')

# Add missing columns
with engine.connect() as conn:
    # Add salary_range column
    conn.execute(text("ALTER TABLE jobs ADD COLUMN salary_range VARCHAR"))
    # Add type column
    conn.execute(text("ALTER TABLE jobs ADD COLUMN type VARCHAR"))
    conn.commit()

print("Database migration complete")