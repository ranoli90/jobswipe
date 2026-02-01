# ADR-007: Backup and Point-in-Time Recovery (PITR) Strategy

## Status

Accepted

## Context

JobSwipe needs a reliable backup strategy to:
- Protect against data loss
- Ensure business continuity
- Support disaster recovery
- Comply with regulatory requirements
- Enable point-in-time recovery for critical data

## Decision

We will implement a **comprehensive backup strategy** using PostgreSQL's built-in features and third-party tools:

### Strategy Components

1. **Full Backups**: Weekly full database backups using `pg_basebackup`
2. **Incremental Backups**: Daily incremental backups
3. **WAL Archiving**: Continuous WAL (Write-Ahead Log) archiving every 30 minutes
4. **Point-in-Time Recovery**: Restore to any specific point in time
5. **Verification**: Daily backup integrity checks
6. **Retention**: 30-day retention for full backups, 7-day for incrementals

### Architecture

```
[PostgreSQL] → [WAL Archives] → [Backup Storage]
                [Full/Incremental Backups] → [S3/GCS/Azure]
```

### Schedule

```
- Full Backup: Weekly on Sunday at 2 AM UTC
- Incremental Backup: Daily at 2 AM UTC (Monday-Saturday)
- WAL Archive: Every 30 minutes
- Verify Backup: Daily at 4 AM UTC
- Cleanup: Daily at 5 AM UTC
```

## Consequences

### Positive

1. **Comprehensive Protection**: Full + incremental + WAL archiving provides complete coverage
2. **Point-in-Time Recovery**: Restore to any specific second in time
3. **Automated Scheduling**: Hands-off backup management
4. **Verification**: Ensures backups are valid and restorable
5. **Cloud Integration**: Support for S3, GCS, and Azure storage
6. **Monitoring**: Email notifications for backup status

### Negative

1. **Storage Requirements**: Multiple backup copies consume significant storage
2. **Complexity**: PITR setup and management is more complex
3. **Recovery Time**: Full recovery may take hours depending on data size
4. **Cost**: Cloud storage and transfer costs for backups

## Alternatives Considered

### Snapshot-Based Backups
- Pros: Fast, efficient
- Cons: Doesn't support PITR, storage-level only

### Logical Backups (pg_dump)
- Pros: Simple, portable
- Cons: Slow for large databases, doesn't support PITR

### Cloud Provider Backups (RDS, Cloud SQL)
- Pros: Managed service, simple
- Cons: Vendor lock-in, less control
- Decision factor: We want control over backup process

### Continuous Replication
- Pros: Near-real-time failover
- Cons: Not a true backup solution, data corruption risk
- Decision factor: Complementary to backup strategy, not a replacement

## Implementation Notes

1. **Backup Storage**: Use cloud object storage with lifecycle policies
2. **Encryption**: Encrypt backups at rest and in transit
3. **Monitoring**: Track backup success/failure with metrics
4. **Documentation**: Maintain disaster recovery runbook
5. **Testing**: Regularly test recovery procedures
6. **Configuration Management**: Use Ansible/Chef for backup infrastructure
7. **Alerting**: Set up notifications for failed backups or verification errors

### Tools Used

- `pg_basebackup`: PostgreSQL base backup utility
- `pg_wal`: WAL archiving management
- Custom Python backup manager for scheduling and monitoring
- Shell scripts for backup execution
