# JobSwipe Production Deployment Guide

This guide provides step-by-step instructions for deploying JobSwipe to production on Fly.io.

## Prerequisites

### Required Tools
- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) - `flyctl`
- [Flutter SDK](https://flutter.dev/docs/get-started/install) - `flutter`
- [Git](https://git-scm.com/) - `git`
- [Docker](https://docs.docker.com/get-docker/) - `docker`

### Required Accounts
- [Fly.io account](https://fly.io/app/sign-up)
- [Google Play Console account](https://play.google.com/console) (for Android)
- [Apple Developer account](https://developer.apple.com/) (for iOS)

## Backend Deployment

### Step 1: Install Fly.io CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2: Login to Fly.io

```bash
flyctl auth login
```

### Step 3: Create Fly.io App

```bash
cd backend
flyctl launch --name jobswipe-backend --region iad
```

### Step 4: Set Environment Variables

The deployment script will automatically set secrets from `.env.production`:

```bash
chmod +x deploy_backend.sh
./deploy_backend.sh
```

Or manually set secrets:

```bash
flyctl secrets set DATABASE_URL="postgresql://..."
flyctl secrets set REDIS_URL="redis://..."
flyctl secrets set SECRET_KEY="your-secret-key"
# ... set all other secrets from .env.production
```

### Step 5: Deploy Backend

```bash
# Using the deployment script
./deploy_backend.sh

# Or manually
flyctl deploy --config backend/fly.toml
```

### Step 6: Verify Deployment

```bash
# Check status
flyctl status --app jobswipe-backend

# Check logs
flyctl logs --app jobswipe-backend

# Health check
curl https://jobswipe-backend.fly.dev/health
```

### Step 7: Configure Custom Domain (Optional)

```bash
# Add custom domain
flyctl certs add yourdomain.com --app jobswipe-backend

# Update DNS records as instructed by flyctl
```

## Mobile App Deployment

### Step 1: Configure Production Backend URL

The mobile app is already configured to use the production backend URL when built with `--dart-define=ENV=production`.

### Step 2: Build for Production

```bash
cd mobile-app
chmod +x deploy_mobile.sh
./deploy_mobile.sh
```

Or manually:

```bash
# Get dependencies
flutter pub get

# Run tests
flutter test

# Build Android APK
flutter build apk --release --dart-define=ENV=production

# Build Android App Bundle (for Play Store)
flutter build appbundle --release --dart-define=ENV=production

# Build iOS IPA (for App Store)
flutter build ios --release --dart-define=ENV=production
```

### Step 3: Deploy to App Stores

#### Android (Google Play Store)

1. Go to [Google Play Console](https://play.google.com/console)
2. Create a new app or select existing app
3. Upload the `.aab` file from `build/app/outputs/bundle/release/`
4. Complete the store listing
5. Submit for review

#### iOS (Apple App Store)

1. Go to [App Store Connect](https://appstoreconnect.apple.com/)
2. Create a new app or select existing app
3. Upload the `.ipa` file from `build/ios/archive/`
4. Complete the app information
5. Submit for review

## Environment Configuration

### Development

```bash
flutter run --dart-define=ENV=development
```

Uses: `http://localhost:8000`

### Staging

```bash
flutter run --dart-define=ENV=staging
```

Uses: `https://jobswipe-staging.fly.dev`

### Production

```bash
flutter run --dart-define=ENV=production
```

Uses: `https://jobswipe-backend.fly.dev`

## Monitoring and Maintenance

### Backend Monitoring

```bash
# View logs
flyctl logs --app jobswipe-backend

# View metrics
flyctl metrics --app jobswipe-backend

# Scale up/down
flyctl scale count 2 --app jobswipe-backend

# View regions
flyctl regions list
```

### Health Checks

```bash
# Basic health check
curl https://jobswipe-backend.fly.dev/health

# Readiness check (includes database, Redis, Ollama)
curl https://jobswipe-backend.fly.dev/ready

# Metrics endpoint
curl https://jobswipe-backend.fly.dev/metrics
```

### Database Management

```bash
# SSH into the app
flyctl ssh console --app jobswipe-backend

# Run migrations
python -m backend.db.migrate

# Check database tables
python -c "from backend.db.database import engine; print(engine.table_names())"
```

## Troubleshooting

### Backend Issues

#### App won't start
```bash
# Check logs
flyctl logs --app jobswipe-backend

# Check if all secrets are set
flyctl secrets list --app jobswipe-backend
```

#### Database connection issues
```bash
# Check DATABASE_URL secret
flyctl secrets list --app jobswipe-backend | grep DATABASE_URL

# Test database connection
flyctl ssh console --app jobswipe-backend -C "python -c 'from backend.db.database import engine; print(engine.connect())'"
```

#### Redis connection issues
```bash
# Check REDIS_URL secret
flyctl secrets list --app jobswipe-backend | grep REDIS_URL

# Test Redis connection
flyctl ssh console --app jobswipe-backend -C "python -c 'import redis; r = redis.from_url(os.getenv(\"REDIS_URL\")); print(r.ping())'"
```

### Mobile App Issues

#### API connection errors
- Verify backend is running: `curl https://jobswipe-backend.fly.dev/health`
- Check if the correct environment is being used
- Verify network connectivity

#### Build errors
```bash
# Clean build cache
flutter clean

# Get fresh dependencies
flutter pub get

# Upgrade Flutter
flutter upgrade
```

## Security Best Practices

### API Keys and Secrets Management

**API Keys Audit Results: ✅ PASSED**

- **Validation**: Automated validation via `tools/validate_secrets.py`
- **Storage**: All secrets stored securely in Fly.io secrets management
- **Encryption**: PII data encrypted with Fernet, secrets encrypted at rest
- **Access Control**: API keys scoped to specific services with audit logging
- **Rotation**: Regular rotation policy implemented with automated reminders
- **Monitoring**: Failed authentication attempts logged and alerted

**Key Security Features:**
1. **Never commit secrets** - Use `.env.production` as template, set via `flyctl secrets set`
2. **Environment-specific validation** - Production secrets validated against development defaults
3. **Audit logging** - All secret access and API key usage logged
4. **Rate limiting** - Redis-backed distributed rate limiting (auth: 5/min, API: 60/min, public: 100/min)
5. **HTTPS enforcement** - All production traffic encrypted with custom domains
6. **Input sanitization** - Comprehensive validation and sanitization middleware
7. **Security headers** - CSP, HSTS, X-Frame-Options, and other headers enabled

### Additional Security Measures

- **Multi-factor authentication** - TOTP and backup codes for user accounts
- **Account lockout** - Automatic lockout after failed login attempts
- **OAuth2 integration** - Secure social login with Google and LinkedIn
- **PII encryption** - Personal data encrypted in database
- **Structured logging** - Security events logged with correlation IDs
- **Dependency updates** - Regular updates via automated pipelines

## Cost Optimization

### Fly.io Backend

- Use `auto_stop_machines = true` to stop idle instances
- Set appropriate `min_machines_running` and `max_machines_running`
- Monitor usage with `flyctl metrics`

### Mobile App

- Use app bundles (`.aab`) for Android instead of APKs
- Optimize images and assets
- Use code splitting for large apps

## Backup and Recovery

### Database Backups

Fly.io provides automatic backups for PostgreSQL. To restore:

```bash
# List backups
flyctl postgres backups list --app jobswipe-backend

# Restore from backup
flyctl postgres backups restore <backup-id> --app jobswipe-backend
```

### Manual Backup

```bash
# SSH into the app
flyctl ssh console --app jobswipe-backend

# Export database
pg_dump $DATABASE_URL > backup.sql

# Copy backup to local machine
flyctl sftp get backup.sql --app jobswipe-backend
```

## Support

For issues or questions:
- Backend: Check logs with `flyctl logs --app jobswipe-backend`
- Mobile: Check Flutter documentation at https://flutter.dev/docs
- Fly.io: https://community.fly.io/
