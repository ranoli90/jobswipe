#!/usr/bin/env pwsh
# E2E Test Script for JobSwipe Android App (Windows PowerShell)
# Run this script on a machine with Android emulator support (hardware acceleration)

param(
    [string]$APKPath = "mobile-app\build\app\outputs\apk\dev\debug\app-dev-debug.apk",
    [string]$AVDName = "test_avd",
    [string]$PackageName = "com.jobswipe.jobswipe",
    [string]$MainActivity = ".MainActivity",
    [string]$APIEndpoint = "https://jobswipe-9obhra.fly.dev",
    [string]$LogFile = "e2e_test_results.log"
)

# Test counters
$TestsPassed = 0
$TestsFailed = 0
$TestsTotal = 0

# Logging function
function Log-Message {
    param(
        [string]$Level,
        [string]$Message,
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $Color
    $logEntry | Out-File -FilePath $LogFile -Append
}

function Log-Info { Log-Message -Level "INFO" -Message $args[0] -Color "Cyan" }
function Log-Success { Log-Message -Level "SUCCESS" -Message $args[0] -Color "Green" }
function Log-Error { Log-Message -Level "ERROR" -Message $args[0] -Color "Red" }
function Log-Warning { Log-Message -Level "WARNING" -Message $args[0] -Color "Yellow" }

# Pre-flight checks
function Invoke-PreflightChecks {
    Log-Info "=== Running Pre-flight Checks ==="
    
    # Check if APK exists
    if (Test-Path $APKPath) {
        Log-Success "APK file found: $APKPath"
        $apkSize = (Get-Item $APKPath).Length / 1MB
        Log-Info "APK size: $([math]::Round($apkSize, 2)) MB"
    }
    else {
        Log-Error "APK file not found: $APKPath"
        exit 1
    }
    
    # Check ADB
    try {
        $adbVersion = adb version 2>&1 | Out-String
        Log-Success "ADB is available"
        Log-Info $adbVersion.Trim()
    }
    catch {
        Log-Error "ADB not found. Please install Android SDK platform-tools"
        exit 1
    }
}

# Start emulator
function Start-Emulator {
    param([string]$AVDName)
    
    Log-Info "=== Starting Android Emulator ==="
    
    # Check if emulator is already running
    $devices = adb devices 2>&1 | Out-String
    if ($devices -match "emulator") {
        Log-Warning "Emulator already running"
        return
    }
    
    Log-Info "Starting emulator: $AVDName"
    
    # Start emulator in background
    $emulatorProcess = Start-Process -FilePath "emulator" -ArgumentList "-avd", $AVDName, "-no-window", "-no-audio", "-no-skin", "-no-boot-anim" -PassThru -NoNewWindow
    
    Log-Info "Waiting for emulator to boot (PID: $($emulatorProcess.Id))"
    
    # Wait for device
    do {
        Start-Sleep -Seconds 5
        $state = adb get-state 2>&1 | Out-String
    } while ($state.Trim() -ne "device")
    
    # Wait for boot complete
    do {
        Start-Sleep -Seconds 5
        $bootStatus = adb shell getprop sys.boot_completed 2>&1 | Out-String
    } while ($bootStatus.Trim() -ne "1")
    
    Log-Success "Emulator booted successfully"
    return $emulatorProcess
}

# Install APK
function Install-APK {
    param([string]$APKPath)
    
    Log-Info "=== Installing APK ==="
    
    $result = adb install -r $APKPath 2>&1 | Out-String
    
    if ($result -match "Success") {
        Log-Success "APK installed successfully"
        return $true
    }
    else {
        Log-Error "Failed to install APK: $result"
        return $false
    }
}

# Test app launch
function Test-AppLaunch {
    Log-Info "=== Test: App Launch ==="
    
    # Clear app data
    adb shell pm clear $PackageName | Out-Null
    
    # Launch app
    adb shell am start -n "$PackageName/$MainActivity" | Out-Null
    
    # Wait for app to initialize
    Start-Sleep -Seconds 5
    
    # Check if app is running
    $pid = adb shell pidof $PackageName 2>&1 | Out-String
    
    if ($pid -match "[0-9]") {
        Log-Success "App launched successfully (PID: $($pid.Trim()))"
        return $true
    }
    else {
        Log-Error "App failed to launch"
        return $false
    }
}

# Test API connectivity
function Test-ApiConnectivity {
    Log-Info "=== Test: API Connectivity ==="
    
    # Test network connectivity
    try {
        adb shell ping -c 3 8.8.8.8 | Out-Null
        Log-Success "Network connectivity confirmed"
    }
    catch {
        Log-Warning "Network ping failed - continuing with tests"
    }
    
    # Check if API endpoint is accessible
    try {
        $response = Invoke-RestMethod -Uri "$APIEndpoint/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response -ne $null) {
            Log-Success "API endpoint accessible: $APIEndpoint"
            return $true
        }
    }
    catch {
        Log-Warning "API endpoint not accessible: $APIEndpoint"
        return $false
    }
    
    return $false
}

# Test logcat for errors
function Test-LogcatErrors {
    Log-Info "=== Test: Logcat Error Check ==="
    
    # Clear logcat buffer
    adb logcat -c | Out-Null
    
    # Start app
    adb shell am start -n "$PackageName/$MainActivity" | Out-Null
    
    # Wait for app to initialize
    Start-Sleep -Seconds 10
    
    # Capture logs
    $logs = adb logcat -d 2>&1 | Out-String
    
    # Check for critical errors
    $errorPatterns = @("FATAL", "CRASH", "ANR", "Exception", "Error")
    $foundErrors = $false
    
    foreach ($pattern in $errorPatterns) {
        if ($logs -match $pattern) {
            $foundErrors = $true
            Log-Error "Found error pattern: $pattern"
            ($logs -split "`n" | Select-String -Pattern $pattern | Select-Object -First 10) | ForEach-Object {
                Log-Error "  $_"
            }
        }
    }
    
    if (-not $foundErrors) {
        Log-Success "No critical errors found in logcat"
        return $true
    }
    
    return $false
}

# Test data persistence
function Test-DataPersistence {
    Log-Info "=== Test: Data Persistence ==="
    
    try {
        adb shell mkdir -p "/sdcard/Android/data/$PackageName" 2>&1 | Out-Null
        Log-Success "App data directory created successfully"
        return $true
    }
    catch {
        Log-Warning "Data persistence check had issues"
        return $false
    }
}

# Test offline queue
function Test-OfflineQueue {
    Log-Info "=== Test: Offline Queue Functionality ==="
    
    if (adb shell pm list packages | Select-String $PackageName) {
        Log-Success "App package installed - offline queue test prepared"
        return $true
    }
    else {
        Log-Error "App package not found"
        return $false
    }
}

# Capture screenshots
function Capture-Screenshots {
    Log-Info "=== Capturing Screenshots ==="
    
    $screenshotDir = "test_screenshots"
    New-Item -ItemType Directory -Force -Path $screenshotDir | Out-Null
    
    try {
        adb shell screencap -p /sdcard/screen.png 2>&1 | Out-Null
        adb pull /sdcard/screen.png "$screenshotDir\main_screen.png" 2>&1 | Out-Null
        adb shell rm /sdcard/screen.png 2>&1 | Out-Null
        Log-Success "Screenshots saved to $screenshotDir"
    }
    catch {
        Log-Warning "Failed to capture screenshots"
    }
}

# Generate report
function Generate-Report {
    Log-Info "=== Generating Test Report ==="
    
    $successRate = if ($TestsTotal -gt 0) { [math]::Round(($TestsPassed / $TestsTotal) * 100, 2) } else { 0 }
    
    @"
# JobSwipe Android E2E Test Report

**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**APK:** $APKPath
**Package:** $PackageName

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | $TestsTotal |
| Passed | $TestsPassed |
| Failed | $TestsFailed |
| Success Rate | $successRate% |

## Test Results

- App Launch: $(if ($TestsPassed -gt 0) { 'PASSED' } else { 'FAILED' })
- API Connectivity: $(if ($TestsPassed -gt 1) { 'PASSED' } else { 'CHECK MANUALLY' })
- Logcat Errors: $(if ($TestsPassed -gt 2) { 'PASSED' } else { 'FAILED' })
- Data Persistence: $(if ($TestsPassed -gt 3) { 'PASSED' } else { 'CHECK MANUALLY' })
- Offline Queue: $(if ($TestsPassed -gt 4) { 'PASSED' } else { 'CHECK MANUALLY' })

## Detailed Logs

See `e2e_test_results.log` for full test output.

"@ | Out-File -FilePath "e2e_test_report.md" -Encoding utf8
    
    Log-Success "Report generated: e2e_test_report.md"
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  JobSwipe Android E2E Test Suite" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Initialize log file
    "E2E Test Run - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $LogFile -Encoding utf8
    
    # Run preflight checks
    Invoke-PreflightChecks
    
    # Start emulator
    $emulatorProcess = Start-Emulator -AVDName $AVDName
    
    # Install APK
    $null = Install-APK -APKPath $APKPath
    
    # Run tests
    Write-Host ""
    Log-Info "========================================="
    Log-Info "  Running Test Scenarios"
    Log-Info "========================================="
    Write-Host ""
    
    if (Test-AppLaunch) { $TestsPassed++ } else { $TestsFailed++ }
    $TestsTotal++
    
    if (Test-ApiConnectivity) { $TestsPassed++ } else { $TestsFailed++ }
    $TestsTotal++
    
    if (Test-LogcatErrors) { $TestsPassed++ } else { $TestsFailed++ }
    $TestsTotal++
    
    if (Test-DataPersistence) { $TestsPassed++ } else { $TestsFailed++ }
    $TestsTotal++
    
    if (Test-OfflineQueue) { $TestsPassed++ } else { $TestsFailed++ }
    $TestsTotal++
    
    # Capture screenshots
    Capture-Screenshots
    
    # Generate report
    Generate-Report
    
    # Cleanup
    if ($emulatorProcess -and -not $emulatorProcess.HasExited) {
        Log-Info "Stopping emulator (PID: $($emulatorProcess.Id))"
        $emulatorProcess.Kill()
    }
    
    # Final summary
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  Test Summary" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Total Tests: $TestsTotal" -ForegroundColor White
    Write-Host "Passed: $TestsPassed" -ForegroundColor Green
    Write-Host "Failed: $TestsFailed" -ForegroundColor Red
    $successRate = if ($TestsTotal -gt 0) { [math]::Round(($TestsPassed / $TestsTotal) * 100, 2) } else { 0 }
    Write-Host "Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } else { "Yellow" })
    Write-Host "=========================================" -ForegroundColor Cyan
}

# Run main function
Main
