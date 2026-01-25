#!/usr/bin/env bash
set -euo pipefail

# Apple App Store Lookup Script
# For Sorce-like Job Search App

APP_ID="6504584959"
OUTPUT_DIR="$(dirname "$0")/../data"
OUTPUT_FILE="$OUTPUT_DIR/appstore_lookup.json"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Fetching App Store metadata for app ID: $APP_ID"

# Fetch App Store metadata using Apple Lookup API
curl -s "https://itunes.apple.com/lookup?id=${APP_ID}" | jq . > "$OUTPUT_FILE"

# Display key information
echo "Successfully fetched metadata"
echo "------------------------------------------"
jq '.results[0] | {
    version, 
    minimumOsVersion, 
    sellerName, 
    releaseNotes, 
    screenshotUrls: .screenshotUrls[:3]
}' "$OUTPUT_FILE"
echo "------------------------------------------"
echo "Full response saved to: $OUTPUT_FILE"

# Check if metadata has changed from previous version (if exists)
if [ -f "$OUTPUT_DIR/appstore_lookup_prev.json" ]; then
    echo "Checking for metadata changes..."
    if diff -q "$OUTPUT_DIR/appstore_lookup_prev.json" "$OUTPUT_FILE" > /dev/null; then
        echo "No changes detected in App Store metadata"
    else
        echo "Metadata has changed! Creating backup of previous version"
        cp "$OUTPUT_FILE" "$OUTPUT_DIR/appstore_lookup_prev.json"
        git add "$OUTPUT_DIR/appstore_lookup_prev.json"
        git commit -m "Update App Store metadata"
    fi
else
    # First run - create previous version file
    cp "$OUTPUT_FILE" "$OUTPUT_DIR/appstore_lookup_prev.json"
fi

# Validate the response
if ! jq -e '.results[0]' "$OUTPUT_FILE" > /dev/null; then
    echo "ERROR: Failed to parse App Store response"
    rm -f "$OUTPUT_FILE"
    exit 1
fi

echo "App Store metadata validation successful"
