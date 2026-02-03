# Flutter Web Debugger

A comprehensive Playwright-based debugging tool for diagnosing blank screen issues in Flutter web applications deployed on Fly.io.

## Overview

This debugging script helps identify why a Flutter web application might be showing a blank screen by:

- **Visual Inspection**: Launches Chrome in headful mode for real-time observation
- **Screenshots**: Captures screenshots at multiple stages of page load
- **Console Logging**: Records all console messages with types (error, warning, info)
- **Network Monitoring**: Captures all network requests and responses
- **API Health Checks**: Tests backend API endpoints
- **DOM Analysis**: Inspects DOM structure to identify rendering issues
- **Flutter-Specific Checks**: Detects Flutter engine initialization problems
- **Detailed Reports**: Generates both JSON and HTML debug reports

## Requirements

- Python 3.8+
- Playwright (`pip install playwright`)
- Chromium browser (`playwright install chromium`)

## Installation

1. Install Python dependencies:
```bash
pip install playwright
playwright install chromium
```

Or use the requirements file:
```bash
pip install -r scripts/requirements_debug.txt
```

2. (Optional) Make the launcher script executable:
```bash
chmod +x scripts/run_flutter_debug.sh
```

## Usage

### Command Line

```bash
# Run with default settings (headful Chrome)
python scripts/flutter_web_debug.py

# Run with custom URL
python scripts/flutter_web_debug.py --url https://your-app.fly.dev

# Run in headless mode
python scripts/flutter_web_debug.py --headless

# Custom output directory and timeout
python scripts/flutter_web_debug.py --output ./my_debug_output --timeout 120000
```

### Shell Script (Linux/macOS)

```bash
# Run with default settings
./scripts/run_flutter_debug.sh

# Run with custom URL
./scripts/run_flutter_debug.sh --url https://jobswipe-9obhra.fly.dev

# Run in headless mode
./scripts/run_flutter_debug.sh --headless
```

### PowerShell (Windows)

```powershell
# Run with default settings
.\scripts\run_flutter_debug.ps1

# Run with custom URL
.\scripts\run_flutter_debug.ps1 --url https://jobswipe-9obhra.fly.dev

# Run in headless mode
.\scripts\run_flutter_debug.ps1 --headless
```

## Output

The debugger creates the following output in the specified directory:

```
debug_output/
├── screenshots/
│   ├── 01_initial_load.png
│   ├── 02_dom_ready.png
│   ├── 03_network_idle.png
│   ├── 04_flutter_rendered.png
│   └── 05_final_state.png
├── debug_report.json     # Detailed JSON report
└── debug_report.html     # Human-readable HTML report
```

### Debug Report Contents

The debug report includes:

1. **Session Info**: URL, timestamps, output directory
2. **Timeline**: Chronological list of events
3. **Screenshots**: All captured screenshots with timestamps
4. **Console Logs**: All console messages separated by type
5. **JavaScript Errors**: Detailed error information
6. **Network Activity**: All HTTP requests and responses
7. **DOM Snapshot**: Page structure and content analysis
8. **Flutter Status**: Engine initialization and rendering status
9. **Issues Analysis**: Critical issues, warnings, and info messages

## Flutter-Specific Checks

The debugger performs several Flutter-specific checks:

- **Flutter Engine Detection**: Checks for `flt-glass-pane`, `flt-scene`, `flutter-view`
- **Loading State**: Monitors loading indicators and error elements
- **Widget Count**: Approximate count of rendered Flutter widgets
- **Service Worker**: Checks service worker readiness
- **Engine Version**: Reports Flutter engine version if available

## Common Blank Screen Causes

The debugger helps identify these common issues:

1. **JavaScript Errors**: Syntax errors, runtime errors
2. **Network Failures**: Failed to load Flutter assets, API errors
3. **CORS Issues**: Cross-origin resource sharing problems
4. **Flutter Engine**: Engine initialization failures
5. **Asset Loading**: Missing or corrupted Flutter assets
6. **API Failures**: Backend API not responding
7. **Rendering Issues**: Flutter widgets not rendering

## Configuration

### Environment Variables

You can also use environment variables:

```bash
export FLUTTER_WEB_URL="https://jobswipe-9obhra.fly.dev"
export DEBUG_OUTPUT_DIR="./debug_output"
export DEBUG_TIMEOUT=60000
```

### Programmatic Usage

```python
import asyncio
from flutter_web_debug import FlutterWebDebugger

async def main():
    debugger = FlutterWebDebugger(
        app_url="https://jobswipe-9obhra.fly.dev",
        output_dir="./debug_output",
        timeout=60000,
        headless=False,
    )
    
    summary = await debugger.debug_session()
    print(f"Critical issues: {summary['critical_issues']}")

asyncio.run(main())
```

## Backend API Configuration

The debugger checks the following backend endpoints:

- **Health Check**: `https://jobswipe-9obhra.fly.dev/health`
- **API Base URL**: `https://jobswipe-9obhra.fly.dev`

Configure additional endpoints in the script if needed.

## Troubleshooting

### Playwright Not Installed

```bash
pip install playwright
playwright install chromium
```

### Chromium Not Found

```bash
playwright install chromium
```

### Permission Errors (Linux)

```bash
sudo apt-get install chromium-browser
# or
playwright install --with-deps chromium
```

### Timeout Issues

Increase the timeout value:
```bash
python scripts/flutter_web_debug.py --timeout 120000
```

## Report Analysis

### Critical Issues (Red)

These require immediate attention:
- JavaScript errors
- Console errors
- Missing Flutter engine elements
- Failed network requests
- Page appears blank

### Warnings (Yellow)

These may indicate problems:
- Slow network requests
- API response delays
- Non-critical console warnings

### Info (Blue)

Informational messages:
- Page content analysis
- Network activity summary
- Flutter status details

## Files Created

| File | Description |
|------|-------------|
| [`scripts/flutter_web_debug.py`](scripts/flutter_web_debug.py) | Main Playwright debugging script |
| [`scripts/requirements_debug.txt`](scripts/requirements_debug.txt) | Python dependencies |
| [`scripts/run_flutter_debug.sh`](scripts/run_flutter_debug.sh) | Shell launcher script |
| [`scripts/run_flutter_debug.ps1`](scripts/run_flutter_debug.ps1) | PowerShell launcher script |

## Fly.io Configuration

The Flutter web app is deployed on Fly.io with:
- **App Name**: `jobswipe-9obhra`
- **Primary Region**: `iad` (Washington, D.C.)
- **Backend Health Check**: `/health`
- **API Base URL**: `https://jobswipe-9obhra.fly.dev`

For more details on the deployment configuration, see:
- [`backend/fly.toml`](backend/fly.toml) - Backend API configuration
- [`mobile-app/web/`](mobile-app/web/) - Flutter web assets

## License

This tool is provided as-is for debugging purposes.
