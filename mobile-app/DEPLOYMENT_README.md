# Mobile App Deployment Guide

This guide covers the automated deployment setup for JobSwipe mobile app to Google Play Store and Apple App Store.

## Overview

The deployment is automated using:
- **Fastlane** for managing app store deployments
- **GitHub Actions** for CI/CD pipelines
- **Flutter** for cross-platform mobile development

## Directory Structure

```
mobile-app/
├── android/
│   ├── fastlane/
│   │   ├── Appfile          # Android app store configuration
│   │   └── Fastfile         # Android deployment lanes
│   ├── generate_keystore.sh # Keystore generation script
│   └── gradle.properties    # Signing configuration
├── ios/
│   ├── fastlane/
│   │   ├── Appfile          # iOS app store configuration
│   │   └── Fastfile         # iOS deployment lanes
│   └── provisioning_profiles/
│       └── README.md        # Provisioning setup guide
└── DEPLOYMENT_README.md     # This file
```

## Prerequisites

### Android
- Google Play Console account
- Service account with Play Store access
- Keystore for signing

### iOS
- Apple Developer Program account
- App Store Connect API key
- Distribution certificate
- Provisioning profiles

## Setup Instructions

### 1. Android Setup

#### Generate Keystore
```bash
cd mobile-app/android
./generate_keystore.sh
```

Update `gradle.properties` with actual keystore passwords.

#### Play Store Credentials
1. Create a service account in Google Cloud Console
2. Grant Play Store access in Play Console
3. Download JSON key file
4. Store as base64 in GitHub secret: `PLAY_STORE_CREDENTIALS_JSON`

### 2. iOS Setup

#### App Store Connect API Key
1. Generate API key in App Store Connect
2. Download private key (.p8 file)
3. Store in GitHub secrets:
   - `APP_STORE_CONNECT_PRIVATE_KEY`: Base64 of .p8 file
   - `APP_STORE_CONNECT_KEY_ID`: Key ID
   - `APP_STORE_CONNECT_ISSUER_ID`: Issuer ID
   - `APP_STORE_CONNECT_TEAM_ID`: Team ID

#### Certificates and Provisioning
1. Create distribution certificate in Apple Developer Portal
2. Create App Store provisioning profile
3. Store in GitHub secrets:
   - `IOS_DISTRIBUTION_CERTIFICATE`: Base64 of .p12 file
   - `IOS_CERTIFICATE_PASSWORD`: Certificate password
   - `IOS_PROVISIONING_PROFILE`: Base64 of .mobileprovision file

### 3. GitHub Secrets

Set the following secrets in your GitHub repository:

#### Android
- `ANDROID_KEYSTORE_BASE64`: Base64 of keystore.jks
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`
- `PLAY_STORE_CREDENTIALS_JSON`

#### iOS
- `FASTLANE_USER`: Apple ID email
- `APP_STORE_CONNECT_PRIVATE_KEY`
- `APP_STORE_CONNECT_KEY_ID`
- `APP_STORE_CONNECT_ISSUER_ID`
- `APP_STORE_CONNECT_TEAM_ID`
- `IOS_DISTRIBUTION_CERTIFICATE`
- `IOS_CERTIFICATE_PASSWORD`
- `IOS_PROVISIONING_PROFILE`

## Deployment Workflows

### Automatic Deployment
- Push to `main` branch → Production deployment
- Create GitHub release → Production deployment

### Manual Deployment
Use GitHub Actions workflow dispatch:
- `deploy-android.yml`: Deploy to Play Store
- `deploy-ios.yml`: Deploy to App Store/TestFlight

## Fastlane Lanes

### Android
- `fastlane deploy`: Deploy to production track
- `fastlane beta`: Deploy to beta track

### iOS
- `fastlane deploy`: Deploy to App Store
- `fastlane beta`: Deploy to TestFlight

## Pre-deployment Checks

Run pre-deployment validation:
```bash
./tools/pre_deploy_mobile.sh
```

This checks:
- Flutter version and dependencies
- Code analysis and tests
- Version consistency
- Sensitive data scanning

## Troubleshooting

### Common Issues

1. **Keystore errors**: Ensure keystore file and passwords are correct
2. **Play Store API errors**: Check service account permissions
3. **iOS code signing**: Verify certificates and provisioning profiles
4. **App Store API errors**: Confirm API key and team ID

### Logs
Check GitHub Actions logs for detailed error messages.

## Security Notes

- Never commit keystore files or API keys
- Use GitHub secrets for all sensitive data
- Rotate keys regularly
- Limit service account permissions to minimum required

## Support

For issues with deployment setup, check:
1. Fastlane documentation: https://docs.fastlane.tools
2. Google Play Developer API docs
3. App Store Connect API docs
4. GitHub Actions documentation