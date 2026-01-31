# Flutter Android Setup Guide for JobSwipe

A comprehensive guide for configuring the Flutter Android build environment for the JobSwipe job search/matching application.

## Table of Contents

- [Overview](#overview)
- [Current Environment Status](#current-environment-status)
- [Prerequisites](#prerequisites)
- [Android SDK Setup (Linux)](#android-sdk-setup-linux)
- [Project Configuration](#project-configuration)
- [Gradle Configuration](#gradle-configuration)
- [Build Optimization](#build-optimization)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Production Build Checklist](#production-build-checklist)

---

## Overview

JobSwipe is a job search and matching application with a FastAPI backend. This guide covers the Flutter frontend Android configuration, supporting Android 7.0+ (API 24+).

### Architecture

- **Frontend**: Flutter 3.41.0-0.0.pre (Dart 3.10.7)
- **Backend**: FastAPI (Python)
- **Minimum Android Version**: API 24 (Android 7.0)
- **Target Android Version**: API 36 (Android 16)

---

## Current Environment Status

### Flutter SDK

```
Flutter version: 3.41.0-0.0.pre
Dart version: 3.10.7
Channel: master
```

### Android SDK Versions

| SDK Component | Version | Description |
|--------------|---------|-------------|
| `compileSdk` | 36 | Latest Android API level for compilation |
| `minSdk` | 24 | Minimum Android 7.0 (API 24) support |
| `targetSdk` | 36 | Target Android 16 (API 36) |
| `ndk` | 28.2.13676358 | Native Development Kit version |

### Gradle Configuration

| Component | Version | Notes |
|-----------|---------|-------|
| Gradle | 8.10.2 | Recommended for Flutter 3.41.0 |
| Android Gradle Plugin | 8.7.0 | Compatible with Gradle 8.10.2 |

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB+ free space
- **Java**: JDK 17 or JDK 21 (required for Gradle 8.x)

### Required Tools

```bash
# Verify Flutter installation
flutter doctor

# Verify Java installation
java -version

# Verify Android SDK
sdkmanager --list
```

---

## Android SDK Setup (Linux)

### Step 1: Install Java Development Kit

```bash
# Option 1: OpenJDK 17 (Recommended)
sudo apt update
sudo apt install openjdk-17-jdk

# Option 2: OpenJDK 21
sudo apt install openjdk-21-jdk

# Verify installation
java -version
javac -version
```

### Step 2: Download Android Command Line Tools

```bash
# Create Android SDK directory
mkdir -p ~/Android/Sdk
cd ~/Android/Sdk

# Download command line tools
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip

# Extract
unzip commandlinetools-linux-11076708_latest.zip

# Move to correct location
mkdir -p cmdline-tools/latest
mv cmdline-tools/* cmdline-tools/latest/ 2>/dev/null || true
```

### Step 3: Configure Environment Variables

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Android SDK
export ANDROID_HOME=$HOME/Android/Sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/emulator

# Java (adjust path as needed)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
```

Apply changes:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Step 4: Install Required SDK Components

```bash
# Accept licenses
sdkmanager --licenses

# Install essential packages
sdkmanager "platform-tools"
sdkmanager "platforms;android-36"
sdkmanager "build-tools;36.0.0"
sdkmanager "ndk;28.2.13676358"

# Install emulator (optional, for testing)
sdkmanager "emulator"
sdkmanager "system-images;android-36;google_apis;x86_64"
```

### Step 5: Verify Installation

```bash
# Check Flutter doctor
flutter doctor -v

# Verify Android SDK path
echo $ANDROID_HOME

# List installed packages
sdkmanager --list_installed
```

---

## Project Configuration

### Directory Structure

```
jobswipe/
├── android/
│   ├── app/
│   │   ├── build.gradle          # App-level build configuration
│   │   └── src/
│   ├── gradle/
│   │   └── wrapper/
│   │       └── gradle-wrapper.properties
│   ├── build.gradle              # Project-level build configuration
│   ├── gradle.properties         # Gradle properties
│   └── settings.gradle           # Project settings
├── FLUTTER_ANDROID_SETUP.md      # This file
└── pubspec.yaml                  # Flutter dependencies
```

### AndroidX Migration

JobSwipe uses AndroidX for modern Android support. Ensure `android/gradle.properties` contains:

```properties
org.gradle.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
```

### App-Level build.gradle

See [`android/app/build.gradle.template`](android/app/build.gradle.template) for the recommended configuration.

Key features:
- Uses Flutter-defined SDK versions
- Enables ProGuard for release builds
- Configures signing for production
- Optimizes build performance

---

## Gradle Configuration

### Gradle Wrapper

See [`android/gradle/wrapper/gradle-wrapper.properties.template`](android/gradle/wrapper/gradle-wrapper.properties.template) for the recommended configuration.

### Version Compatibility Matrix

| Flutter Version | Gradle Version | Android Gradle Plugin | JDK |
|----------------|----------------|----------------------|-----|
| 3.41.0-0.0.pre | 8.10.2 | 8.7.0 | 17-21 |
| 3.22.0 | 8.0 | 8.1.0 | 17 |
| 3.16.0 | 7.6.3 | 7.3.0 | 11-17 |

### Project-Level build.gradle

```gradle
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'

subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}

subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
```

### settings.gradle

```gradle
pluginManagement {
    def flutterSdkPath = {
        def properties = new Properties()
        file("local.properties").withInputStream { properties.load(it) }
        def flutterSdkPath = properties.getProperty("flutter.sdk")
        assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
        return flutterSdkPath
    }()

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id "dev.flutter.flutter-plugin-loader" version "1.0.0"
    id "com.android.application" version "8.7.0" apply false
    id "org.jetbrains.kotlin.android" version "1.8.22" apply false
}

include ":app"
```

---

## Build Optimization

### Gradle Performance Settings

Add to `android/gradle.properties`:

```properties
# Performance optimizations
org.gradle.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true

# Android optimizations
android.useAndroidX=true
android.enableJetifier=true
android.enableR8.fullMode=true
```

### Build Types

The template configures three build types:

1. **debug**: Development builds with debugging enabled
2. **profile**: Performance profiling builds
3. **release**: Optimized production builds with ProGuard

### ProGuard Configuration

Release builds use ProGuard for code shrinking and obfuscation:

```gradle
buildTypes {
    release {
        minifyEnabled true
        shrinkResources true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        signingConfig signingConfigs.release
    }
}
```

Create `android/app/proguard-rules.pro`:

```proguard
# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep custom application classes
-keep public class * extends android.app.Application
```

### Resource Optimization

Enable resource shrinking in release builds:

```gradle
android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
            signingConfig signingConfigs.release
        }
    }
}
```

---

## Common Issues and Solutions

### Gradle/AGP Version Conflicts

**Problem**: Build fails with "Minimum supported Gradle version is X.Y.Z" or incompatible AGP version errors.

**Solution**:
1. Check the [Version Compatibility Matrix](#version-compatibility-matrix) above
2. Update `android/gradle/wrapper/gradle-wrapper.properties`:
   ```properties
   distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-bin.zip
   ```
3. Update `android/settings.gradle`:
   ```gradle
   plugins {
       id "dev.flutter.flutter-plugin-loader" version "1.0.0"
       id "com.android.application" version "8.7.0" apply false
       id "org.jetbrains.kotlin.android" version "1.8.22" apply false
   }
   ```
4. Clean and rebuild:
   ```bash
   flutter clean
   flutter pub get
   cd android && ./gradlew clean && cd ..
   flutter build apk
   ```

**Prevention**: Run `flutter doctor` after any Flutter SDK update to catch version mismatches early.

---

### Memory Issues During Build

**Problem**: Build fails with `OutOfMemoryError`, `GC overhead limit exceeded`, or process gets killed (OOM).

**Solution**:
1. Increase Gradle heap size in `android/gradle.properties`:
   ```properties
   org.gradle.jvmargs=-Xmx6G -XX:MaxMetaspaceSize=4G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
   ```
2. Enable Gradle daemon with more memory:
   ```properties
   org.gradle.daemon=true
   org.gradle.parallel=true
   org.gradle.caching=true
   ```
3. For systems with limited RAM (8GB or less), close unnecessary applications during build
4. Consider using swap space on Linux:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

**Prevention**: Monitor memory usage during builds with `htop` or `free -h`. Consider upgrading to 16GB+ RAM for large Flutter projects.

---

### SDK/NDK Path Issues

**Problem**: "SDK location not found", "NDK not found", or "ANDROID_HOME not set" errors.

**Solution**:
1. Verify environment variables are set:
   ```bash
   echo $ANDROID_HOME
   echo $ANDROID_SDK_ROOT
   ```
2. If empty, add to `~/.bashrc` or `~/.zshrc`:
   ```bash
   export ANDROID_HOME=$HOME/Android/Sdk
   export ANDROID_SDK_ROOT=$ANDROID_HOME
   export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```
3. Apply changes:
   ```bash
   source ~/.bashrc  # or source ~/.zshrc
   ```
4. Verify SDK components are installed:
   ```bash
   sdkmanager --list_installed | grep -E "(platform-tools|build-tools|ndk)"
   ```
5. If NDK is missing:
   ```bash
   sdkmanager "ndk;28.2.13676358"
   ```

**Prevention**: Add SDK path verification to your shell startup and run `flutter doctor` regularly.

---

### Dependency Resolution Failures

**Problem**: Build fails with "Could not resolve" or "Failed to transform" dependency errors.

**Solution**:
1. Clear Gradle caches:
   ```bash
   cd android
   ./gradlew cleanBuildCache
   rm -rf ~/.gradle/caches/
   cd ..
   flutter clean
   flutter pub get
   ```
2. Check for network connectivity to Maven repositories
3. Force dependency refresh:
   ```bash
   cd android
   ./gradlew build --refresh-dependencies
   ```
4. If using private repositories, verify credentials in `~/.gradle/gradle.properties`
5. For transient dependency conflicts, exclude problematic packages in `android/app/build.gradle`:
   ```gradle
   implementation('com.example:library:1.0.0') {
       exclude group: 'com.conflicting', module: 'problematic-lib'
   }
   ```

**Prevention**: Pin dependency versions in `pubspec.yaml` and use lock files. Run `flutter pub outdated` regularly.

---

### Kotlin Version Mismatch

**Problem**: Build fails with "Kotlin version X required but Y found" errors.

**Solution**:
1. Check Kotlin version in `android/settings.gradle`:
   ```gradle
   id "org.jetbrains.kotlin.android" version "1.8.22" apply false
   ```
2. Ensure consistency across all Gradle files
3. Update `android/app/build.gradle` if needed:
   ```gradle
   android {
       // ...
       kotlinOptions {
           jvmTarget = '17'
       }
   }
   ```

---

### Build Cache Corruption

**Problem**: Strange build errors that persist after clean builds.

**Solution**:
1. Deep clean everything:
   ```bash
   flutter clean
   cd android
   ./gradlew clean
   rm -rf ~/.gradle/caches/
   rm -rf build/
   cd ..
   flutter pub get
   ```
2. Invalidate IDE caches if using Android Studio
3. Delete and regenerate `pubspec.lock`:
   ```bash
   rm pubspec.lock
   flutter pub get
   ```

---

## Production Build Checklist

### Pre-Build Verification Steps

Before creating a production build, verify the following:

- [ ] **Flutter Environment**
  - [ ] Run `flutter doctor` and resolve any issues
  - [ ] Verify Flutter version matches project requirements
  - [ ] Run `flutter pub get` successfully
  - [ ] Run `flutter test` and ensure all tests pass

- [ ] **Code Quality**
  - [ ] No debug print statements in production code
  - [ ] No hardcoded API keys or secrets in source code
  - [ ] All TODO/FIXME comments addressed or documented
  - [ ] Code analysis passes: `flutter analyze` shows no errors
  - [ ] Dart formatting applied: `dart format --set-exit-if-changed .`

- [ ] **Configuration Files**
  - [ ] `pubspec.yaml` version updated (follow semantic versioning)
  - [ ] `android/app/build.gradle` has correct versionCode and versionName
  - [ ] `android/app/src/main/AndroidManifest.xml` has proper permissions
  - [ ] ProGuard rules are configured for any third-party libraries

- [ ] **Assets and Resources**
  - [ ] All images optimized for mobile (use WebP where possible)
  - [ ] App icons generated for all required densities
  - [ ] Splash screen configured correctly
  - [ ] Localization files complete (if supporting multiple languages)

---

### Release Signing Configuration

Proper signing is required for Play Store submission.

**Step 1: Create Keystore (if not exists)**

```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA \
    -keysize 2048 -validity 10000 -alias upload
```

**Step 2: Configure Signing in `android/app/build.gradle`**

```gradle
android {
    // ...
    signingConfigs {
        release {
            keyAlias 'upload'
            keyPassword 'your-key-password'
            storeFile file('/home/username/upload-keystore.jks')
            storePassword 'your-store-password'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            // ...
        }
    }
}
```

**⚠️ Security Warning**: Never commit keystore passwords to version control. Use environment variables or a separate `key.properties` file (add to `.gitignore`):

```properties
# android/key.properties (add to .gitignore)
storePassword=your-store-password
keyPassword=your-key-password
keyAlias=upload
storeFile=/home/username/upload-keystore.jks
```

Then reference in `build.gradle`:
```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
}
```

**Step 3: Verify Signing Configuration**

```bash
cd android
./gradlew signingReport
```

---

### App Bundle Generation

Android App Bundle (AAB) is the recommended format for Play Store.

**Generate Release AAB**:

```bash
flutter build appbundle --release
```

Output: `build/app/outputs/bundle/release/app-release.aab`

**Generate APK (for testing)**:

```bash
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

**Split APKs by ABI (optional)**:

```bash
flutter build apk --release --split-per-abi
```

This generates separate APKs for:
- `app-arm64-v8a-release.apk`
- `app-armeabi-v7a-release.apk`
- `app-x86_64-release.apk`

**Verify Build Output**:

```bash
# Check AAB contents
bundletool validate --bundle=build/app/outputs/bundle/release/app-release.aab

# Check APK signature
apksigner verify -v build/app/outputs/flutter-apk/app-release.apk
```

---

### Testing Requirements

Before submission, thoroughly test the release build:

- [ ] **Functional Testing**
  - [ ] Install release APK on a physical device: `flutter install --release`
  - [ ] Test all user flows (onboarding, job search, applications, profile)
  - [ ] Verify API integration with production backend
  - [ ] Test authentication flows (login, logout, token refresh)
  - [ ] Verify push notifications work correctly

- [ ] **Performance Testing**
  - [ ] App launches within 3 seconds on mid-range device
  - [ ] Smooth scrolling in job lists (60 FPS)
  - [ ] Memory usage stays within acceptable limits
  - [ ] No ANR (Application Not Responding) errors

- [ ] **Device Compatibility**
  - [ ] Test on Android 7.0 (API 24) - minimum supported
  - [ ] Test on Android 16 (API 36) - target SDK
  - [ ] Test on various screen sizes (phone, tablet)
  - [ ] Test with different locales if localized

- [ ] **Edge Cases**
  - [ ] App behavior with no internet connection
  - [ ] App behavior with slow/intermittent connection
  - [ ] Background/foreground transitions
  - [ ] Low battery mode behavior
  - [ ] Dark mode compatibility

---

### Play Store Submission Prep

**Required Assets**:

- [ ] **App Icon**: 512x512 PNG (32-bit with alpha)
- [ ] **Feature Graphic**: 1024x500 PNG or JPEG
- [ ] **Screenshots**: 
  - Phone: 16:9 or 9:16 aspect ratio (minimum 320px, maximum 3840px)
  - Tablet (optional): 16:9 or 9:16 aspect ratio
  - Minimum 2 screenshots per supported device type
- [ ] **Short Description**: 80 characters max
- [ ] **Full Description**: 4000 characters max
- [ ] **Privacy Policy URL** (required for most apps)
- [ ] **Content Rating Questionnaire** completed

**Store Listing Checklist**:

- [ ] App title finalized (50 characters max)
- [ ] App category selected (e.g., "Business", "Productivity")
- [ ] Contact email provided
- [ ] Target countries/regions selected
- [ ] Pricing set (free or paid)
- [ ] Content rating obtained

**Pre-Launch Report**:

- [ ] Enable pre-launch report in Play Console
- [ ] Review automated test results
- [ ] Address any crashes or ANRs reported
- [ ] Review accessibility issues

**Release Checklist**:

- [ ] Internal testing track configured with team members
- [ ] Closed/Open testing tracks set up (optional but recommended)
- [ ] Production release prepared with staged rollout plan
- [ ] Release notes prepared for each track
- [ ] Rollback plan documented in case of critical issues

**Post-Submission**:

- [ ] Monitor crash reports in Play Console
- [ ] Monitor ANR rates
- [ ] Respond to user reviews promptly
- [ ] Track key metrics (installs, uninstalls, ratings)
- [ ] Plan update cycle for bug fixes and features

---

## Quick Reference Commands

```bash
# Development
flutter doctor                    # Check environment
flutter pub get                  # Install dependencies
flutter run                      # Debug run
flutter run --release            # Release run on device

# Testing
flutter test                     # Run unit tests
flutter integration_test         # Run integration tests
flutter drive                    # Run driver tests

# Building
flutter build apk                # Build APK
flutter build apk --release      # Build release APK
flutter build appbundle          # Build App Bundle
flutter build appbundle --release # Build release AAB

# Android-specific
cd android && ./gradlew clean    # Clean Android build
cd android && ./gradlew build    # Build Android only
cd android && ./gradlew signingReport  # Check signing

# Troubleshooting
flutter clean                    # Clean Flutter build
flutter pub cache repair         # Repair pub cache
flutter analyze                  # Static analysis
```

---

## Additional Resources

- [Flutter Android Deployment Documentation](https://docs.flutter.dev/deployment/android)
- [Android App Bundle Documentation](https://developer.android.com/guide/app-bundle)
- [Google Play Console Help](https://support.google.com/googleplay/android-developer)
- [Flutter Build Modes](https://docs.flutter.dev/testing/build-modes)
- [ProGuard Rules for Flutter](https://github.com/flutter/flutter/wiki/Obfuscating-Dart-Code)

---

*Last Updated: January 2026*
*For JobSwipe Flutter Application v3.41.0*
