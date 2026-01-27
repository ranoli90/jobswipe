# Database Performance Monitoring and Integrity Guide

This document provides SQL queries and scripts for:
1. Checking referential integrity constraints
2. Identifying orphaned records
3. Monitoring database performance
4. Finding optimization opportunities

## 1. Referential Integrity Checks

### Find Orphaned User Records

```sql
-- Find candidate profiles without valid users
SELECT cp.id, cp.user_id 
FROM candidate_profiles cp 
LEFT JOIN users u ON cp.user_id = u.id 
WHERE u.id IS NULL;

-- Find user job interactions without valid users
SELECT ui.id, ui.user_id 
FROM user_job_interactions ui 
LEFT JOIN users u ON ui.user_id = u.id 
WHERE u.id IS NULL;

-- Find user job interactions without valid jobs
SELECT ui.id, ui.job_id 
FROM user_job_interactions ui 
LEFT JOIN jobs j ON ui.job_id = j.id 
WHERE j.id IS NULL;

-- Find application tasks without valid users
SELECT at.id, at.user_id 
FROM application_tasks at 
LEFT JOIN users u ON at.user_id = u.id 
WHERE u.id IS NULL;

-- Find application tasks without valid jobs
SELECT at.id, at.job_id 
FROM application_tasks at 
LEFT JOIN jobs j ON at.job_id = j.id 
WHERE j.id IS NULL;

-- Find application audit logs without valid tasks
SELECT aal.id, aal.task_id 
FROM application_audit_logs aal 
LEFT JOIN application_tasks at ON aal.task_id = at.id 
WHERE at.id IS NULL;

-- Find notifications without valid users
SELECT n.id, n.user_id 
FROM notifications n 
LEFT JOIN users u ON n.user_id = u.id 
WHERE u.id IS NULL;

-- Find device tokens without valid users
SELECT dt.id, dt.user_id 
FROM device_tokens dt 
LEFT JOIN users u ON dt.user_id = u.id 
WHERE u.id IS NULL;

-- Find user notification preferences without valid users
SELECT unp.id, unp.user_id 
FROM user_notification_preferences unp 
LEFT JOIN users u ON unp.user_id = u.id 
WHERE u.id IS NULL;

-- Find cover letter templates without valid users
SELECT clt.id, clt.user_id 
FROM cover_letter_templates clt 
LEFT JOIN users u ON clt.user_id = u.id 
WHERE u.id IS NULL;

-- Find API keys without valid creators
SELECT ak.id, ak.created_by 
FROM api_keys ak 
LEFT JOIN users u ON ak.created_by = u.id 
WHERE u.id IS NULL;

-- Find API key usage logs without valid API keys
SELECT akul.id, akul.api_key_id 
FROM api_key_usage_logs akul 
LEFT JOIN api_keys ak ON akul.api_key_id = ak.id 
WHERE ak.id IS NULL;
```

## 2. Fix Orphaned Records

### Create Cleanup Migration Script

```sql
-- Create a function to clean orphaned records
CREATE OR REPLACE FUNCTION cleanup_orphaned_records()
RETURNS void AS $$
BEGIN
    -- Delete orphaned candidate profiles
    DELETE FROM candidate_profiles 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned user job interactions (users)
    DELETE FROM user_job_interactions 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned user job interactions (jobs)
    DELETE FROM user_job_interactions 
    WHERE job_id NOT IN (SELECT id FROM jobs);

    -- Delete orphaned application tasks (users)
    DELETE FROM application_tasks 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned application tasks (jobs)
    DELETE FROM application_tasks 
    WHERE job_id NOT IN (SELECT id FROM jobs);

    -- Delete orphaned application audit logs
    DELETE FROM application_audit_logs 
    WHERE task_id NOT IN (SELECT id FROM application_tasks);

    -- Delete orphaned notifications
    DELETE FROM notifications 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned device tokens
    DELETE FROM device_tokens 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned user notification preferences
    DELETE FROM user_notification_preferences 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned cover letter templates
    DELETE FROM cover_letter_templates 
    WHERE user_id NOT IN (SELECT id FROM users);

    -- Delete orphaned API keys
    DELETE FROM api_keys 
    WHERE created_by NOT IN (SELECT id FROM users);

    -- Delete orphaned API key usage logs
    DELETE FROM api_key_usage_logs 
    WHERE api_key_id NOT IN (SELECT id FROM api_keys);

    RAISE NOTICE 'Orphaned records cleaned up successfully';
END;
$$ LANGUAGE plpgsql;
```

## 3. Performance Monitoring Queries

### Table Sizes and Row Counts

```sql
-- Get table sizes and row counts
SELECT 
    relname AS table_name,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_total_relation_size(relid) AS total_size,
    n_live_tup AS estimated_rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Index Statistics

```sql
-- Get index sizes and usage statistics
SELECT 
    t.relname AS table_name,
    i.relname AS index_name,
    pg_size_pretty(pg_relation_size(i.oid)) AS index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes i
JOIN pg_index ix ON i.indexrelid = ix.indexrelid
JOIN pg_stat_user_tables t ON i.relid = t.relid
ORDER BY pg_relation_size(i.oid) DESC;
```

### Slow Query Analysis

```sql
-- Get slowest queries from pg_stat_statements
SELECT 
    query,
    calls,
    mean_time,
    total_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

### Missing Indexes Detection

```sql
-- Find tables with sequential scans (potential missing indexes)
SELECT 
    seq_scan,
    seq_tup_read,
    idx_scan,
    relname
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 10;
```

### Lock Monitoring

```sql
-- Active locks
SELECT 
    pid,
    usename,
    state,
    query,
    wait_event,
    wait_event_type
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY query_start;
```

### Connection Pool Monitoring

```sql
-- Connection statistics
SELECT 
    state,
    COUNT(*) AS connection_count
FROM pg_stat_activity
GROUP BY state
ORDER BY state;
```

## 4. Index Optimization Queries

### Create Missing Indexes

```sql
-- Index for candidate_profiles.user_id (already exists via FK)
CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user_id 
ON candidate_profiles(user_id);

-- Index for notifications.user_id
CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
ON notifications(user_id);

-- Index for notifications.created_at
CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
ON notifications(created_at);

-- Index for device_tokens.user_id
CREATE INDEX IF NOT EXISTS idx_device_tokens_user_id 
ON device_tokens(user_id);

-- Index for application_tasks.status
CREATE INDEX IF NOT EXISTS idx_application_tasks_status 
ON application_tasks(status);

-- Index for application_tasks.created_at
CREATE INDEX IF NOT EXISTS idx_application_tasks_created_at 
ON application_tasks(created_at);

-- Index for user_job_interactions.user_id (already exists via migration 004)
-- Index for user_job_interactions.job_id
CREATE INDEX IF NOT EXISTS idx_user_job_interactions_job_id 
ON user_job_interactions(job_id);

-- Index for user_job_interactions.action
CREATE INDEX IF NOT EXISTS idx_user_job_interactions_action 
ON user_job_interactions(action);

-- Index for user_job_interactions.created_at
CREATE INDEX IF NOT EXISTS idx_user_job_interactions_created_at 
ON user_job_interactions(created_at);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_user_job_interactions_user_created 
ON user_job_interactions(user_id, created_at DESC);

-- Index for jobs.source
CREATE INDEX IF NOT EXISTS idx_jobs_source 
ON jobs(source);

-- Index for jobs.created_at
CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
ON jobs(created_at DESC);

-- Index for api_keys.service_type
CREATE INDEX IF NOT EXISTS idx_api_keys_service_type 
ON api_keys(service_type);

-- Index for api_keys.is_active
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active 
ON api_keys(is_active);

-- Index for api_keys.created_at
CREATE INDEX IF NOT EXISTS idx_api_keys_created_at 
ON api_keys(created_at DESC);

-- Index for api_key_usage_logs.api_key_id
CREATE INDEX IF NOT EXISTS idx_api_key_usage_logs_api_key_id 
ON api_key_usage_logs(api_key_id);

-- Index for api_key_usage_logs.created_at
CREATE INDEX IF NOT EXISTS idx_api_key_usage_logs_created_at 
ON api_key_usage_logs(created_at DESC);
```

## 5. Query Performance Testing

### Test Query Execution Time

```sql
-- Enable timing
\timing on

-- Test query (replace with actual query)
SELECT COUNT(*) FROM user_job_interactions;

-- Disable timing
\timing off
```

### Explain Analyze

```sql
-- Get query execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM user_job_interactions 
WHERE user_id = 'some-uuid-here'
ORDER BY created_at DESC
LIMIT 50;
```

## 6. Health Check Queries

### Overall Database Health

```sql
-- Database size
SELECT 
    pg_size_pretty(pg_database_size(current_database())) AS db_size;

-- Last vacuum/analyze times
SELECT 
    relname,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_vacuum NULLS FIRST;

-- Dead tuples ratio
SELECT 
    relname,
    n_dead_tup,
    n_live_tup,
    CASE 
        WHEN n_live_tup > 0 
        THEN ROUND((n_dead_tup::numeric / n_live_tup) * 100, 2)
        ELSE 0
    END AS dead_tuple_percent
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;
```

### Replication Lag (if applicable)

```sql
-- Check replication lag
SELECT 
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(sent_lsn, write_lsn) AS replication_lag_bytes
FROM pg_stat_replication;
```

## 7. Scheduled Maintenance Queries

### Weekly Maintenance Script

```sql
-- Run during low-traffic periods
VACUUM ANALYZE;

-- Reindex frequently updated tables (optional)
-- REINDEX TABLE user_job_interactions;
-- REINDEX TABLE application_tasks;
```

### Monthly Deep Clean

```sql
-- More aggressive maintenance
VACUUM FULL ANALYZE;

-- Rebuild all indexes (requires exclusive lock)
-- REINDEX DATABASE current_database;
```

## 8. Alerting Thresholds

### Set up alerts for:

| Metric | Warning | Critical |
|--------|---------|----------|
| Dead tuple ratio | > 20% | > 50% |
| Connection usage | > 70% | > 90% |
| Replication lag | > 10MB | > 100MB |
| Long running queries | > 60s | > 300s |
| Table size growth | > 10GB/week | > 50GB/week |

## 9. Performance Baseline Queries

### Store baseline metrics

```sql
-- Create table to store baseline metrics
CREATE TABLE IF NOT EXISTS performance_baseline (
    id SERIAL PRIMARY KEY,
    collected_at TIMESTAMP DEFAULT NOW(),
    total_connections INTEGER,
    active_connections INTEGER,
    db_size BIGINT,
    total_rows_users BIGINT,
    total_rows_jobs BIGINT,
    total_rows_interactions BIGINT,
    avg_query_time_ms FLOAT
);

-- Insert baseline
INSERT INTO performance_baseline (total_connections, active_connections, db_size)
SELECT 
    pg_stat_activity.numbackends,
    COUNT(*) FILTER (WHERE state = 'active'),
    pg_database_size(current_database()),
    (SELECT COUNT(*) FROM users),
    (SELECT COUNT(*) FROM jobs),
    (SELECT COUNT(*) FROM user_job_interactions),
    (SELECT AVG(mean_time) FROM pg_stat_statements WHERE query LIKE '%jobs%');
```
