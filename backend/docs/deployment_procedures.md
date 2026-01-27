# Deployment Procedures

This document describes the deployment procedures for the JobSwipe platform.

## Environments

| Environment | URL | Purpose |
|-------------|-----|---------|
| Development | `api.dev.jobswipe.app` | Development and testing |
| Staging | `api.staging.jobswipe.app` | Pre-production testing |
| Production | `api.jobswipe.app` | Live production |

## Prerequisites

### Required Tools

- Docker 20.10+
- Docker Compose 2.0+
- Fly.io CLI (`flyctl`)
- PostgreSQL 14+ client
- Redis CLI

### Required Accounts

- Fly.io account with organization access
- Docker Hub or container registry access
- OpenAI API access (for embeddings)
- SMTP provider (SendGrid, AWS SES, etc.)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/jobswipe/backend.git
cd backend
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jobswipe
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Encryption
ENCRYPTION_KEY=your-32-byte-key-here

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
FROM_EMAIL=noreply@jobswipe.app

# Storage
STORAGE_BUCKET=jobswipe-storage
STORAGE_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# App Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify services
docker-compose ps
```

### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed initial data (if needed)
python -m db.seed
```

### 5. Run Development Server

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using docker
docker-compose up app
```

### 6. Access API Documentation

Open http://localhost:8000/docs in your browser.

## Docker Deployment

### Build Images

```bash
# Build API image
docker build -f Dockerfile.api -t jobswipe/api:latest .

# Build Automation image
docker build -f Dockerfile.automation -t jobswipe/automation:latest .
```

### Run with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Development deployment
docker-compose up -d
```

### Environment Variables

Ensure all environment variables are properly set in your deployment environment.

## Fly.io Deployment

### 1. Install Fly CLI

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Authenticate
flyctl auth login
```

### 2. Launch Application

```bash
# Launch in production
flyctl launch --name jobswipe-api --region ord

# Or deploy to existing app
flyctl deploy
```

### 3. Set Secrets

```bash
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  SECRET_KEY="your-secret-key" \
  JWT_ALGORITHM="HS256" \
  OPENAI_API_KEY="sk-..." \
  ENCRYPTION_KEY="your-32-byte-key" \
  --app jobswipe-api
```

### 4. Configure Scale

```bash
# Scale to 2 VMs
flyctl scale count 2 --app jobswipe-api

# Configure auto-scaling
flyctl autoscale balanced --min 2 --max 10 --app jobswipe-api
```

### 5. Set Up Volumes

```bash
# Create volume for persistent storage
flyctl volumes create jobswipe_data --size 10 --region ord --app jobswipe-api
```

### 6. Configure Health Checks

```bash
# Add health check
flyctl health-check set \
  --url "/" \
  --interval 30s \
  --timeout 10s \
  --app jobswipe-api
```

### 7. Staging Deployment

```bash
# Deploy to staging
flyctl deploy --config fly.staging.toml --app jobswipe-api-staging
```

### 8. Monitor Deployment

```bash
# View logs
flyctl logs --app jobswipe-api

# View metrics
flyctl metrics --app jobswipe-api

# Check status
flyctl status --app jobswipe-api
```

## Database Migrations

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Upgrade to specific revision
alembic upgrade +2

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current
```

### Creating New Migration

```bash
# Auto-generate migration
alembic revision --autogenerate -m "description_of_change"

# Manual migration
alembic revision -m "description_of_change"
```

### Migration in Production

```bash
# Run migrations with downtime protection
alembic upgrade head --apply-with-downtime-protection
```

## Rollback Procedures

### Database Rollback

```bash
# Rollback single migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>
```

### Application Rollback

```bash
# Rollback to previous release
flyctl deploy --image <previous-image-tag> --app jobswipe-api

# Or restore from volume snapshot
flyctl volumes restore <snapshot-id> --app jobswipe-api
```

### Emergency Rollback

```bash
# Immediately rollback to previous version
flyctl deploy --rollback --app jobswipe-api
```

## Monitoring and Alerting

### Health Checks

```bash
# Check API health
curl https://api.jobswipe.app/health

# Check database connectivity
curl https://api.jobswipe.app/health/db

# Check Redis connectivity
curl https://api.jobswipe.app/health/redis
```

### Metrics

```bash
# View Prometheus metrics
curl https://api.jobswipe.app/metrics
```

### Logs

```bash
# Tail logs
flyctl logs --tail --app jobswipe-api

# Search logs
flyctl logs --search "ERROR" --app jobswipe-api
```

### Setting Up Alerts

```bash
# Configure alerts (via Fly Dashboard or external monitoring)
# Recommended alerts:
# - Error rate > 1%
# - Response time > 500ms
# - CPU usage > 80%
# - Memory usage > 80%
# - Disk usage > 80%
```

## Scaling Procedures

### Horizontal Scaling

```bash
# Increase VM count
flyctl scale count 4 --app jobswipe-api

# Configure auto-scaling
flyctl autoscale balanced --min 2 --max 10 --app jobswipe-api
```

### Vertical Scaling

```bash
# Increase VM size
flyctl scale vm shared-cpu-2x --app jobswipe-api

# Available sizes:
# shared-cpu-1x, shared-cpu-2x, shared-cpu-4x
# performance-1x, performance-2x, performance-4x
```

### Database Scaling

```bash
# Scale PostgreSQL (via Supabase or similar)
# Contact your database provider for scaling options
```

## Security Procedures

### Rotate Secrets

```bash
# Generate new encryption key
python -c "import os; print(os.urandom(32).hex())"

# Update secrets
flyctl secrets set ENCRYPTION_KEY="new-key" --app jobswipe-api

# Important: Decrypt existing data before rotation
```

### SSL/TLS

Fly.io automatically provisions Let's Encrypt certificates.

### Audit Logs

```bash
# View audit logs
flyctl audit-logs --app jobswipe-api
```

## Backup and Recovery

### Database Backups

```bash
# Create backup
pg_dump -h localhost -U user jobswipe > backup.sql

# Restore backup
psql -h localhost -U user jobswipe < backup.sql
```

### Disaster Recovery

See [DISASTER_RECOVERY_RUNBOOK.md](../backup/DISASTER_RECOVERY_RUNBOOK.md)

## CI/CD Pipeline

### GitHub Actions

The CI/CD pipeline runs on every push to `main`:

1. **Lint & Type Check** - Ruff, mypy
2. **Security Scan** - pip-audit, Trivy
3. **Tests** - pytest with coverage
4. **Build** - Docker image build
5. **Deploy** - Fly.io deployment

### Manual Deployment

```bash
# Trigger manual deployment
gh workflow run deploy.yml -f ref=main --repo owner/repo
```

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check database status
flyctl status --app jobswipe-api

# Check logs
flyctl logs --app jobswipe-api | grep -i database

# Verify secrets
flyctl secrets list --app jobswipe-api
```

#### High Memory Usage

```bash
# Check memory metrics
flyctl metrics --app jobswipe-api | grep memory

# Scale up
flyctl scale vm performance-1x --app jobswipe-api
```

#### Slow Response Times

```bash
# Check latency metrics
curl https://api.jobswipe.app/metrics | grep latency

# Check database queries
flyctl logs --app jobswipe-api | grep -i query
```

### Getting Help

- Check logs: `flyctl logs --app jobswipe-api`
- Check status: `flyctl status --app jobswipe-api`
- Contact: devops@jobswipe.app
