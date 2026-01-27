FROM python:3.12-slim AS base

# Stage 1: Build dependencies
FROM base AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# Stage 2: Production image
FROM base AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*



# Create non-root user for security
RUN useradd -m -u 1000 appuser
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app

# Copy dependencies from builder stage
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages

# Copy application code
COPY . .

# Set permissions
RUN chown -R appuser:appuser /app

USER appuser

# Expose port for API
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with Gunicorn for production
CMD ["gunicorn", "api.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
