# JobSwipe Monitoring Schedule for Fly.io Deployment

## Overview

This document outlines the monitoring schedule and procedures for the JobSwipe application deployed on Fly.io.

## Monitoring Components

### 1. Application Logs (Fly.io Logs)
- **Tool**: `flyctl logs`
- **Schedule**: Real-time monitoring during launch, then daily checks
- **Alert Triggers**:
  - ERROR or CRITICAL level logs
  - Repeated warning patterns
  - Connection failures
  - Authentication failures

### 2. Sentry Error Tracking
- **DSN**: Set via `SENTRY_DSN` environment variable
- **Schedule**:
  - Check daily during first week of launch
  - Then weekly reviews
- **Alert Triggers**:
  - New error types
  - Increasing error rates
  - Performance regressions

### 3. Prometheus Metrics
- **Endpoint**: `/metrics`
- **Schedule**: Continuous monitoring via Grafana dashboards
- **Key Metrics**:
  - Request latency (p50, p95, p99)
  - Error rate by endpoint
  - Database query performance
  - Redis cache hit rate
  - Celery queue length

### 4. Health Checks
- **Endpoints**:
  - `/health` - Basic health check
  - `/ready` - Readiness check (database + Redis)
- **Schedule**: Every 60 seconds via Fly.io health checks

## Daily Monitoring Checklist

### Morning Check (9:00 UTC)
```bash
# Check application logs for overnight issues
flyctl logs --app jobswipe-backend --since 8h | grep -E "ERROR|CRITICAL|WARN"

# Check Sentry for new errors
# View in Sentry dashboard

# Check health endpoints
curl https://jobswipe-backend.fly.dev/health
curl https://jobswipe-backend.fly.dev/ready
```

### Midday Check (14:00 UTC)
```bash
# Check application performance
flyctl metrics --app jobswipe-backend

# Check for rate limiting
flyctl logs --app jobswipe-backend | grep "429"
```

### Evening Check (20:00 UTC)
```bash
# Daily summary check
flyctl logs --app jobswipe-backend --since 6h | tail -50

# Check for deployment issues
flyctl status --app jobswipe-backend
```

## Weekly Monitoring Tasks

### Monday - Performance Review
- Review Prometheus dashboards
- Analyze slow queries
- Check cache efficiency

### Wednesday - Security Review
- Review failed authentication attempts
- Check rate limiting effectiveness
- Review security headers

### Friday - Reliability Review
- Review error rates
- Check Celery worker health
- Verify backup completion

## Alert Response Procedures

### Critical Alert (P1)
1. Acknowledge alert immediately
2. Check Fly.io status: `flyctl status --app jobswipe-backend`
3. Review logs: `flyctl logs --app jobswipe-backend --recent`
4. If deployment issue, rollback: `flyctl deploy --app jobswipe-backend --rollback`
5. Document incident in incident log

### High Alert (P2)
1. Acknowledge within 15 minutes
2. Investigate root cause
3. Create ticket if needs fix
4. Monitor for recurrence

### Medium Alert (P3)
1. Review during next monitoring cycle
2. Add to backlog if needs fix
3. Monitor for escalation

## Log Monitoring Commands

```bash
# Real-time logs
flyctl logs --app jobswipe-backend

# Recent logs (last 100 lines)
flyctl logs --app jobswipe-backend --recent

# Logs since specific time
flyctl logs --app jobswipe-backend --since 1h

# Filter by severity
flyctl logs --app jobswipe-backend | grep "ERROR"
flyctl logs --app jobswipe-backend | grep -E "ERROR|WARN"

# Filter by endpoint
flyctl logs --app jobswipe-backend | grep "/api/v1/"
```

## Grafana Dashboard Access

- **URL**: https://jobswipe-grafana.fly.dev
- **Credentials**: Set via `GRAFANA_ADMIN_PASSWORD` secret

### Recommended Dashboard Panels
1. API Request Rate
2. Response Time Histogram
3. Error Rate by Endpoint
4. Database Connection Pool
5. Redis Cache Performance
6. Celery Worker Status

## Sentry Dashboard Checks

### Daily
- [ ] Review "Unresolved" issues
- [ ] Check "New Releases" for new errors
- [ ] Review "Volume" chart for spikes

### Weekly
- [ ] Review "Trend" analysis
- [ ] Check "User Impact" for user-facing errors
- [ ] Review "Performance" bottlenecks

## Resource Monitoring

### Fly.io Machine Status
```bash
# Check machine status
flyctl machines list --app jobswipe-backend

# Check resource usage
flyctl metrics --app jobswipe-backend
```

### Database Monitoring
```bash
# Check PostgreSQL connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('jobswipe'));"
```

### Redis Monitoring
```bash
# Check memory usage
redis-cli info memory

# Check connected clients
redis-cli info clients
```

## Documentation

- Log all incidents in `docs/incidents/`
- Update runbooks based on findings
- Review and update this schedule monthly

## Contact Information

- **Primary On-Call**: See Fly.io organization settings
- **SLA Response Times**:
  - P1: 15 minutes
  - P2: 1 hour
  - P3: 4 hours
