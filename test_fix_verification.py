#!/usr/bin/env python3
"""Test script to verify the constants and fixes I've implemented.
This script doesn't require a full environment setup.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

def test_job_ingestion_service():
    """Test job_ingestion_service.py constants."""
    print("Testing job_ingestion_service.py...")
    try:
        from services.job_ingestion_service import JOB_TYPES
        assert len(JOB_TYPES) > 0
        assert "Software Engineer" in JOB_TYPES
        assert "Data Scientist" in JOB_TYPES
        assert "Product Manager" in JOB_TYPES
        assert "Designer" in JOB_TYPES
        print("✅ JOB_TYPES constant is defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_file_validation():
    """Test file_validation.py constants."""
    print("\nTesting file_validation.py...")
    try:
        from api.middleware.file_validation import (
            RESUME_ALLOWED_EXTENSIONS,
            RESUME_ALLOWED_TYPES,
            RESUME_MAX_SIZE
        )
        assert len(RESUME_ALLOWED_EXTENSIONS) > 0
        assert ".pdf" in RESUME_ALLOWED_EXTENSIONS
        assert len(RESUME_ALLOWED_TYPES) > 0
        assert "application/pdf" in RESUME_ALLOWED_TYPES
        assert RESUME_MAX_SIZE == 5 * 1024 * 1024  # 5MB
        print("✅ File validation constants are defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_api_keys():
    """Test api_keys.py constants."""
    print("\nTesting api_keys.py...")
    try:
        from api.routers.api_keys import VALID_SERVICE_TYPES
        from services.api_key_service import VALID_SERVICE_TYPES as SERVICE_VALID_TYPES
        
        assert VALID_SERVICE_TYPES == SERVICE_VALID_TYPES
        assert len(VALID_SERVICE_TYPES) == 4
        assert "ingestion" in VALID_SERVICE_TYPES
        assert "automation" in VALID_SERVICE_TYPES
        assert "analytics" in VALID_SERVICE_TYPES
        assert "webhook" in VALID_SERVICE_TYPES
        print("✅ VALID_SERVICE_TYPES constant is defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_notification_service():
    """Test notification_service.py constants."""
    print("\nTesting notification_service.py...")
    try:
        from services.notification_service import NotificationService
        assert hasattr(NotificationService, 'NOTIFICATION_TITLES')
        assert len(NotificationService.NOTIFICATION_TITLES) > 0
        assert "application_submitted" in NotificationService.NOTIFICATION_TITLES
        assert "job_match_found" in NotificationService.NOTIFICATION_TITLES
        print("✅ NOTIFICATION_TITLES constant is defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_cover_letter_service():
    """Test cover_letter_service.py constants."""
    print("\nTesting cover_letter_service.py...")
    try:
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
        print("✅ Cover letter generation constants are defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_cleanup_tasks():
    """Test cleanup_tasks.py constants."""
    print("\nTesting cleanup_tasks.py...")
    try:
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
        assert len(TEMPORARY_DIRECTORIES) > 0
        assert MAX_INTERACTIONS_TO_ARCHIVE == 10000
        assert CELERY_TASK_TIMEOUT == 60
        print("✅ Cleanup task constants are defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_domain_service():
    """Test domain_service.py constants."""
    print("\nTesting domain_service.py...")
    try:
        from services.domain_service import DomainRateLimiter
        assert hasattr(DomainRateLimiter, 'DEFAULT_RPM')
        assert hasattr(DomainRateLimiter, 'DEFAULT_RPH')
        assert hasattr(DomainRateLimiter, 'DEFAULT_RPD')
        assert hasattr(DomainRateLimiter, 'DEFAULT_CONCURRENCY')
        assert hasattr(DomainRateLimiter, 'MINUTE')
        assert hasattr(DomainRateLimiter, 'HOUR')
        assert hasattr(DomainRateLimiter, 'DAY')
        print("✅ Domain service constants are defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_input_sanitization():
    """Test input_sanitization.py constants."""
    print("\nTesting input_sanitization.py...")
    try:
        from api.middleware.input_sanitization import (
            InputSanitizationMiddleware
        )
        assert hasattr(InputSanitizationMiddleware, 'DEFAULT_MAX_FILE_SIZE')
        assert hasattr(InputSanitizationMiddleware, 'DEFAULT_ALLOWED_MIME_TYPES')
        assert hasattr(InputSanitizationMiddleware, 'DANGEROUS_HTML_TAGS')
        assert len(InputSanitizationMiddleware.DEFAULT_ALLOWED_MIME_TYPES) > 0
        assert len(InputSanitizationMiddleware.DANGEROUS_HTML_TAGS) > 0
        print("✅ Input sanitization constants are defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def test_ingestion_tasks():
    """Test ingestion_tasks.py constants."""
    print("\nTesting ingestion_tasks.py...")
    try:
        from workers.celery_tasks.ingestion_tasks import INGESTION_SOURCES
        assert len(INGESTION_SOURCES) > 0
        assert "greenhouse" in INGESTION_SOURCES
        assert "lever" in INGESTION_SOURCES
        assert "rss" in INGESTION_SOURCES
        print("✅ INGESTION_SOURCES constant is defined correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def main():
    """Main test function."""
    print("=" * 60)
    print("JobSwipe Constants Fix Verification")
    print("=" * 60)
    
    tests = [
        test_job_ingestion_service,
        test_file_validation,
        test_api_keys,
        test_notification_service,
        test_cover_letter_service,
        test_cleanup_tasks,
        test_domain_service,
        test_input_sanitization,
        test_ingestion_tasks
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All constants and fixes verified successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()