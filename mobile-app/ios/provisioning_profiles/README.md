# iOS Provisioning Profiles Setup

This directory should contain the provisioning profiles for different environments.

## Required Provisioning Profiles

1. **Development Profile**: `jobswipe_dev.mobileprovision`
   - Bundle ID: `com.jobswipe.jobswipe.dev`
   - Used for development builds

2. **Staging Profile**: `jobswipe_staging.mobileprovision`
   - Bundle ID: `com.jobswipe.jobswipe.staging`
   - Used for staging builds

3. **Production Profile**: `jobswipe_prod.mobileprovision`
   - Bundle ID: `com.jobswipe.jobswipe`
   - Used for production builds

## Setup Instructions

1. Log in to [Apple Developer Portal](https://developer.apple.com)
2. Create App IDs for each bundle ID
3. Create provisioning profiles for each environment
4. Download the .mobileprovision files and place them in this directory
5. Update the Xcode project to use these profiles

## Xcode Configuration

In Xcode, for each scheme:
- Set the Provisioning Profile under Build Settings > Code Signing
- Ensure the Code Signing Identity matches the profile

## Environment Variables

Set the following in your CI/CD or local environment:
- `IOS_DEV_PROVISIONING_PROFILE`: Path to dev profile
- `IOS_STAGING_PROVISIONING_PROFILE`: Path to staging profile
- `IOS_PROD_PROVISIONING_PROFILE`: Path to prod profile