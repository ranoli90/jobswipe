# Mobile App Deployment Guide for JobSwipe

A comprehensive guide for building, testing, and deploying the JobSwipe Flutter mobile app to Google Play Store.

## Table of Contents

- [Build Prerequisites](#build-prerequisites)
- [Local Development Setup](#local-development-setup)
- [Build Commands](#build-commands)
- [Release Signing Setup](#release-signing-setup)
- [Testing Checklist](#testing-checklist)
- [Quick Reference](#quick-reference)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Build Prerequisites

### Flutter SDK Version Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Flutter SDK | 3.41.0 or higher | Master channel recommended |
| Dart SDK | 3.10.7 or higher | Bundled with Flutter |
| Channel | master | For latest fixes |

**Verify your Flutter installation:**
```bash
flutter --version
flutter doctor -v
```

### Java 17 Requirement

Java 17 is **required** for Gradle 8.x and Android Gradle Plugin 8.x.

**Check your Java version:**
```bash
java -version
```

**If you need to install Java 17 on Windows:**
1. Download OpenJDK 17 from [Adoptium](https://adoptium.net/)
2. Run the installer
3. Set `JAVA_HOME` environment variable to the JDK installation path
4. Add `%JAVA_HOME%\bin` to your PATH

**Set Java 17 for Flutter (if multiple Java versions installed):**
```powershell
# PowerShell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.10.7-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
```

### Android SDK Setup

**Required SDK Components:**

| Component | Version | Description |
|-----------|---------|-------------|
| compileSdk | 36 | Android API 36 for compilation |
| minSdk | 24 | Minimum Android 7.0 support |
| targetSdk | 36 | Target Android 16 |
| build-tools | 36.0.0 | Build tools version |
| ndk | 28.2.13676358 | Native Development Kit |

**Verify Android SDK installation:**
```bash
flutter doctor -v
# Look for Android SDK section
```

**Environment Variables (Windows):**
```powershell
# System Environment Variables
ANDROID_HOME = C:\Users\%USERNAME%\AppData\Local\Android\Sdk
ANDROID_SDK_ROOT = %ANDROID_HOME%
```

---

## Local Development Setup

### Installation of Dependencies

```bash
# Navigate to mobile-app directory
cd mobile-app

# Get Flutter dependencies
flutter pub get

# Generate Flutter localization (if using)
flutter gen-l10n

# Install Fastlane for deployment (optional)
gem install fastlane  # Ruby required
# OR
brew install fastlane # macOS with Homebrew
```

### Environment Configuration (Dart-Define Usage)

JobSwipe uses Flutter's `--dart-define` for environment-specific configuration.

**Available Dart Defines:**

| Variable | Dev | Staging | Production |
|----------|-----|---------|------------|
| API_BASE_URL | http://10.0.2.2:8000 | https://staging.api.jobswipe.com | https://api.jobswipe.com |
| APP_SUFFIX | .dev | .staging | (empty) |

**Example environment file (.env):**
```properties
# mobile-app/.env
API_BASE_URL=http://10.0.2.2:8000
APP_SUFFIX=.dev
```

**Build with custom API URL:**
```bash
flutter build apk --debug --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### Running the App in Debug Mode

```bash
# Run with default configuration
flutter run --flavor dev

# Run with custom API
flutter run --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Hot reload enabled by default
# Press 'r' to reload, 'R' to restart
```

---

## Build Commands

### Debug Builds for All Flavors

```bash
# Development build (debug)
flutter build apk --debug --flavor dev -t lib/main.dart

# Staging build (debug)
flutter build apk --debug --flavor staging -t lib/main.dart

# Production build (debug)
flutter build apk --debug --flavor prod -t lib/main.dart
```

### Release Builds

```bash
# Development release
flutter build apk --release --flavor dev -t lib/main.dart

# Staging release
flutter build apk --release --flavor staging -t lib/main.dart

# Production release (requires signing)
flutter build apk --release --flavor prod -t lib/main.dart
```

### Build with Custom API URL

```bash
# Development with local backend
flutter build apk --debug --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Staging environment
flutter build apk --release --flavor staging --dart-define=API_BASE_URL=https://staging.api.jobswipe.com

# Production environment
flutter build apk --release --flavor prod --dart-define=API_BASE_URL=https://api.jobswipe.com
```

### Build Outputs

Build artifacts are generated in `build/app/outputs/flutter-apk/`:

| Flavor | Debug Output | Release Output |
|--------|--------------|----------------|
| dev | app-dev-debug.apk | app-dev-release.apk |
| staging | app-staging-debug.apk | app-staging-release.apk |
| prod | app-prod-debug.apk | app-prod-release.apk |

---

## Release Signing Setup

### Generate Release Keystore

**Using the provided script (Linux/macOS):**
```bash
cd mobile-app/android
./generate_keystore.sh
```

**Manual keystore generation (Windows PowerShell):**
```powershell
keytool -genkeypair -v -storetype JKS -keyalg RSA -keysize 2048 `
  -validity 10000 `
  -keystore mobile-app/android/app/release.keystore `
  -alias jobswipe-upload `
  -keypass your_key_password `
  -storepass your_store_password
```

**Required keystore information:**
- Keystore password (storepass)
- Key alias (jobswipe-upload)
- Key password (keypass)

### Configure Signing in gradle.properties

Edit `mobile-app/android/gradle.properties`:

```properties
# Release signing configuration
MYAPP_UPLOAD_STORE_PASSWORD=your_store_password
MYAPP_UPLOAD_KEY_PASSWORD=your_key_password
MYAPP_UPLOAD_KEY_ALIAS=jobswipe-upload

# Path to keystore (relative to android/app/)
KEYSTORE_PATH=app/release.keystore
```

**Security Note:** Never commit actual passwords to version control. Use environment variables or a separate `local.properties` file (add to `.gitignore`).

### Update build.gradle.kts for Production Signing

Edit `mobile-app/android/app/build.gradle.kts`:

```kotlin
android {
    signingConfigs {
        create("release") {
            keyAlias = "jobswipe-upload"
            keyPassword = project.findProperty("MYAPP_UPLOAD_KEY_PASSWORD") as? String ?: ""
            storeFile = file(project.findProperty("KEYSTORE_PATH") as? String ?: "release.keystore")
            storePassword = project.findProperty("MYAPP_UPLOAD_STORE_PASSWORD") as? String ?: ""
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            minifyEnabled(true)
            shrinkResources(true)
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    flavorDimensions += "environment"
    productFlavors {
        create("dev") { ... }
        create("staging") { ... }
        create("prod") {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

### CI/CD Signing Configuration

For GitHub Actions or CI/CD pipelines, use environment variables:

```yaml
# GitHub Actions example
- name: Build Release APK
  env:
    MYAPP_UPLOAD_STORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
    MYAPP_UPLOAD_KEY_PASSWORD: ${{ secrets.ANDROID_KEY_PASSWORD }}
    MYAPP_UPLOAD_KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
  run: flutter build apk --release --flavor prod
```

---

## Testing Checklist

### Code Analysis

```bash
# Run Flutter analyzer
flutter analyze

# Analyze with specific directory
flutter analyze lib/

# Check for deprecated API usage
flutter analyze lib/ --watch
```

### Unit Tests

```bash
# Run all tests
flutter test

# Run tests with coverage
flutter test --coverage

# Run specific test file
flutter test test/unit_test.dart

# Run tests in specific directory
flutter test test/domain/
```

### Manual Testing Criteria

#### Launch Time Testing

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Cold start | < 3 seconds | Manual timing from tap to home screen |
| Warm start | < 1 second | Manual timing from background |
| Time to interactive | < 5 seconds | Measure until UI is responsive |

#### Navigation Testing

- [ ] Splash screen displays correctly
- [ ] Login screen loads without lag
- [ ] Bottom navigation switches between tabs
- [ ] Back button navigation works correctly
- [ ] Deep links open correct screens
- [ ] Screen rotation preserves state

#### Error Handling Testing

- [ ] Invalid credentials show appropriate error
- [ ] Network timeout displays user-friendly message
- [ ] API errors show fallback UI
- [ ] Unexpected crashes are caught and logged
- [ ] Offline mode works when no network

#### Network Unavailability Testing

1. **Airplane Mode Test:**
   - Enable airplane mode
   - Launch app
   - Verify offline message displays
   - Test cached data loading

2. **Wi-Fi Off Test:**
   - Disable Wi-Fi
   - Keep mobile data on
   - Verify app functions with data
   - Test after data also disabled

3. **Server Down Test:**
   - Block API requests (use airplane mode or firewall)
   - Test job feed loading
   - Verify error states and retry options
   - Check cached data display

4. **Timeout Simulation:**
   - Use Charles Proxy or similar to simulate slow network
   - Verify loading indicators show
   - Test timeout error handling

### Performance Testing

```bash
# Profile mode for performance analysis
flutter run --profile --flavor dev

# Memory profiling
dart devtools

# Build size analysis
flutter build apk --analyze-size --flavor prod
```

---

## Quick Reference

### Essential Commands

```bash
# Clean and rebuild
flutter clean && flutter pub get

# Get dependencies
flutter pub get

# Analyze code
flutter analyze

# Run tests
flutter test

# Build debug APK (dev)
flutter build apk --debug --flavor dev

# Build release APK (prod)
flutter build apk --release --flavor prod

# Run on device
flutter run --flavor dev

# Check for issues
flutter doctor -v
```

### File Locations

| File | Location |
|------|----------|
| Build outputs | `build/app/outputs/flutter-apk/` |
| Gradle wrapper | `android/gradle/wrapper/` |
| Keystore (generate) | `android/generate_keystore.sh` |
| ProGuard rules | `android/app/proguard-rules.pro` |
| Environment config | `lib/config/app_config.dart` |

### Environment Variables Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `JAVA_HOME` | Java SDK path | Required |
| `ANDROID_HOME` | Android SDK path | Required |
| `ANDROID_SDK_ROOT` | Android SDK root | Optional |
| `API_BASE_URL` | Backend API URL | Varies by flavor |

---

## Troubleshooting Guide

### Common Build Issues

#### 1. Gradle Version Mismatch

**Error:** `Minimum supported Gradle version is X.Y.Z`

**Solution:**
```bash
# Check Gradle version
cd android
./gradlew --version

# Update Gradle wrapper
cd android/gradle/wrapper/
# Edit gradle-wrapper.properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-bin.zip

# Clean and rebuild
flutter clean
flutter pub get
flutter build apk
```

#### 2. Java Version Issues

**Error:** `Could not determine the Java version`

**Solution:**
```powershell
# Verify Java 17 is set
java -version

# Set Java 17 explicitly
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.10.7-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Clean and rebuild
flutter clean
flutter build apk
```

#### 3. Android SDK Not Found

**Error:** `SDK location not found`

**Solution:**
```powershell
# Verify ANDROID_HOME is set
echo $env:ANDROID_HOME

# Set if not present (in PowerShell as Administrator)
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk", "User")
[Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk", "User")

# Restart terminal and verify
flutter doctor -v
```

#### 4. Dependency Resolution Failures

**Error:** `Could not resolve` or `Failed to transform`

**Solution:**
```bash
# Clear Gradle caches
cd android
./gradlew cleanBuildCache
rm -rf ~/.gradle/caches/
cd ..

# Clean Flutter build
flutter clean
flutter pub get

# Force dependency refresh
flutter pub upgrade
flutter pub get
```

#### 5. Memory Issues (OutOfMemoryError)

**Error:** `OutOfMemoryError: GC overhead limit exceeded`

**Solution:**
Edit `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx6G -XX:MaxMetaspaceSize=4G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
```

#### 6. Keystore Errors

**Error:** `Keystore was tampered with, or password was incorrect`

**Solution:**
```bash
# Verify keystore exists
ls -la android/app/release.keystore

# Verify passwords match in gradle.properties
# Re-generate keystore if passwords lost
keytool -genkeypair -v -storetype JKS -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -keystore android/app/release.keystore \
  -alias jobswipe-upload
```

### Build Performance Tips

1. **Enable Gradle caching:**
   ```properties
   org.gradle.caching=true
   ```

2. **Enable parallel builds:**
   ```properties
   org.gradle.parallel=true
   ```

3. **Use daemon:**
   ```properties
   org.gradle.daemon=true
   ```

4. **Enable configuration on demand:**
   ```properties
   org.gradle.configureondemand=true
   ```

### Getting Help

1. **Flutter Doctor:** `flutter doctor -v`
2. **Flutter Build Verbose:** `flutter build apk -v`
3. **Gradle Verbose:** `flutter build apk --debug --verbose`
4. **Check logs:** `flutter logs`

---

## Version Compatibility Reference

| Flutter Version | Gradle Version | Android Gradle Plugin | Java Version |
|----------------|----------------|----------------------|--------------|
| 3.41.0+ | 8.10.2 | 8.7.0 | 17-21 |
| 3.22.0 | 8.0 | 8.1.0 | 17 |
| 3.16.0 | 7.6.3 | 7.3.0 | 11-17 |

---

## Security Best Practices

1. **Never commit keystores or passwords to version control**
2. **Use environment variables for sensitive data**
3. **Rotate keystores annually**
4. **Limit CI/CD service account permissions**
5. **Use separate keystores for dev/staging/prod**
6. **Enable ProGuard/R8 for release builds**
7. **Use HTTPS for all API communications**
8. **Implement certificate pinning for production**

---

## Support

For issues with:
- **Flutter:** [Flutter Documentation](https://docs.flutter.dev)
- **Android:** [Android Developer Documentation](https://developer.android.com)
- **Gradle:** [Gradle Documentation](https://docs.gradle.org)
- **Fastlane:** [Fastlane Documentation](https://docs.fastlane.tools)
