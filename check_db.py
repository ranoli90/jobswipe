#!/usr/bin/env python3

from sqlalchemy import create_engine, MetaData

# Connect to SQLite database
engine = create_engine('sqlite:///test.db')
metadata = MetaData()

# Reflect existing tables
metadata.reflect(bind=engine)

# Get jobs table
jobs_table = metadata.tables['jobs']

print("Jobs table columns:")
for column in jobs_table.columns:
    print(f"- {column.name} ({column.type})")