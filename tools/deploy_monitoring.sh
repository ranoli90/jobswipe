#!/bin/bash

# JobSwipe Monitoring Stack Deployment Script
# Deploys Prometheus and Grafana to Fly.io

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}JobSwipe Monitoring Stack Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if flyctl is available
if ! ./flyctl version &> /dev/null; then
    echo -e "${RED}Error: flyctl is not available${NC}"
    echo "Please ensure flyctl binary is in the current directory"
    exit 1
fi

# Check if user is logged in
if ! ./flyctl auth whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Fly.io${NC}"
    echo "Please login: ./flyctl auth login"
    exit 1
fi

# Create and deploy Prometheus
echo -e "\n${YELLOW}Creating and deploying Prometheus...${NC}"
cd monitoring
if ! ../flyctl apps list | grep -q "jobswipe-prometheus"; then
    ../flyctl apps create jobswipe-prometheus --org personal || { echo -e "${RED}✗ Failed to create Prometheus app${NC}"; exit 1; }
fi
if ../flyctl deploy --config prometheus-fly.toml --remote-only; then
    echo -e "${GREEN}✓ Prometheus deployed successfully${NC}"
else
    echo -e "${RED}✗ Prometheus deployment failed${NC}"
    exit 1
fi

# Create and deploy Grafana
echo -e "\n${YELLOW}Creating and deploying Grafana...${NC}"
if ! ../flyctl apps list | grep -q "jobswipe-grafana"; then
    ../flyctl apps create jobswipe-grafana --org personal || { echo -e "${RED}✗ Failed to create Grafana app${NC}"; exit 1; }
fi
if ../flyctl deploy --config grafana-fly.toml --remote-only; then
    echo -e "${GREEN}✓ Grafana deployed successfully${NC}"
else
    echo -e "${RED}✗ Grafana deployment failed${NC}"
    exit 1
fi

cd ..

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Monitoring Stack Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nAccess URLs:"
echo -e "Prometheus: https://jobswipe-prometheus.fly.dev"
echo -e "Grafana: https://jobswipe-grafana.fly.dev"
echo -e "\nGrafana Credentials:"
echo -e "Username: admin"
echo -e "Password: admin (change this immediately!)"
echo -e "\nNext steps:"
echo -e "1. Change Grafana admin password"
echo -e "2. Configure data sources in Grafana"
echo -e "3. Import dashboards"