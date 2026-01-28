#!/bin/bash

# Real-time monitoring script for Jobswipe API load testing
# Monitors Fly.io scaling events and system metrics

APP_NAME="jobswipe"
REGION="lax"
INTERVAL=10
DURATION=300  # 5 minutes by default

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--app)
            APP_NAME="$2"
            shift; shift
            ;;
        -r|--region)
            REGION="$2"
            shift; shift
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift; shift
            ;;
        -d|--duration)
            DURATION="$2"
            shift; shift
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Usage: $0 [--app APP_NAME] [--region REGION] [--interval SECONDS] [--duration SECONDS]"
            exit 1
            ;;
    esac
done

echo "=== Jobswipe API Load Test Monitoring ==="
echo "App: $APP_NAME"
echo "Region: $REGION"
echo "Interval: ${INTERVAL}s"
echo "Duration: ${DURATION}s"
echo "========================================="
echo ""

# Function to log messages with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to get Fly.io app instances
get_instances() {
    flyctl status --app $APP_NAME | grep -E "(v[0-9]+:|   [0-9] instances)"
}

# Function to get Fly.io metrics
get_metrics() {
    flyctl vm status --app $APP_NAME --json 2>/dev/null || echo "[]"
}

# Function to check if app is running
check_app_running() {
    if ! flyctl status --app $APP_NAME >/dev/null 2>&1; then
        log "Error: App $APP_NAME is not running"
        return 1
    fi
    return 0
}

# Main monitoring loop
main() {
    log "Starting monitoring..."
    
    if ! check_app_running; then
        exit 1
    fi
    
    log "Initial instances: $(get_instances)"
    log "========================================="
    
    start_time=$(date +%s)
    end_time=$((start_time + DURATION))
    
    while [ $(date +%s) -lt $end_time ]; do
        # Get instance count and list
        instances=$(get_instances)
        log "Instance status:"
        echo "$instances"
        echo ""
        
        # Get metrics
        log "Application metrics:"
        if [ -x "$(command -v curl)" ]; then
            # Try to get metrics from /metrics endpoint
            curl -s "https://$APP_NAME.fly.dev/metrics" || log "Failed to get metrics from /metrics endpoint"
        else
            log "curl not available"
        fi
        echo ""
        
        log "Fly.io CPU and Memory:"
        flyctl vm status --app $APP_NAME --details | grep -E "(CPU|Memory)" || log "No VM details available"
        echo ""
        
        log "========================================="
        sleep $INTERVAL
    done
    
    log "Monitoring complete!"
    log "Final instance status: $(get_instances)"
}

# Handle script interruption
trap 'log "Monitoring interrupted"; exit 1' INT

main
