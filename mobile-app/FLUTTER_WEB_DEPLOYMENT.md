# Flutter Web Deployment to Fly.io

This document describes the deployment configuration for JobSwipe Flutter web app on Fly.io.

## Architecture

- **Backend API**: `jobswipe-9obhra.fly.dev` (Python/FastAPI)
- **Flutter Web**: `jobswipe-web.fly.dev` (Static Nginx)

## Files Created

| File | Purpose |
|------|---------|
| `Dockerfile.web` | Multi-stage Docker build for Flutter web |
| `fly.toml` | Fly.io app configuration for web deployment |

## Deployment Steps

### 1. Build and Deploy Flutter Web

```bash
cd mobile-app

# Option A: Deploy directly with flyctl
fly deploy --config fly.toml

# Option B: Build Docker image first and test locally
docker build -f Dockerfile.web -t jobswipe-web .
docker run -p 8080:80 jobswipe-web
```

### 2. Configure Custom Domain (Optional)

```bash
fly certs add jobswipe.example.com
```

### 3. Verify Deployment

```bash
# Check app status
fly status

# View logs
fly logs

# Open in browser
fly open
```

## Nginx Configuration Features

The `Dockerfile.web` includes:

- **Gzip compression** for JS, CSS, and JSON
- **Static asset caching** (1 year cache for immutable assets)
- **SPA routing support** (try_files directive)
- **Health check endpoint** at `/health`
- **Security hardening** (file permissions)

## API Endpoint Configuration

Update `lib/config/app_config.dart` to point to the correct backend:

```dart
static const String baseUrl = 'https://jobswipe-9obhra.fly.dev/api/v1';
```

## Troubleshooting

### Blank Screen
1. Check browser console for JavaScript errors
2. Verify API endpoint configuration
3. Check Nginx logs: `fly logs`

### CORS Errors
The backend must allow CORS from the Flutter web domain. Update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jobswipe-web.fly.dev"],
    allow_credentials=True,
)
```

## Alternative: Single App Deployment

If you prefer to serve both backend and frontend from the same domain (e.g., `jobswipe.fly.dev`), you can:

1. Keep backend at `/api/*`
2. Configure Nginx to proxy API requests and serve Flutter web for other routes

This would require modifying the backend's Nginx configuration.
