web: python -m uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
worker: celery -A backend.workers.celery_app worker --concurrency=2
