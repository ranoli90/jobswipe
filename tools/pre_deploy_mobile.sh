#!/bin/bash

# Pre-deployment checks for mobile app
set -e

echo "Running pre-deployment checks for mobile app..."

# Check if we're in the right directory
if [ ! -f "mobile-app/pubspec.yaml" ]; then
    echo "Error: mobile-app/pubspec.yaml not found. Run from project root."
    exit 1
fi

cd mobile-app

# Check Flutter version
echo "Checking Flutter version..."
flutter --version

# Check dependencies
echo "Checking dependencies..."
flutter pub get

# Run static analysis
echo "Running Flutter analyze..."
flutter analyze --no-pub

# Run tests
echo "Running tests..."
flutter test --coverage

# Check for any TODO comments in production code
echo "Checking for TODO comments..."
if grep -r "TODO\|FIXME\|XXX" lib/ --include="*.dart" | grep -v test; then
    echo "Warning: Found TODO/FIXME comments in production code"
    # Don't fail the build for TODOs, just warn
fi

# Check version consistency
echo "Checking version consistency..."
PUBSPEC_VERSION=$(grep "version:" pubspec.yaml | sed 's/version: //')
ANDROID_VERSION=$(grep "versionName" android/app/build.gradle.kts | head -1 | sed 's/.*versionName = "\(.*\)"/\1/')
IOS_VERSION=$(grep "CFBundleShortVersionString" ios/Runner/Info.plist | sed 's/.*<string>\(.*\)<\/string>.*/\1/')

echo "Pubspec version: $PUBSPEC_VERSION"
echo "Android version: $ANDROID_VERSION"
echo "iOS version: $IOS_VERSION"

if [ "$PUBSPEC_VERSION" != "$ANDROID_VERSION" ] || [ "$PUBSPEC_VERSION" != "$IOS_VERSION" ]; then
    echo "Error: Version mismatch between pubspec.yaml, Android, and iOS"
    exit 1
fi

# Check for sensitive data
echo "Checking for sensitive data..."
if grep -r "password\|secret\|key\|token" lib/ --include="*.dart" | grep -v test | grep -v ".git"; then
    echo "Warning: Found potential sensitive data in code"
fi

# Check build configurations
echo "Checking build configurations..."
if [ ! -f "android/app/google-services.json" ]; then
    echo "Warning: google-services.json not found"
fi

if [ ! -f "ios/Runner/GoogleService-Info.plist" ]; then
    echo "Warning: GoogleService-Info.plist not found"
fi

echo "Pre-deployment checks completed successfully!"