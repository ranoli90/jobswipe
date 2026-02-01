#!/bin/bash

echo "=========================================="
echo "=== Jobswipe Security Audit ==="
echo "=========================================="
echo ""

# Check for flake8 installation
if ! command -v flake8 &> /dev/null; then
    echo "❌ flake8 not installed. Please install with: pip install flake8"
    exit 1
fi

# Check for bandit installation
if ! command -v bandit &> /dev/null; then
    echo "❌ bandit not installed. Please install with: pip install bandit"
    exit 1
fi

echo "=== Step 1: Running flake8 for syntax and error checks ==="
flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
echo ""

echo "=== Step 2: Running flake8 with style and complexity checks ==="
flake8 backend/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
echo ""

echo "=== Step 3: Running bandit for security vulnerability checks ==="
bandit -r backend/ -f json -o bandit-report.json
bandit -r backend/ -f screen -v
echo ""

echo "=== Step 4: Checking for uncommitted changes ==="
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Uncommitted changes detected:"
    git status
else
    echo "✅ No uncommitted changes"
fi
echo ""

echo "=== Step 5: Checking for sensitive files in git ==="
SENSITIVE_FILES=("*.env" "*.env.*" "*.pem" "*.key" "*.crt" "secrets*.json" "vault*.json")
for pattern in "${SENSITIVE_FILES[@]}"; do
    if compgen -G "$pattern" > /dev/null; then
        echo "⚠️  Sensitive file pattern found: $pattern"
    fi
done
echo ""

echo "=========================================="
echo "=== Audit Complete ==="
echo "=========================================="
echo ""
echo "Reports generated:"
echo "  - bandit-report.json (security vulnerabilities)"
