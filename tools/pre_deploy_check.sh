#!/bin/bash

# Pre-deployment validation script for JobSwipe
# This script validates that all required secrets are properly configured
# before allowing deployment to proceed.

set -e

echo "🔍 Running pre-deployment checks..."

# Check if required tools are available
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required but not installed."; exit 1; }

# Validate production secrets
echo "📋 Validating production secrets..."
if [ -f ".env.production" ]; then
    python3 tools/validate_secrets.py --env-file .env.production
    echo "✅ Production secrets validation passed"
else
    echo "⚠️  .env.production file not found - skipping validation"
fi

# Validate staging secrets
echo "📋 Validating staging secrets..."
if [ -f ".env.staging" ]; then
    python3 tools/validate_secrets.py --env-file .env.staging
    echo "✅ Staging secrets validation passed"
else
    echo "⚠️  .env.staging file not found - skipping validation"
fi

# Check for any remaining placeholder values in environment files (uncommented lines only)
echo "🔍 Checking for placeholder values..."
placeholder_patterns=("your_" "CHANGE_" "dev-" "minioadmin" "user:password@host:port")

for file in .env.production .env.staging; do
    if [ -f "$file" ]; then
        echo "Checking $file..."
        for pattern in "${placeholder_patterns[@]}"; do
            # Check only uncommented lines (lines that don't start with #)
            if grep -v '^#' "$file" | grep -q "$pattern"; then
                echo "❌ Found placeholder pattern '$pattern' in uncommented lines of $file"
                echo "Please replace all placeholder values with actual secrets."
                exit 1
            fi
        done
        echo "✅ No placeholder values found in uncommented lines of $file"
    fi
done

echo ""
echo "🎉 All pre-deployment checks passed!"
echo "🚀 Ready for deployment"