#!/usr/bin/env python3
"""Test script to verify the constants I've defined in the codebase."""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

def test_job_ingestion_service_constants():
    """Test job_ingestion_service.py constants."""
    from services.job_ingestion_service import JOB_TYPES
    assert len(JOB_TYPES) > 0
    assert "Software Engineer" in JOB_TYPES
    assert "Data Scientist" in JOB_TYPES
    assert "Product Manager" in JOB_TYPES
    assert "Designer" in JOB_TYPES
    print("✅ Job ingestion service constants tested successfully")

def test_api_keys_constants():
    """Test api_keys.py constants."""
    from api.routers.api_keys import VALID_SERVICE_TYPES
    from services.api_key_service import VALID_SERVICE_TYPES as SERVICE_VALID_TYPES
    
    assert VALID_SERVICE_TYPES == SERVICE_VALID_TYPES
    assert len(VALID_SERVICE_TYPES) == 4
    assert "ingestion" in VALID_SERVICE_TYPES
    assert "automation" in VALID_SERVICE_TYPES
    assert "analytics" in VALID_SERVICE_TYPES
    assert "webhook" in VALID_SERVICE_TYPES
    print("✅ API keys constants tested successfully")

def test_notification_service_constants():
    """Test notification_service.py constants."""
    from services.notification_service import NotificationService
    assert hasattr(NotificationService, 'NOTIFICATION_TITLES')
    assert len(NotificationService.NOTIFICATION_TITLES) > 0
    assert "application_submitted" in NotificationService.NOTIFICATION_TITLES
    assert "job_match_found" in NotificationService.NOTIFICATION_TITLES
    print("✅ Notification service constants tested successfully")

def test_cover_letter_service_constants():
    """Test cover_letter_service.py constants."""
    from services.cover_letter_service import (
        MAX_SKILLS_TO_INCLUDE,
        MAX_EXPERIENCE_ENTRIES,
        MAX_WORDS,
        MAX_CHARACTERS,
        TRUNCATION_SUFFIX,
        TRUNCATED_CHARACTER_LIMIT,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS
    )
    assert MAX_SKILLS_TO_INCLUDE == 8
    assert MAX_EXPERIENCE_ENTRIES == 3
    assert MAX_WORDS == 180
    assert MAX_CHARACTERS == 1500
    assert TRUNCATION_SUFFIX == "..."
    assert TRUNCATED_CHARACTER_LIMIT == 1497
    assert LLM_TEMPERATURE == 0.3
    assert LLM_MAX_TOKENS == 300
    print("✅ Cover letter service constants tested successfully")

def test_cleanup_tasks_constants():
    """Test cleanup_tasks.py constants."""
    from workers.celery_tasks.cleanup_tasks import (
        DEFAULT_EXPIRED_TOKENS_DAYS,
        DEFAULT_OLD_SESSIONS_DAYS,
        DEFAULT_EXPIRED_OAUTH_STATES_HOURS,
        DEFAULT_OLD_INTERACTIONS_DAYS,
        DEFAULT_ORPHAN_NOTIFICATIONS_DAYS,
        DEFAULT_TEMP_FILES_HOURS,
        TEMPORARY_DIRECTORIES,
        MAX_INTERACTIONS_TO_ARCHIVE,
        CELERY_TASK_TIMEOUT
    )
    assert DEFAULT_EXPIRED_TOKENS_DAYS == 1
    assert DEFAULT_OLD_SESSIONS_DAYS == 7
    assert DEFAULT_EXPIRED_OAUTH_STATES_HOURS == 1
    assert DEFAULT_OLD_INTERACTIONS_DAYS == 90
    assert DEFAULT_ORPHAN_NOTIFICATIONS_DAYS == 30
    assert DEFAULT_TEMP_FILES_HOURS == 24
    assert len(TEMPORARY_DIRECTORIES) == 3
    assert "/tmp/reports" in TEMPORARY_DIRECTORIES
    assert "/tmp/uploads" in TEMPORARY_DIRECTORIES
    assert "/tmp/cache" in TEMPORARY_DIRECTORIES
    assert MAX_INTERACTIONS_TO_ARCHIVE == 10000
    assert CELERY_TASK_TIMEOUT == 60
    print("✅ Cleanup tasks constants tested successfully")

if __name__ == "__main__":
    print("Testing constants in jobswipe codebase...")
    test_job_ingestion_service_constants()
    test_api_keys_constants()
    test_notification_service_constants()
    test_cover_letter_service_constants()
    test_cleanup_tasks_constants()
    print("\n✅ All constants tested successfully!")
