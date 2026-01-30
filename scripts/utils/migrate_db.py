#!/usr/bin/env python3

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text

from backend.db.database import engine

# Add missing columns
with engine.connect() as conn:
    try:
        # Add salary_range column
        conn.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_range VARCHAR")
        )
        # Add type column
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS type VARCHAR"))
        conn.commit()
        print("Database migration complete")
    except Exception as e:
        print(f"Migration failed: {e}")
        # For SQLite, no IF NOT EXISTS, so try without
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN salary_range VARCHAR"))
            conn.execute(text("ALTER TABLE jobs ADD COLUMN type VARCHAR"))
            conn.commit()
            print("Database migration complete")
        except Exception as e2:
            print(f"Migration failed again: {e2}")
