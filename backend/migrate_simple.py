#!/usr/bin/env python3
"""Simple migration script that creates tables directly"""

import os
import sys
from sqlalchemy import create_engine, text, Column, String, Boolean, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to database...")

engine = create_engine(database_url)

def create_tables():
    """Create all required tables"""
    with engine.connect() as conn:
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'active',
                role VARCHAR DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_verified BOOLEAN DEFAULT FALSE,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR,
                mfa_backup_codes JSONB,
                lockout_until TIMESTAMP
            )
        """))
        print("✓ Created users table")

        # Create index on email
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)
        """))
        print("✓ Created users email index")

        # Create candidate_profiles table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidate_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                full_name VARCHAR,
                phone VARCHAR,
                location VARCHAR,
                headline VARCHAR,
                work_experience JSONB,
                education JSONB,
                skills JSONB,
                resume_file_url VARCHAR,
                parsed_at TIMESTAMP
            )
        """))
        print("✓ Created candidate_profiles table")

        # Create domains table (required for domain service)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS domains (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                domain VARCHAR UNIQUE NOT NULL,
                company_name VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created domains table")

        # Create jobs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                external_id VARCHAR,
                title VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                location VARCHAR,
                description TEXT,
                url VARCHAR UNIQUE,
                salary_range VARCHAR,
                job_type VARCHAR,
                experience_level VARCHAR,
                skills_required JSONB,
                benefits JSONB,
                application_deadline TIMESTAMP,
                source VARCHAR,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created jobs table")

        # Create indexes for jobs
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_jobs_company ON jobs(company)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs(status)
        """))
        print("✓ Created jobs indexes")

        # Create user_job_interactions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_job_interactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                interaction_type VARCHAR NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, job_id, interaction_type)
            )
        """))
        print("✓ Created user_job_interactions table")

        # Create api_keys table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key_hash VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                permissions JSONB,
                last_used_at TIMESTAMP,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created api_keys table")

        # Create notifications table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                message TEXT,
                data JSONB,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created notifications table")

        # Create notification preferences table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                email_notifications BOOLEAN DEFAULT TRUE,
                push_notifications BOOLEAN DEFAULT TRUE,
                job_matches BOOLEAN DEFAULT TRUE,
                application_updates BOOLEAN DEFAULT TRUE,
                weekly_digest BOOLEAN DEFAULT TRUE,
                marketing BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created user_notification_preferences table")

        # Create analytics_events table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                event_type VARCHAR NOT NULL,
                event_data JSONB,
                session_id VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created analytics_events table")

        # Create resumes table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS resumes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                file_name VARCHAR NOT NULL,
                file_url VARCHAR,
                file_size INTEGER,
                mime_type VARCHAR,
                parsed_data JSONB,
                skills JSONB,
                experience_years INTEGER,
                education JSONB,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created resumes table")

        # Create cover_letters table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cover_letters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL,
                content TEXT,
                variables JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created cover_letters table")

        # Create job_categories table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS job_categories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR UNIQUE NOT NULL,
                description TEXT,
                keywords JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created job_categories table")

        conn.commit()
        print("\n✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()
