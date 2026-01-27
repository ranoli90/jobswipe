#!/usr/bin/env python3

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.db import models
from backend.db.database import Base, engine

# Reflect existing tables
metadata = Base.metadata
metadata.reflect(bind=engine)

# Get jobs table
jobs_table = metadata.tables.get("jobs")
if jobs_table:
    print("Jobs table columns:")
    for column in jobs_table.columns:
        print(f"- {column.name} ({column.type})")
else:
    print("Jobs table not found")
