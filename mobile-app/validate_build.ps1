<#
.SYNOPSIS
    Validates the JobSwipe Flutter Android build environment and attempts a debug build.
.DESCRIPTION
    This script runs a series of validation steps to ensure the build environment
    is properly configured before attempting to build the Android app.
.PARAMETER Flavor
    The build flavor to use (dev, staging, prod). Default is 'dev'.
.PARAMETER SkipClean
    Skips the flutter clean step.
.PARAMETER SkipTests
    Skips running flutter test.
.EXAMPLE
    .\validate_build.ps1
    Runs full validation with dev flavor.
.EXAMPLE
    .\validate_build.ps1 -Flavor staging -SkipTests
    Runs validation for staging flavor without tests.
#>

param(
    [string]$Flavor = "dev",
    [switch]$SkipClean,
    [switch]$SkipTests,
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# Color codes for output
$GREEN = "[32m"
$RED = "[31m"
$YELLOW = "[33m"
$BLUE = "[34m"
$RESET = "[0m"

# Track overall status
$global:stepPassed = $true
$script:stepsPassed = 0
$script:stepsFailed = 0

function Write-Step {
    param([string]$Message)
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
    $script:stepsPassed++
}

function Write-Failure {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:stepsFailed++
    $global:stepPassed = $false
}

function Write-Warning {
    param([string]$Message)
    Write-Host "! $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Blue
}

function Step-Completed {
    param([string]$StepName)
    Write-Success "$StepName completed successfully"
}

function Step-Failed {
    param([string]$StepName, [string]$Error)
    Write-Failure "$StepName failed"
    Write-Host "  Error: $Error" -ForegroundColor Red
}

# Banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║         JobSwipe Flutter Android Build Validation Script          ║" -ForegroundColor Magenta
Write-Host "║                      Phase 5 - Android Stabilization               ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Info "Target Flavor: $Flavor"
Write-Info "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# ============================================================================
# STEP 1: Verify Flutter Installation
# ============================================================================
Write-Step "STEP 1: Verifying Flutter Installation"

try {
    $flutterVersion = flutter --version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Step-Completed "Flutter installation"
        Write-Host "  Version: $flutterVersion" -ForegroundColor White
    } else {
        Step-Failed "Flutter installation" "flutter command not found or failed"
        exit 1
    }
} catch {
    Step-Failed "Flutter installation" $_.Exception.Message
    exit 1
}

# ============================================================================
# STEP 2: Verify Java Installation
# ============================================================================
Write-Step "STEP 2: Verifying Java Installation"

try {
    $javaVersion = java -version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        # Check for Java 17
        if ($javaVersion -match "version ""17") {
            Step-Completed "Java 17 installation"
            Write-Host "  $javaVersion" -ForegroundColor White
        } else {
            Write-Warning "Java 17 not detected. Gradle 8.x requires Java 17."
            Write-Host "  $javaVersion" -ForegroundColor White
            Step-Failed "Java 17 requirement" "Java version mismatch"
        }
    } else {
        Step-Failed "Java installation" "java command not found"
        exit 1
    }
} catch {
    Step-Failed "Java installation" $_.Exception.Message
    exit 1
}

# ============================================================================
# STEP 3: Verify Android SDK
# ============================================================================
Write-Step "STEP 3: Verifying Android SDK"

try {
    # Check ANDROID_HOME
    if ([string]::IsNullOrEmpty($env:ANDROID_HOME)) {
        Step-Failed "ANDROID_HOME environment variable" "ANDROID_HOME is not set"
    } else {
        Step-Completed "ANDROID_HOME environment variable"
        Write-Host "  Path: $env:ANDROID_HOME" -ForegroundColor White
    }

    # Check SDK components
    $sdkManager = "$env:ANDROID_HOME\cmdline-tools\latest\bin\sdkmanager.bat"
    if (Test-Path $sdkManager) {
        Step-Completed "SDK Manager found"
        
        # List installed packages
        Write-Info "Checking installed SDK components..."
        try {
            $packages = & $sdkManager --list_installed 2>&1 | Out-String
            if ($packages -match "platforms;android-36") {
                Write-Host "  ✓ Android API 36 installed" -ForegroundColor Green
            } else {
                Write-Warning "Android API 36 may not be installed"
            }
            if ($packages -match "build-tools") {
                Write-Host "  ✓ Build tools installed" -ForegroundColor Green
            }
        } catch {
            Write-Warning "Could not list installed packages"
        }
    } else {
        Step-Failed "SDK Manager" "SDK Manager not found at $sdkManager"
    }
} catch {
    Step-Failed "Android SDK verification" $_.Exception.Message
}

# ============================================================================
# STEP 4: Navigate to Project Directory
# ============================================================================
Write-Step "STEP 4: Navigating to Project Directory"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$mobileAppPath = Join-Path $projectRoot "mobile-app"

if (Test-Path $mobileAppPath) {
    Step-Completed "Project directory found"
    Write-Host "  Path: $mobileAppPath" -ForegroundColor White
    Push-Location $mobileAppPath
} else {
    Step-Failed "Project directory" "mobile-app directory not found at $mobileAppPath"
    exit 1
}

# ============================================================================
# STEP 5: Flutter Clean
# ============================================================================
if (-not $SkipClean) {
    Write-Step "STEP 5: Running Flutter Clean"
    
    try {
        $cleanOutput = flutter clean 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            Step-Completed "Flutter clean"
        } else {
            Step-Failed "Flutter clean" $cleanOutput
        }
    } catch {
        Step-Failed "Flutter clean" $_.Exception.Message
    }
} else {
    Write-Step "STEP 5: Skipping Flutter Clean (--SkipClean specified)"
}

# ============================================================================
# STEP 6: Get Dependencies
# ============================================================================
Write-Step "STEP 6: Getting Flutter Dependencies"

try {
    $pubGetOutput = flutter pub get 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Step-Completed "Flutter pub get"
    } else {
        Step-Failed "Flutter pub get" $pubGetOutput
    }
} catch {
    Step-Failed "Flutter pub get" $_.Exception.Message
}

# ============================================================================
# STEP 7: Run Flutter Analyze
# ============================================================================
Write-Step "STEP 7: Running Flutter Analyze"

try {
    $analyzeOutput = flutter analyze 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Step-Completed "Flutter analyze"
        # Show summary if available
        $analyzeLines = $analyzeOutput -split "`n"
        foreach ($line in $analyzeLines) {
            if ($line -match "issue|s found|No issues") {
                Write-Host "  $line" -ForegroundColor White
            }
        }
    } else {
        Step-Failed "Flutter analyze" $analyzeOutput
    }
} catch {
    Step-Failed "Flutter analyze" $_.Exception.Message
}

# ============================================================================
# STEP 8: Run Flutter Test (if tests exist)
# ============================================================================
if (-not $SkipTests) {
    Write-Step "STEP 8: Running Flutter Tests"
    
    $testDir = Join-Path $mobileAppPath "test"
    if (Test-Path $testDir) {
        try {
            $testOutput = flutter test 2>&1 | Out-String
            if ($LASTEXITCODE -eq 0) {
                Step-Completed "Flutter test"
                # Show test results summary
                $testLines = $testOutput -split "`n"
                foreach ($line in $testLines) {
                    if ($line -match "All tests passed|Running|Unittest") {
                        Write-Host "  $line" -ForegroundColor White
                    }
                }
            } else {
                Step-Failed "Flutter test" $testOutput
            }
        } catch {
            Step-Failed "Flutter test" $_.Exception.Message
        }
    } else {
        Write-Warning "Test directory not found, skipping tests"
    }
} else {
    Write-Step "STEP 8: Skipping Flutter Tests (--SkipTests specified)"
}

# ============================================================================
# STEP 9: Attempt Debug Build for Specified Flavor
# ============================================================================
Write-Step "STEP 9: Attempting Debug Build for '$Flavor' Flavor"

$validFlavors = @("dev", "staging", "prod")
if ($Flavor -notin $validFlavors) {
    Step-Failed "Build flavor" "Invalid flavor '$Flavor'. Valid flavors: $($validFlavors -join ', ')"
} else {
    try {
        Write-Info "Building APK with: flutter build apk --debug --flavor $Flavor -t lib/main.dart"
        $buildOutput = flutter build apk --debug --flavor $Flavor -t lib/main.dart 2>&1 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            Step-Completed "Debug build for '$Flavor' flavor"
            
            # Show build output location
            $apkPath = Join-Path $mobileAppPath "build\app\outputs\flutter-apk"
            if (Test-Path $apkPath) {
                Write-Host "  Build artifacts:" -ForegroundColor White
                Get-ChildItem $apkPath -Filter "*.apk" | ForEach-Object {
                    Write-Host "    $($_.FullName)" -ForegroundColor DarkCyan
                    Write-Host "    Size: $([math]::Round($_.Length / 1MB, 2)) MB" -ForegroundColor DarkGray
                }
            }
        } else {
            Step-Failed "Debug build for '$Flavor' flavor" $buildOutput
        }
    } catch {
        Step-Failed "Debug build" $_.Exception.Message
    }
}

# Restore original directory
Pop-Location

# ============================================================================
# Summary
# ============================================================================
Write-Step "VALIDATION SUMMARY"

Write-Host ""
Write-Host "  Steps Passed: $script:stepsPassed" -ForegroundColor $(if ($script:stepsPassed -gt 0) { "Green" } else { "White" })
Write-Host "  Steps Failed: $script:stepsFailed" -ForegroundColor $(if ($script:stepsFailed -gt 0) { "Red" } else { "White" })
Write-Host ""

if ($script:stepsFailed -eq 0) {
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                    VALIDATION PASSED ✓                             ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  The build environment is properly configured." -ForegroundColor White
    Write-Host "  You can now proceed with release builds or further development." -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                    VALIDATION FAILED ✗                             ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please fix the failed steps before attempting to build." -ForegroundColor White
    Write-Host "  Refer to DEPLOYMENT_README.md for troubleshooting guidance." -ForegroundColor White
    Write-Host ""
    exit 1
}
