#!/bin/bash

# Real-time monitoring script for Jobswipe API load testing
# Monitors Fly.io scaling events and system metrics

set -o pipefail

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

# Dependency check
if ! command -v flyctl &> /dev/null; then
    echo "Error: flyctl could not be found. Please install the Fly.io CLI." >&2
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq could not be found. Please install jq." >&2
    exit 1
fi

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
    flyctl status --app "$APP_NAME" | grep -E "(v[0-9]+:|   [0-9] instances)"
}

# Function to check if app is running
check_app_running() {
    if ! flyctl status --app "$APP_NAME" >/dev/null 2>&1; then
        log "Error: App $APP_NAME is not running or accessible."
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
    
    log "Initial instances:"
    get_instances
    log "========================================="
    
    start_time=$(date +%s)
    end_time=$((start_time + DURATION))
    
    while [ $(date +%s) -lt $end_time ]; do
        # Get instance count and list
        log "Instance status:"
        instances=$(get_instances)
        echo "$instances"
        echo ""
        
        # Get metrics
        log "Application metrics (from /metrics endpoint):"
        metrics_url="https://$APP_NAME.fly.dev/metrics"
        if curl -s --fail "$metrics_url"; then
            echo ""
        else
            log "Failed to get metrics from $metrics_url"
        fi
        echo ""
        
        log "Fly.io VM Metrics (CPU and Memory):"
        vm_statuses=$(flyctl vm status --app "$APP_NAME" --json)
        if [ -n "$vm_statuses" ] && [ "$vm_statuses" != "[]" ]; then
            echo "$vm_statuses" | jq -r '.[] | "  VM: \(.id) | CPU: \(.cpu_count) | Memory: \(.memory_mb)MB"'
        else
            log "No VM details available or empty response."
        fi
        echo ""
        
        log "========================================="
        sleep "$INTERVAL"
    done
    
    log "Monitoring complete!"
    log "Final instance status:"
    get_instances
}

# Handle script interruption
trap '{ log "Monitoring interrupted"; exit 1; }' INT

main
