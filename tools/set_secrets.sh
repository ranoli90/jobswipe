#!/bin/bash
set -euo pipefail

# Usage: tools/set_secrets.sh [APP_NAME]
APP_NAME="${1:-jobswipe-9obhra}"

export PATH="$HOME/.fly/bin:$PATH"

if ! command -v flyctl &> /dev/null; then
    echo "Error: flyctl is not installed"
    echo "Install flyctl: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

if ! flyctl auth whoami &> /dev/null; then
    echo "Not logged in to Fly.io"
    echo "Login: flyctl auth login"
    exit 1
fi

# Optional environment overrides
if [ -f ".env.production" ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env.production
    set +a
fi

DATABASE_URL=${DATABASE_URL:-postgresql+psycopg2://jobswipe:jobswipe@db.internal:5432/jobswipe}
SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
ENCRYPTION_PASSWORD=${ENCRYPTION_PASSWORD:-$(openssl rand -hex 32)}
ENCRYPTION_SALT=${ENCRYPTION_SALT:-$(openssl rand -hex 32)}
OAUTH_STATE_SECRET=${OAUTH_STATE_SECRET:-$(openssl rand -hex 32)}
CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://default:password@redis.internal:6379/0}
CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://default:password@redis.internal:6379/1}
KAFKA_BROKER_URL=${KAFKA_BROKER_URL:-kafka.internal:9092}

echo "Setting secrets for $APP_NAME..."
flyctl secrets set -a "$APP_NAME" \
  DATABASE_URL="$DATABASE_URL" \
  SECRET_KEY="$SECRET_KEY" \
  ENCRYPTION_PASSWORD="$ENCRYPTION_PASSWORD" \
  ENCRYPTION_SALT="$ENCRYPTION_SALT" \
  OAUTH_STATE_SECRET="$OAUTH_STATE_SECRET" \
  CELERY_BROKER_URL="$CELERY_BROKER_URL" \
  CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND" \
  KAFKA_BROKER_URL="$KAFKA_BROKER_URL"

echo "Secrets set for $APP_NAME."
