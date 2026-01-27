#!/bin/bash

# JobSwipe Backend Deployment Script for Fly.io
# This script deploys the backend to Fly.io production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}JobSwipe Backend Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if flyctl is available (prefer newly installed version)
FLYCTL="$HOME/.fly/bin/flyctl"
if [ ! -f "$FLYCTL" ]; then
    if ! command -v flyctl &> /dev/null; then
        echo -e "${RED}Error: flyctl is not installed${NC}"
        echo "Please install flyctl: https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi
    FLYCTL="flyctl"
fi

# Check if user is logged in
if ! $FLYCTL auth whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Fly.io${NC}"
    echo "Please login: $FLYCTL auth login"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production file not found${NC}"
    exit 1
fi

# Validate required secrets
echo -e "\n${YELLOW}Validating required secrets...${NC}"
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
    echo -e "${RED}Error: Missing or invalid required secrets:${NC}"
    for secret in "${missing_secrets[@]}"; do
        echo "  - $secret"
    done
    exit 1
fi

# Set environment variables from .env.production
echo -e "\n${YELLOW}Setting environment variables...${NC}"

# Read .env.production and set secrets
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # Remove quotes from value
    value=$(echo "$value" | sed 's/^["'\''\"]//;s/["'\''\"]$//')
    
    # Skip if value is empty
    [ -z "$value" ] && continue
    
    # Set secret (skip if already set with same value)
    if $FLYCTL secrets list --app jobswipe-backend 2>/dev/null | grep -q "^$key"; then
        echo -e "${GREEN}✓ Secret $key already set${NC}"
    else
        echo "Setting secret: $key"
        $FLYCTL secrets set "$key=$value" --app jobswipe-backend
    fi
done < .env.production

# Deploy backend
echo -e "\n${YELLOW}Deploying backend to Fly.io...${NC}"
cd backend || exit 1

if $FLYCTL deploy --app jobswipe-backend --remote-only; then
    echo -e "${GREEN}✓ Deployment successful${NC}"
    
    # Check if workers are running
    echo -e "\n${YELLOW}Checking worker processes...${NC}"
    if $FLYCTL scale count worker=1 --app jobswipe-backend; then
        echo -e "${GREEN}✓ Worker process scaled to 1 instance${NC}"
    fi
    
    # Verify deployment
    echo -e "\n${YELLOW}Verifying deployment...${NC}"
    if $FLYCTL status --app jobswipe-backend; then
        echo -e "${GREEN}✓ Deployment verified${NC}"
    fi
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}Error: Deployment failed${NC}"
    exit 1
fi
