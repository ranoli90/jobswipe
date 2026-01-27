# JobSwipe Disaster Recovery Runbook

## Overview

This runbook provides step-by-step procedures for recovering JobSwipe services in case of major incidents, data loss, or system failures.

## Emergency Contacts

- **Primary On-Call**: oncall@jobswipe.com
- **Secondary On-Call**: backup@jobswipe.com
- **DevOps Lead**: devops@jobswipe.com
- **Emergency Phone**: +1-XXX-XXX-XXXX

## Incident Response Process

### 1. Incident Detection
- Monitor alerts from Prometheus/AlertManager
- Check Fly.io status dashboard
- Review application logs in Fly.io dashboard

### 2. Incident Assessment
- Determine scope: backend, database, monitoring, etc.
- Assess data loss potential
- Evaluate customer impact
- Notify stakeholders if needed

### 3. Recovery Decision
- Choose appropriate recovery procedure
- Gather required credentials and access
- Prepare recovery environment

## Recovery Procedures

### Database Recovery

#### Complete Database Loss
```bash
# 1. Access backup environment
flyctl ssh console --app jobswipe-backup

# 2. List available backups
aws s3 ls s3://jobswipe-prod/backups/ --human-readable

# 3. Choose most recent backup (or specific point-in-time)
LATEST_BACKUP=$(aws s3 ls s3://jobswipe-prod/backups/ | sort | tail -n 1 | awk '{print $4}')

# 4. Restore database
./backup/restore_postgres.sh "$LATEST_BACKUP"

# 5. Verify data integrity
# Run database health checks
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM jobs;"
```

#### Partial Data Corruption
```bash
# 1. Identify corrupted tables/data
# 2. Restore to temporary database
# 3. Export specific tables
# 4. Import to production database
```

### Backend Service Recovery

#### Service Down
```bash
# 1. Check Fly.io app status
flyctl status --app jobswipe-backend

# 2. Restart service
flyctl restart --app jobswipe-backend

# 3. Scale up if needed
flyctl scale count 2 --app jobswipe-backend
```

#### Complete Service Failure
```bash
# 1. Redeploy from latest working commit
flyctl deploy --app jobswipe-backend

# 2. Restore from staging if available
# (staging should have latest stable code)
```

### Monitoring Stack Recovery

#### Prometheus/Grafana Down
```bash
# 1. Check monitoring services
flyctl status --app jobswipe-prometheus
flyctl status --app jobswipe-grafana

# 2. Restart services
flyctl restart --app jobswipe-prometheus
flyctl restart --app jobswipe-grafana
```

#### Data Loss in Monitoring
```bash
# Monitoring data is ephemeral - focus on application recovery
# Historical metrics will be lost but new metrics will be collected
```

## Backup Verification

### Daily Backup Checks
- [ ] Backup script executed successfully
- [ ] Backup file uploaded to S3
- [ ] Backup file size is reasonable (> 10MB)
- [ ] Backup can be decrypted locally
- [ ] Backup integrity check passes

### Monthly Backup Testing
- [ ] Restore backup to test environment
- [ ] Verify data integrity
- [ ] Test application functionality
- [ ] Document restore time

## Communication Plan

### Internal Communication
- Slack channel: #incidents
- Email distribution: team@jobswipe.com
- Status page: status.jobswipe.com

### Customer Communication
- Status page updates
- Email notifications for prolonged outages
- Social media updates if major incident

## Post-Incident Activities

### 1. Incident Review
- Document timeline
- Identify root cause
- Determine preventive measures

### 2. System Improvements
- Implement fixes for identified issues
- Update monitoring/alerting rules
- Review backup procedures

### 3. Documentation Updates
- Update runbook with lessons learned
- Add new procedures if needed
- Review contact information

## Recovery Time Objectives (RTO)

- **Database Recovery**: 2-4 hours
- **Service Recovery**: 30 minutes - 2 hours
- **Full System Recovery**: 4-8 hours
- **Data Loss**: < 24 hours (daily backups)

## Recovery Point Objectives (RPO)

- **Database**: 24 hours (daily backups)
- **Application Code**: 0 hours (Git-based)
- **Configuration**: 0 hours (version controlled)

## Testing Schedule

- **Backup Testing**: Monthly
- **Failover Testing**: Quarterly
- **Full Disaster Recovery**: Annually
- **Runbook Review**: Quarterly

## Key Metrics to Monitor

- Mean Time To Recovery (MTTR)
- Mean Time Between Failures (MTBF)
- Backup success rate
- Recovery success rate
- Customer impact duration

## Appendices

### A. Environment URLs
- Production: https://jobswipe-backend.fly.dev
- Staging: https://jobswipe-backend-staging.fly.dev
- Monitoring: https://jobswipe-prometheus.fly.dev

### B. Critical Credentials Location
- Fly.io API tokens: GitHub Secrets
- Database credentials: Fly.io Secrets
- AWS credentials: Fly.io Secrets
- Backup encryption keys: Fly.io Secrets

### C. Third-Party Dependencies
- Fly.io status: https://status.fly.io
- AWS S3 status: https://status.aws.amazon.com
- PostgreSQL status: https://status.postgresql.org