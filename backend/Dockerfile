# syntax=docker/dockerfile:1.4
FROM python:3.12-slim AS base

# Stage 1: Builder stage with all dependencies and BuildKit cache mounts
FROM base AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    echo "Starting pip install at $(date)" && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --cache-dir /root/.cache/pip -r requirements.txt && \
    python -m spacy download en_core_web_sm && \
    echo "Pip install completed at $(date)"

# Stage 2: Production image with minimal dependencies
FROM python:3.12-slim AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security hardening
RUN groupadd -r appgroup && useradd -r -s /bin/false -g appgroup appuser
RUN mkdir -p /app/logs /app/data && chown -R appuser:appgroup /app
RUN chmod 750 /app && chmod 750 /app/logs /app/data

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code into /app/backend/ directory
# This ensures imports like 'backend.workers.celery_app' work correctly
RUN mkdir -p /app/backend
COPY . /app/backend/

# Set permissions
RUN chown -R appuser:appgroup /app
RUN find /app -type d -exec chmod 750 {} \;
RUN find /app -type f -exec chmod 640 {} \;

# Verify the backend package structure is correct
RUN ls -la /app/backend/ && test -f /app/backend/__init__.py && echo "Backend package structure verified"

USER appuser

# Expose port for API
EXPOSE 8080

# Healthcheck with better configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Resource limits (for Docker Compose/Orchestration)
# mem_limit: 512m
# mem_reservation: 256m
# cpu_shares: 512

# Note: fly.toml controls the start command using uvicorn directly
