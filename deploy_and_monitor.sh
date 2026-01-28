#!/bin/bash
# Deploy to fly.io and monitor logs

set -e

APP_NAME="jobswipe-9obhra"
BACKEND_DIR="backend"

echo "======================================"
echo "Fly.io Deployment and Monitor Script"
echo "======================================"

# Check if flyctl exists
if [ ! -f "./flyctl" ]; then
    echo "Error: flyctl not found in current directory"
    exit 1
fi

# Function to deploy
deploy() {
    echo ""
    echo "Deploying to Fly.io..."
    cd "$BACKEND_DIR"
    ../flyctl deploy --app "$APP_NAME" --yes
    cd ..
    echo "Deployment initiated!"
}

# Function to monitor logs
monitor_logs() {
    echo ""
    echo "Monitoring logs (press Ctrl+C to stop)..."
    ./flyctl logs --app "$APP_NAME" --json 2>&1 | tee /tmp/fly_logs_live.json | while read line; do
        # Parse and display important messages
        echo "$line" | python3 -c "
import sys
import json

try:
    log = json.loads(sys.stdin.read())
    msg = log.get('message', '')
    level = log.get('level', 'info')
    instance = log.get('instance', 'unknown')[:12]
    
    # Color code based on level
    color = ''
    reset = '\033[0m'
    if level == 'error':
        color = '\033[91m'  # Red
    elif level == 'warn' or level == 'warning':
        color = '\033[93m'  # Yellow
    elif 'ValidationError' in msg or 'error' in msg.lower():
        color = '\033[91m'
    
    # Only print important messages
    if any(x in msg.lower() for x in ['error', 'exception', 'validation', 'failed', 'crash', 'restart', 'critical', 'fatal']):
        print(f'{color}[{instance}] {msg[:150]}{reset}')
    elif 'starting' in msg.lower() or 'ready' in msg.lower() or 'listening' in msg.lower():
        print(f'\033[92m[{instance}] {msg[:150]}{reset}')  # Green for good news
except:
    pass
" 2>/dev/null || true
    done
}

# Function to check status
check_status() {
    echo ""
    echo "Checking app status..."
    ./flyctl status --app "$APP_NAME"
}

# Function to run log analysis
analyze_logs() {
    echo ""
    echo "Analyzing recent logs..."
    ./flyctl logs --app "$APP_NAME" -n --json > /tmp/fly_logs_recent.json 2>&1
    python3 debug_fly_logs.py /tmp/fly_logs_recent.json
}

# Menu
case "${1:-menu}" in
    deploy)
        deploy
        ;;
    logs)
        monitor_logs
        ;;
    status)
        check_status
        ;;
    analyze)
        analyze_logs
        ;;
    full)
        deploy
        sleep 10
        check_status
        analyze_logs
        ;;
    *)
        echo ""
        echo "Usage: $0 [deploy|logs|status|analyze|full]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the app to fly.io"
        echo "  logs    - Monitor live logs with filtering"
        echo "  status  - Check app status"
        echo "  analyze - Analyze recent logs"
        echo "  full    - Deploy, wait, check status, and analyze"
        echo ""
        ;;
esac
