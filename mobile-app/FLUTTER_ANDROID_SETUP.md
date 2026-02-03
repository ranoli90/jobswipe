# Flutter Android Setup - Quick Reference

Configuration changes, quick commands, and troubleshooting guide for JobSwipe Android builds.

## Configuration Changes Summary (Phases 1-4)

### Phase 1: Gradle Version Update
**Files Modified:** `android/gradle/wrapper/gradle-wrapper.properties`
```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-bin.zip
```

### Phase 2: Android Gradle Plugin Update
**Files Modified:** `android/settings.gradle.kts`
```kotlin
plugins {
    id "dev.flutter.flutter-plugin-loader" version "1.0.0"
    id "com.android.application" version "8.7.0" apply false
    id "org.jetbrains.kotlin.android" version "1.8.22" apply false
}
```

### Phase 3: Build Configuration
**Files Modified:** `android/app/build.gradle.kts`, `android/gradle.properties`

Key additions to `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true
android.useAndroidX=true
android.enableJetifier=true
android.enableR8.fullMode=true
```

### Phase 4: Signing & Release Configuration
**Files Modified:** `android/gradle.properties`, `android/app/build.gradle.kts`

Added signing configuration:
```properties
MYAPP_UPLOAD_STORE_PASSWORD=your_password
MYAPP_UPLOAD_KEY_PASSWORD=your_password
MYAPP_UPLOAD_KEY_ALIAS=jobswipe-upload
KEYSTORE_PATH=app/release.keystore
```

---

## Quick Reference Commands

### Development Commands
```powershell
# Check environment
flutter doctor -v

# Install dependencies
flutter pub get

# Run on device (dev flavor)
flutter run --flavor dev

# Hot reload
# Press 'r' in terminal
```

### Build Commands
```powershell
# Debug builds
flutter build apk --debug --flavor dev -t lib/main.dart
flutter build apk --debug --flavor staging -t lib/main.dart
flutter build apk --debug --flavor prod -t lib/main.dart

# Release builds
flutter build apk --release --flavor dev -t lib/main.dart
flutter build apk --release --flavor staging -t lib/main.dart
flutter build apk --release --flavor prod -t lib/main.dart

# Build with custom API URL
flutter build apk --debug --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### Android-Specific Commands
```powershell
# Clean Android build
cd android
./gradlew clean
cd ..

# Check signing configuration
cd android
./gradlew signingReport

# Build Android only
flutter build apk --debug
```

### Testing Commands
```powershell
# Static analysis
flutter analyze

# Run tests
flutter test

# Run with coverage
flutter test --coverage

# Profile mode
flutter run --profile
```

---

## Troubleshooting Guide

### Issue 1: Gradle Version Mismatch

**Symptoms:**
- "Minimum supported Gradle version is X.Y.Z"
- "Incompatible AGP version"

**Solution:**
```powershell
# Check current versions
cd android
./gradlew --version

# Update gradle-wrapper.properties
# File: android/gradle/wrapper/gradle-wrapper.properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-bin.zip

# Clean and rebuild
flutter clean
flutter pub get
flutter build apk
```

### Issue 2: Java Version Not Supported

**Symptoms:**
- "Could not determine the Java version"
- Build fails immediately

**Solution:**
```powershell
# Verify Java version
java -version

# Set Java 17 explicitly
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.10.7-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Verify
java -version
```

### Issue 3: Android SDK Not Found

**Symptoms:**
- "SDK location not found"
- "ANDROID_HOME not set"

**Solution:**
```powershell
# Verify ANDROID_HOME
echo $env:ANDROID_HOME

# Set environment variable (PowerShell as Administrator)
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk", "User")

# Restart terminal and verify
flutter doctor -v
```

### Issue 4: Dependency Resolution Failures

**Symptoms:**
- "Could not resolve" errors
- "Failed to transform" errors

**Solution:**
```powershell
# Clear all caches
flutter clean
cd android
./gradlew cleanBuildCache
rm -rf ~/.gradle/caches/
cd ..

# Refresh dependencies
flutter pub get
flutter pub upgrade
flutter pub get

# Force rebuild
flutter build apk
```

### Issue 5: Out of Memory (OOM)

**Symptoms:**
- "OutOfMemoryError"
- Build process killed
- "GC overhead limit exceeded"

**Solution:**
Edit `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx6G -XX:MaxMetaspaceSize=4G -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
```

Then run:
```powershell
flutter clean
flutter build apk
```

### Issue 6: Keystore Errors

**Symptoms:**
- "Keystore was tampered with"
- "Password was incorrect"

**Solution:**
```powershell
# Verify keystore exists
dir android\app\release.keystore

# Verify passwords in android/gradle.properties
# MYAPP_UPLOAD_STORE_PASSWORD=your_password
# MYAPP_UPLOAD_KEY_PASSWORD=your_password

# Re-generate if needed (WARNING: This breaks existing releases)
keytool -genkeypair -v -storetype JKS -keyalg RSA -keysize 2048 `
  -validity 10000 `
  -keystore android/app/release.keystore `
  -alias jobswipe-upload `
  -keypass new_password `
  -storepass new_password
```

### Issue 7: Build Cache Corruption

**Symptoms:**
- Strange errors after updates
- Clean builds don't fix issues

**Solution:**
```powershell
# Deep clean everything
flutter clean
cd android
./gradlew clean
rm -rf build/
rm -rf ~/.gradle/caches/
cd ..

# Delete pubspec.lock and regenerate
rm pubspec.lock
flutter pub get

# Invalidate IDE caches (if using Android Studio)
# File > Invalidate Caches / Restart

# Rebuild
flutter build apk
```

### Issue 8: Kotlin Version Mismatch

**Symptoms:**
- "Kotlin version X required but Y found"
- Compilation errors related to Kotlin

**Solution:**
Check `android/settings.gradle.kts`:
```kotlin
id "org.jetbrains.kotlin.android" version "1.8.22" apply false
```

Update to matching version in `android/app/build.gradle.kts`:
```kotlin
android {
    kotlinOptions {
        jvmTarget = '17'
    }
}
```

---

## Environment Verification Checklist

Before building, verify:

- [ ] `flutter doctor -v` shows no errors
- [ ] Java 17 is installed and `JAVA_HOME` set
- [ ] Android SDK installed with API 36
- [ ] `ANDROID_HOME` environment variable set
- [ ] `flutter pub get` completes successfully
- [ ] `flutter analyze` shows no errors

Run validation script:
```powershell
.\validate_build.ps1
```

---

## File Reference

| File | Purpose |
|------|---------|
| `android/gradle.properties` | Gradle properties, signing passwords |
| `android/settings.gradle.kts` | Plugin versions, project settings |
| `android/app/build.gradle.kts` | App configuration, signing, flavors |
| `android/gradle/wrapper/gradle-wrapper.properties` | Gradle version |
| `android/app/proguard-rules.pro` | Code obfuscation rules |
| `lib/config/app_config.dart` | App configuration, API URLs |

---

## Support Resources

- [Flutter Documentation](https://docs.flutter.dev)
- [Android Developer Documentation](https://developer.android.com)
- [Flutter Android Deployment](https://docs.flutter.dev/deployment/android)
- [Gradle Documentation](https://docs.gradle.org)

---

*Last Updated: February 2026*
*JobSwipe Mobile App v3.41.0*
