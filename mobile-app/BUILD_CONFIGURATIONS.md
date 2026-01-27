# Build Configurations for JobSwipe Mobile App

This document outlines the build configurations for Android and iOS platforms with proper signing and build variants.

## Android Configuration

### Signing Configuration

- **Keystore**: Located at `../keystore.jks` (relative to `android/app/`)
- **Properties**: Configured in `android/gradle.properties`
- **Generation Script**: `android/generate_keystore.sh`

Update `android/gradle.properties` with actual passwords before building:

```properties
MYAPP_UPLOAD_STORE_PASSWORD=your_store_password
MYAPP_UPLOAD_KEY_PASSWORD=your_key_password
```

### Build Variants (Flavors)

- **dev**: Development build with suffix `.dev`
- **staging**: Staging build with suffix `.staging`
- **prod**: Production build (no suffix)

#### Build Commands

```bash
# Development
flutter build apk --flavor dev --debug
flutter build apk --flavor dev --release

# Staging
flutter build apk --flavor staging --debug
flutter build apk --flavor staging --release

# Production
flutter build apk --flavor prod --debug
flutter build apk --flavor prod --release
```

## iOS Configuration

### Provisioning Profiles

Provisioning profiles should be placed in `ios/provisioning_profiles/`:

- `jobswipe_dev.mobileprovision` - Development
- `jobswipe_staging.mobileprovision` - Staging
- `jobswipe_prod.mobileprovision` - Production

### Build Variants (Schemes)

Xcode schemes are configured via xcconfig files:

- **Dev-Debug/Release**: `com.jobswipe.jobswipe.dev`
- **Staging-Debug/Release**: `com.jobswipe.jobswipe.staging`
- **Prod-Debug/Release**: `com.jobswipe.jobswipe`

#### Build Commands

```bash
# Development
flutter build ios --flavor dev --debug
flutter build ios --flavor dev --release

# Staging
flutter build ios --flavor staging --debug
flutter build ios --flavor staging --release

# Production
flutter build ios --flavor prod --debug
flutter build ios --flavor prod --release
```

## Flutter Configuration

Flavors are defined in `pubspec.yaml` under the `flutter.flavors` section.

## Environment Setup

1. **Android**: Generate keystore using the provided script
2. **iOS**: Download provisioning profiles from Apple Developer Portal
3. Update configuration files with actual credentials
4. Configure CI/CD pipelines to use appropriate flavors

## CI/CD Integration

For automated builds, set environment variables:

- Android: `MYAPP_UPLOAD_STORE_PASSWORD`, `MYAPP_UPLOAD_KEY_PASSWORD`
- iOS: Provisioning profile paths and signing certificates

## Security Notes

- Never commit actual keystore files or passwords to version control
- Use environment variables or secure credential storage in CI/CD
- Rotate keystores and certificates regularly
- Keep provisioning profiles up to date