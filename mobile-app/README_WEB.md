# Flutter Web Build and Run (Containerized)

This document explains how to build and run the Flutter web version using Docker (no local Flutter SDK needed).

## Prerequisites
- Docker installed
- Backend running locally (or a reachable backend URL)

## Backend
Run the backend locally (example):

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8081
```

Ensure CORS allows http://localhost:8080 in non-production (default in the current configuration). In production, configure CORS_ALLOW_ORIGINS.

## Build the Web Image

Build with a custom API base URL passed to Flutter as a compile-time define:

```bash
# From repository root
docker build -f mobile-app/Dockerfile.web -t jobswipe-web \
  --build-arg API_BASE_URL=http://localhost:8081 \
  ./mobile-app
```

## Run the Web Container

```bash
docker run --rm -p 8080:80 jobswipe-web
```

Open http://localhost:8080 in your browser. The app will use the API_BASE_URL defined at build time.

## Notes
- To use a different backend, rebuild with a different `--build-arg API_BASE_URL=...`.
- If you deploy to production, ensure the backend CORS origins include your web domain.
- If API calls fail due to CORS, adjust backend CORS config or origins accordingly.
