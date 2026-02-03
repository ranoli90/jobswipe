#!/bin/bash
#
# JobSwipe Backend Deployment Script for Fly.io
# 
# Usage: ./deploy_backend.sh [environment]
#   environment: production (default), staging
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="jobswipe-backend"
REGISTRY="registry.fly.io/${APP_NAME}"
DOCKERFILE="backend/Dockerfile"

# Get environment
ENVIRONMENT=${1:-production}
echo -e "${GREEN}Deploying to ${ENVIRONMENT} environment...${NC}"

# Set app name based on environment
if [ "$ENVIRONMENT" = "staging" ]; then
    FLY_APP="${APP_NAME}-staging"
    REGISTRY="registry.fly.io/${APP_NAME}-staging"
else
    FLY_APP="${APP_NAME}"
fi

echo -e "${GREEN}Using Fly.io app: ${FLY_APP}${NC}"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}Error: flyctl is not installed.${NC}"
    echo "Install flyctl: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in to Fly.io
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Fly.io. Please login:${NC}"
    flyctl auth login
fi

# Verify required secrets are set
echo -e "${GREEN}Verifying required secrets...${NC}"

REQUIRED_SECRETS=(
    "DATABASE_URL"
    "SECRET_KEY"
    "ENCRYPTION_PASSWORD"
    "ENCRYPTION_SALT"
    "OAUTH_STATE_SECRET"
    "REDIS_URL"
    "CELERY_BROKER_URL"
    "APPLE_KEY_ID"
    "APPLE_TEAM_ID"
    "APPLE_BUNDLE_ID"
    "APPLE_PRIVATE_KEY"
)

OPTIONAL_SECRETS=(
    "SENTRY_DSN"  # For error tracking
    "SENTRY_ENVIRONMENT"
)

# Check required secrets
MISSING_SECRETS=()
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! flyctl secrets list --app "$FLY_APP" 2>/dev/null | grep -q "$secret"; then
        MISSING_SECRETS+=("$secret")
    fi
done

if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required secrets:${NC}"
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "Set secrets with: flyctl secrets set SECRET_NAME='value' --app $FLY_APP"
    exit 1
fi

echo -e "${GREEN}All required secrets are set.${NC}"

# Check for optional Sentry secret
if flyctl secrets list --app "$FLY_APP" 2>/dev/null | grep -q "SENTRY_DSN"; then
    echo -e "${GREEN}Sentry is configured.${NC}"
else
    echo -e "${YELLOW}Warning: SENTRY_DSN not set. Error tracking will be disabled.${NC}"
    echo "To enable Sentry: flyctl secrets set SENTRY_DSN='your-dsn' --app $FLY_APP"
fi

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t "$REGISTRY:latest" -f "$DOCKERFILE" ./backend

# Push the image to Fly.io registry
echo -e "${GREEN}Pushing image to Fly.io registry...${NC}"
docker push "$REGISTRY:latest"

# Deploy the application
echo -e "${GREEN}Deploying to Fly.io...${NC}"
flyctl deploy "$FLY_APP" --image "$REGISTRY:latest" --strategy rolling

# Wait for deployment to complete
echo -e "${GREEN}Waiting for deployment to complete...${NC}"
flyctl deploy "$FLY_APP" --wait

# Verify deployment
echo -e "${GREEN}Verifying deployment...${NC}"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${FLY_APP}.fly.dev/health" || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "Health check: https://${FLY_APP}.fly.dev/health"
    echo -e "API docs: https://${FLY_APP}.fly.dev/docs"
else
    echo -e "${YELLOW}Warning: Health check returned status $HEALTH_STATUS${NC}"
    echo "Check logs with: flyctl logs --app $FLY_APP"
fi

# Show deployment info
echo ""
echo -e "${GREEN}Deployment Information:${NC}"
echo "App: $FLY_APP"
echo "URL: https://${FLY_APP}.fly.dev"
echo "Region: $(flyctl regions list --app $FLY_APP | grep primary)"

# Show monitoring commands
echo ""
echo -e "${GREEN}Monitoring Commands:${NC}"
echo "View logs: flyctl logs --app $FLY_APP"
echo "View metrics: flyctl metrics --app $FLY_APP"
echo "Check status: flyctl status --app $FLY_APP"

echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
