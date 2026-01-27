# Phase 1: Critical & Blocker Issues - Task List

## Status: Ready to Start

## Objective
Fix issues that affect code correctness and prevent normal operation (17 issues total).

## Estimated Timeline: Week 1 (2-4 hours)

---

## Pre-Phase Preparation
- [ ] Create branch: `git checkout -b phase1-critical-fixes`
- [ ] Run current issues scan: `python3 scripts/search_phase1_issues.py`
- [ ] Review issues with team (5 minutes)

---

## Task 1: Fix 'await' should be used within an async function (6 issues)
### Files to Check:
- `backend/api/main.py` - lines 130, 144, 159, 188, 265, 289, 291, 446, 465
- `backend/api/websocket_manager.py` - lines 85, 161, 187, 208, 234, 237, 251, 260, 270, 274, 317
- `backend/api/routers/analytics.py` - lines 140, 228, 260, 288, 316, 348, 380, 408
- `backend/api/routers/application_automation.py` - lines 145, 199, 462, 535, 664, 665
- `backend/api/routers/applications.py` - line 86
- `backend/api/routers/auth.py` - line 814
- `backend/api/routers/jobs.py` - lines 121, 197, 353
- `backend/api/routers/jobs_ingestion.py` - lines 86, 131, 172, 212
- `backend/api/routers/profile.py` - lines 106, 109, 116
- `backend/api/routers/notifications.py` - lines 36, 59, 80, 100, 106, 129, 173, 211, 242, 270
- `backend/api/routers/websocket.py` - multiple lines
- `backend/api/middleware/input_sanitization.py` - lines 48, 79, 81, 144
- `backend/services/application_automation.py` - multiple lines
- `backend/services/application_service.py` - lines 143, 155
- `backend/services/embedding_service.py` - lines 81, 82, 126, 127, 231, 234, 239
- `backend/services/job_ingestion_service.py` - lines 236, 238, 261, 318, 505, 534, 556, 560, 565, 569, 578, 582, 603, 608
- `backend/services/matching.py` - lines 224, 271, 364
- `backend/services/notification_service.py` - multiple lines
- `backend/services/oauth2_service.py` - lines 150, 153
- `backend/services/openai_service.py` - line 434
- `backend/services/resume_parser_enhanced.py` - lines 422, 457
- `backend/services/embedding_cache.py` - multiple lines
- `backend/services/push_notification_service.py` - multiple lines
- `backend/services/ab_testing.py` - multiple lines
- `backend/workers/embedding_worker.py` - multiple lines
- `backend/workers/application_agent/agents/greenhouse.py` - multiple lines
- `backend/workers/ingestion/greenhouse.py` - lines 46, 177
- `backend/workers/ingestion/lever.py` - lines 46, 165
- `backend/workers/ingestion/rss.py` - lines 45, 171

### Steps:
1. Search for specific patterns in these files
2. Convert functions to async if await is valid
3. Remove await if function should remain synchronous
4. Test affected endpoints

---

## Task 2: Fix Remove this use of "return" (5 issues)
### Files to Check:
- `backend/metrics.py` - line 676
- `backend/tracing.py` - line 676
- `backend/vault_secrets.py` - line 676
- `backend/config.py` - line 676
- `backend/test_migrations.py` - line 676
- `backend/validate_migrations.py` - line 676
- `backend/create_migration.py` - line 676
- `backend/api/__init__.py` - line 676
- `backend/api/routers/notifications.py` - lines 177, 216, 247
- `backend/api/routers/api_keys.py` - lines 177, 216, 247
- `backend/services/notification_service.py` - lines 238, 750
- `backend/services/openai_service.py` - line 298
- `backend/services/resume_parser.py` - line 298
- `backend/services/embedding_cache.py` - lines 129, 183
- `backend/services/api_key_service.py` - lines 129, 183
- `backend/workers/embedding_worker.py` - line 341
- `backend/workers/celery_app.py` - line 341
- `backend/workers/ingestion/greenhouse.py` - line 151
- `backend/workers/ingestion/lever.py` - line 141
- `backend/workers/ingestion/rss.py` - line 148
- `backend/workers/celery_tasks/__init__.py` - line 148
- `backend/workers/celery_tasks/notification_tasks.py` - line 148
- `backend/workers/celery_tasks/ingestion_tasks.py` - line 148
- `backend/workers/celery_tasks/analytics_tasks.py` - line 148
- `backend/workers/celery_tasks/cleanup_tasks.py` - line 148
- `backend/alembic/env.py` - line 148
- `backend/alembic/versions/004_add_user_id_index.py` - line 148
- `backend/alembic/versions/initial_migration.py` - line 148
- `backend/alembic/versions/002_add_notification_models.py` - line 148
- `backend/alembic/versions/003_add_default_notification_templates.py` - line 148
- `backend/alembic/versions/005_add_api_keys_tables.py` - line 148
- `backend/alembic/versions/006_add_email_verified_field.py` - line 148

### Steps:
1. Look for return statements in loops or improper control flow
2. Refactor to use proper loop control
3. Test affected functionality

---

## Task 3: Fix Value 'app_info' is unsubscriptable (4 issues)
### Files to Check:
- `backend/workers/ingestion/` - Check app_info usage
- `backend/workers/application_agent/` - Check app_info usage

### Steps:
1. Search for `app_info[` in worker files
2. Check if app_info is properly initialized
3. Add null checks or fix type issues
4. Test job ingestion process

---

## Task 4: Fix Parsing failed: 'invalid syntax' (2 issues)
### Steps:
1. Run flake8 to find syntax errors: `flake8 backend/ --count --select=E9 --show-source --statistics`
2. Fix the specific syntax issues
3. Verify all files parse correctly

---

## Task 5: Fix Method 'validate_cors_restrictions' should have "self" (2 issues)
### File:
- `backend/config.py` - line 120

### Current Method:
```python
@classmethod
def validate_cors_restrictions(cls, v, info):
    """Validate that CORS settings are not wildcard in production."""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        if isinstance(v, str) and v.strip() == "*":
            raise ValueError(
                f"{info.field_name} cannot be '*' in production - must specify allowed {info.field_name.replace('cors_allow_', '')}"
            )
        if isinstance(v, list) and v == ["*"]:
            raise ValueError(
                f"{info.field_name} cannot be ['*'] in production - must specify allowed {info.field_name.replace('cors_allow_', '')}"
            )
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v
```

### Steps:
1. Check if method should be instance or class method
2. Fix method signature if needed
3. Test CORS validation

---

## Post-Phase Verification
- [ ] Run flake8 to verify fixes: `flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics`
- [ ] Run all backend tests: `pytest backend/tests/ -v`
- [ ] Run bandit security scan: `bandit -r backend/`
- [ ] Commit changes: `git add . && git commit -m "Phase 1: Fix critical and blocker issues"`
- [ ] Create pull request for review

---

## Success Criteria
- [ ] All 17 Phase 1 issues are fixed
- [ ] flake8 passes without Phase 1 error codes
- [ ] All backend tests pass
- [ ] Bandit security scan shows no new vulnerabilities
- [ ] Application starts and runs without syntax errors

---

## Quick Win Tips
1. Use `grep -rn "await" backend/ --include="*.py" | grep -v "async def"` to quickly find await issues
2. Use `grep -rn "return.*else:" backend/ --include="*.py"` to find return followed by else
3. Use `python -m py_compile` to check for syntax errors
4. Run tests incrementally after each fix to avoid breaking changes
