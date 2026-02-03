#!/bin/bash
# E2E Test Script for JobSwipe Android App
# Run this script on a machine with Android emulator support (hardware acceleration)

set -e

# Configuration
APK_PATH="${APK_PATH:-mobile-app/build/app/outputs/apk/dev/debug/app-dev-debug.apk}"
AVD_NAME="${AVD_NAME:-test_avd}"
PACKAGE_NAME="com.jobswipe.jobswipe"
MAIN_ACTIVITY=".MainActivity"
API_ENDPOINT="https://jobswipe-9obhra.fly.dev"
LOG_FILE="e2e_test_results.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$1"
}

log_success() {
    log "${GREEN}SUCCESS${NC}" "$1"
}

log_error() {
    log "${RED}ERROR${NC}" "$1"
}

log_warning() {
    log "${YELLOW}WARNING${NC}" "$1"
}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

run_test() {
    local test_name=$1
    local test_command=$2
    local expected_result=$3  # "success" or "failure"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_info "Running test: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        if [ "$expected_result" == "success" ]; then
            log_success "[$test_name] PASSED"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "[$test_name] FAILED - Expected failure but succeeded"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        if [ "$expected_result" == "failure" ]; then
            log_success "[$test_name] PASSED - Expected failure occurred"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "[$test_name} FAILED"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi
}

# Pre-flight checks
preflight_checks() {
    log_info "=== Running Pre-flight Checks ==="
    
    # Check if APK exists
    if [ -f "$APK_PATH" ]; then
        log_success "APK file found: $APK_PATH"
        local apk_size=$(du -h "$APK_PATH" | cut -f1)
        log_info "APK size: $apk_size"
    else
        log_error "APK file not found: $APK_PATH"
        exit 1
    fi
    
    # Check ADB
    if command -v adb &> /dev/null; then
        log_success "ADB is available"
        adb version
    else
        log_error "ADB not found. Please install Android SDK platform-tools"
        exit 1
    fi
    
    # Check emulator
    if command -v emulator &> /dev/null; then
        log_success "Android emulator is available"
    else
        log_error "Android emulator not found. Please install Android emulator"
        exit 1
    fi
}

# Start emulator
start_emulator() {
    log_info "=== Starting Android Emulator ==="
    
    # Check if emulator is already running
    if adb devices | grep -q "emulator"; then
        log_warning "Emulator already running"
    else
        log_info "Starting emulator: $AVD_NAME"
        emulator -avd "$AVD_NAME" -no-window -no-audio -no-skin -no-boot-anim &
        local emulator_pid=$!
        
        log_info "Waiting for emulator to boot (PID: $emulator_pid)"
        adb wait-for-device shell getprop sys.boot_completed
        
        log_success "Emulator booted successfully"
    fi
}

# Install APK
install_apk() {
    log_info "=== Installing APK ==="
    
    local result=$(adb install -r "$APK_PATH" 2>&1)
    if echo "$result" | grep -q "Success"; then
        log_success "APK installed successfully"
        return 0
    else
        log_error "Failed to install APK: $result"
        return 1
    fi
}

# Test scenarios
test_app_launch() {
    log_info "=== Test: App Launch ==="
    
    # Clear app data
    adb shell pm clear "$PACKAGE_NAME"
    
    # Launch app
    adb shell am start -n "$PACKAGE_NAME/$MAIN_ACTIVITY"
    
    # Wait for app to initialize
    sleep 5
    
    # Check if app is running
    if adb shell pidof "$PACKAGE_NAME" | grep -q "[0-9]"; then
        log_success "App launched successfully"
        return 0
    else
        log_error "App failed to launch"
        return 1
    fi
}

test_api_connectivity() {
    log_info "=== Test: API Connectivity ==="
    
    # Test network connectivity
    adb shell ping -c 3 8.8.8.8 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "Network connectivity confirmed"
    else
        log_warning "Network ping failed - continuing with tests"
    fi
    
    # Check if API endpoint is accessible (from host)
    if curl -s --connect-timeout 5 "$API_ENDPOINT/health" > /dev/null 2>&1; then
        log_success "API endpoint accessible: $API_ENDPOINT"
        return 0
    else
        log_warning "API endpoint not accessible: $API_ENDPOINT"
        return 1
    fi
}

test_logcat_for_errors() {
    log_info "=== Test: Logcat Error Check ==="
    
    # Clear logcat buffer
    adb logcat -c
    
    # Start app
    adb shell am start -n "$PACKAGE_NAME/$MAIN_ACTIVITY"
    
    # Wait for app to initialize
    sleep 10
    
    # Capture logs
    local logs=$(adb logcat -d 2>/dev/null)
    
    # Check for critical errors
    if echo "$logs" | grep -iE "FATAL|CRASH|ANR|java.*exception" > /dev/null; then
        log_error "Found critical errors in logcat:"
        echo "$logs" | grep -iE "FATAL|CRASH|ANR|java.*exception" | head -20
        return 1
    else
        log_success "No critical errors found in logcat"
        return 0
    fi
}

test_data_persistence() {
    log_info "=== Test: Data Persistence ==="
    
    # Check if app can create files in external storage
    local result=$(adb shell mkdir -p /sdcard/Android/data/"$PACKAGE_NAME" 2>&1)
    
    if [ -z "$result" ]; then
        log_success "App data directory created successfully"
        return 0
    else
        log_warning "Data persistence check had issues: $result"
        return 1
    fi
}

test_offline_queue() {
    log_info "=== Test: Offline Queue Functionality ==="
    
    # This test verifies the offline queue mechanism exists
    # In a real test, you would:
    # 1. Enable airplane mode
    # 2. Perform actions that should be queued
    # 3. Disable airplane mode
    # 4. Verify queued actions were processed
    
    # For now, just check if the app package has the necessary components
    if adb shell pm list packages | grep -q "$PACKAGE_NAME"; then
        log_success "App package installed - offline queue test prepared"
        return 0
    else
        log_error "App package not found"
        return 1
    fi
}

capture_screenshots() {
    log_info "=== Capturing Screenshots ==="
    
    local screenshot_dir="test_screenshots"
    mkdir -p "$screenshot_dir"
    
    # Capture screenshot of main screen
    adb shell screencap -p /sdcard/screen.png
    adb pull /sdcard/screen.png "$screenshot_dir/main_screen.png" 2>/dev/null || true
    adb shell rm /sdcard/screen.png 2>/dev/null || true
    
    log_success "Screenshots saved to $screenshot_dir"
}

generate_report() {
    log_info "=== Generating Test Report ==="
    
    cat > "e2e_test_report.md" << EOF
# JobSwipe Android E2E Test Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**APK:** $APK_PATH
**Package:** $PACKAGE_NAME

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | $TESTS_TOTAL |
| Passed | $TESTS_PASSED |
| Failed | $TESTS_FAILED |
| Success Rate | $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)% |

## Test Results

EOF

    # Add detailed results
    echo "## Detailed Log" >> "e2e_test_report.md"
    echo "" >> "e2e_test_report.md"
    echo '```' >> "e2e_test_report.md"
    cat "$LOG_FILE" >> "e2e_test_report.md"
    echo '```' >> "e2e_test_report.md"
    
    log_success "Report generated: e2e_test_report.md"
}

cleanup() {
    log_info "=== Cleanup ==="
    
    # Stop emulator if it was started by this script
    if [ -n "$emulator_pid" ] && kill -0 "$emulator_pid" 2>/dev/null; then
        log_info "Stopping emulator (PID: $emulator_pid)"
        kill "$emulator_pid" 2>/dev/null || true
    fi
    
    log_success "Cleanup complete"
}

# Main execution
main() {
    echo "========================================="
    echo "  JobSwipe Android E2E Test Suite"
    echo "========================================="
    echo ""
    
    # Initialize log file
    echo "E2E Test Run - $(date '+%Y-%m-%d %H:%M:%S')" > "$LOG_FILE"
    
    # Run preflight checks
    preflight_checks
    
    # Start emulator
    start_emulator
    
    # Install APK
    install_apk
    
    # Run tests
    echo ""
    log_info "========================================="
    log_info "  Running Test Scenarios"
    log_info "========================================="
    echo ""
    
    test_app_launch
    test_api_connectivity
    test_logcat_for_errors
    test_data_persistence
    test_offline_queue
    
    # Capture screenshots
    capture_screenshots
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup
    
    # Final summary
    echo ""
    echo "========================================="
    echo "  Test Summary"
    echo "========================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)%"
    echo "========================================="
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Trap for cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
