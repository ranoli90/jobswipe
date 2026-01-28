#!/bin/bash

# Set default app name or use provided one
APP_NAME="${APP_NAME:-jobswipe-9obhra}"

export PATH="$HOME/.fly/bin:$PATH"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "Error: flyctl is not installed"
    echo "Please install flyctl: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "Not logged in to Fly.io"
    echo "Please login: flyctl auth login"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "Error: .env.production file not found"
    exit 1
fi

# Validate required secrets
required_secrets=("DATABASE_URL" "REDIS_URL" "SECRET_KEY" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "ENCRYPTION_PASSWORD" "ENCRYPTION_SALT")
missing_secrets=()

while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # Check if this is a required secret and it's missing or invalid
    for secret in "${required_secrets[@]}"; do
        if [ "$key" == "$secret" ]; then
            value=$(echo "$value" | sed 's/^["'\''\"]//;s/["'\''\"]$//')
            if [ -z "$value" ] || [[ "$value" =~ ^(dev-|CHANGE_|minioadmin).*$ ]]; then
                missing_secrets+=("$key")
            fi
        fi
    done
done < .env.production

if [ ${#missing_secrets[@]} -ne 0 ]; then
    echo "Error: Missing or invalid required secrets:"
    for secret in "${missing_secrets[@]}"; do
        echo "  - $secret"
    done
    exit 1
fi

# Set secrets from .env.production
echo "Setting secrets from .env.production..."
while IFS='=' read -r key value; do
    if [[ $key =~ ^[A-Z_]+$ ]]; then
        # Remove quotes from value
        value=$(echo "$value" | sed 's/^["'\''\"]//;s/["'\''\"]$//')
        # Skip if value is empty
        [ -z "$value" ] && continue
        echo "Setting secret: $key"
        flyctl secrets set --app "$APP_NAME" "$key"="$value"
    fi
done < .env.production

echo "All secrets set successfully!"