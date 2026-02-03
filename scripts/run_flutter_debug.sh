#!/bin/bash
#
# Flutter Web Debugger - Shell Launcher
#
# Usage: ./scripts/run_flutter_debug.sh [--url URL] [--output DIR] [--timeout MS] [--headless]
#

set -e

# Default values
URL="https://jobswipe-9obhra.fly.dev"
OUTPUT_DIR="./debug_output"
TIMEOUT=60000
HEADLESS=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--headless)
            HEADLESS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Flutter Web Debugger Usage:"
            echo "  -u, --url URL       Target Flutter web app URL"
            echo "  -o, --output DIR    Output directory for debug artifacts"
            echo "  -t, --timeout MS    Timeout in milliseconds"
            echo "  -h, --headless      Run in headless mode"
            echo "  -v, --verbose       Verbose output"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Flutter Web Debugger${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "Target URL: $URL"
echo "Output Directory: $OUTPUT_DIR"
echo "Timeout: $TIMEOUT ms"
echo "Headless: $HEADLESS"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed or not in PATH${NC}"
    exit 1
fi

echo "Python Version: $(python --version)"

# Check if Playwright is installed
if ! python -c "import playwright" &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright...${NC}"
    pip install -r scripts/requirements_debug.txt
fi

# Install Playwright browsers if needed
if ! python -c "import playwright" &> /dev/null || ! playwright --version &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    playwright install chromium
fi

# Run the debugger
echo ""
echo -e "${GREEN}Starting debugging session...${NC}"
echo ""

PYTHON_ARGS=(
    "scripts/flutter_web_debug.py"
    "--url" "$URL"
    "--output" "$OUTPUT_DIR"
    "--timeout" "$TIMEOUT"
)

if [ "$HEADLESS" = true ]; then
    PYTHON_ARGS+=("--headless")
fi

if [ "$VERBOSE" = true ]; then
    PYTHON_ARGS+=("--verbose")
fi

python "${PYTHON_ARGS[@]}"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}Debugging session completed successfully!${NC}"
else
    echo -e "${RED}Debugging session failed with exit code: $exit_code${NC}"
fi

exit $exit_code
