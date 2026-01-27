#!/bin/bash

# JobSwipe Mobile App Deployment Script
# This script builds the Flutter app for production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}JobSwipe Mobile App Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}Error: Flutter is not installed${NC}"
    echo "Please install Flutter: https://flutter.dev/docs/get-started/install"
    exit 1
fi

# Check if fastlane is installed for app store deployment
FASTLANE_INSTALLED=false
if command -v fastlane &> /dev/null; then
    FASTLANE_INSTALLED=true
    echo -e "${GREEN}Fastlane detected for automated app store deployment${NC}"
else
    echo -e "${YELLOW}Warning: Fastlane not installed. Manual app store deployment required.${NC}"
    echo "Install fastlane: https://docs.fastlane.tools/getting-started/ios/setup/ and https://docs.fastlane.tools/getting-started/android/setup/"
fi

# Check Flutter version
echo -e "\n${YELLOW}Flutter version:${NC}"
flutter --version

# Check if we're in the mobile-app directory
if [ ! -f "pubspec.yaml" ]; then
    echo -e "${RED}Error: pubspec.yaml not found${NC}"
    echo "Please run this script from the mobile-app directory"
    exit 1
fi

# Get current version from pubspec.yaml
CURRENT_VERSION=$(grep '^version:' pubspec.yaml | sed 's/version: //' | sed 's/+.*//')
echo -e "\n${YELLOW}Current app version: ${CURRENT_VERSION}${NC}"

# Prompt for version bump
echo -e "\n${YELLOW}Select version bump type:${NC}"
echo "1) Patch (bug fixes)"
echo "2) Minor (new features)"
echo "3) Major (breaking changes)"
echo "4) Keep current version"
read -p "Enter choice (1-4): " VERSION_CHOICE

case $VERSION_CHOICE in
    1) NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{print $1"."$2"."($3+1)}') ;;
    2) NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{print $1"."($2+1)".0"}') ;;
    3) NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{print ($1+1)".0.0"}') ;;
    4) NEW_VERSION=$CURRENT_VERSION ;;
    *) echo -e "${RED}Invalid choice. Keeping current version.${NC}"; NEW_VERSION=$CURRENT_VERSION ;;
esac

if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    echo -e "${GREEN}Updating version to: ${NEW_VERSION}${NC}"
    # Update pubspec.yaml version
    sed -i "s/version: $CURRENT_VERSION/version: $NEW_VERSION/" pubspec.yaml
fi

# Get release notes
echo -e "\n${YELLOW}Enter release notes (press Ctrl+D when done):${NC}"
RELEASE_NOTES=$(cat)

# Get dependencies
echo -e "\n${YELLOW}Getting dependencies...${NC}"
flutter pub get

# Run tests
echo -e "\n${YELLOW}Running tests...${NC}"
flutter test

# Build for Android (APK)
echo -e "\n${YELLOW}Building Android APK (Production)...${NC}"
flutter build apk --release --dart-define=ENV=production

# Build for Android (App Bundle)
echo -e "\n${YELLOW}Building Android App Bundle (Production)...${NC}"
flutter build appbundle --release --dart-define=ENV=production

# Build for iOS (IPA)
echo -e "\n${YELLOW}Building iOS IPA (Production)...${NC}"
flutter build ios --release --dart-define=ENV=production

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nAndroid APK: build/app/outputs/flutter-apk/app-release.apk"
echo -e "Android App Bundle: build/app/outputs/bundle/release/app-release.aab"
echo -e "iOS IPA: build/ios/archive/*.ipa"

# App Store Deployment
if [ "$FASTLANE_INSTALLED" = true ]; then
    echo -e "\n${YELLOW}Starting automated app store deployment...${NC}"

    # Create fastlane directory if it doesn't exist
    if [ ! -d "fastlane" ]; then
        echo -e "${YELLOW}Setting up fastlane...${NC}"
        fastlane init
    fi

    # Deploy to Google Play Store
    echo -e "\n${YELLOW}Deploying to Google Play Store...${NC}"
    fastlane android deploy

    # Deploy to Apple App Store
    echo -e "\n${YELLOW}Deploying to Apple App Store...${NC}"
    fastlane ios deploy

    echo -e "\n${GREEN}App store deployment complete!${NC}"
else
    echo -e "\n${YELLOW}Fastlane not available. Manual deployment required:${NC}"
    echo -e "  - Google Play: Upload the .aab file to Google Play Console"
    echo -e "  - Apple App Store: Upload the .ipa file via Xcode or Transporter"
fi

echo -e "\n${GREEN}Deployment Summary:${NC}"
echo -e "Version: ${NEW_VERSION}"
echo -e "Release Notes: ${RELEASE_NOTES}"
echo -e "Android: Deployed via fastlane"
echo -e "iOS: Deployed via fastlane"
