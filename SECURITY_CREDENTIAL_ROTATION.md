# Security Credential Rotation Guide

## URGENT: Firebase Credentials Were Exposed

The following Firebase credentials were accidentally committed to version control and MUST be regenerated:

### Exposed Credentials (NOW INVALID - DO NOT USE):
- iOS API Key: `AIzaSyc0298053d61363d701c58ec23f408ab12aa49204d9`
- Android API Key: `AIzaSyc0298053d61363d701c58ec23f408ab12aa49204d9`
- Project ID: `jobswipe-app`
- GCM Sender ID: `111270390054`

### Steps to Regenerate:

#### Step 1: Access Firebase Console
1. Go to https://console.firebase.google.com
2. Select the `jobswipe-app` project

#### Step 2: Regenerate API Keys
1. Go to Project Settings > General
2. Scroll to "Your apps" section
3. For each app (iOS and Android):
   - Click the gear icon
   - Select "Manage API key in Google Cloud Console"
   - In Google Cloud Console, create a NEW API key
   - Restrict the new key to your app's bundle ID / package name
   - Delete the OLD exposed key

#### Step 3: Download New Credential Files
1. In Firebase Console > Project Settings > General
2. For iOS app: Click "GoogleService-Info.plist" download button
3. For Android app: Click "google-services.json" download button

#### Step 4: Update Local Files
1. Replace `mobile-app/ios/Runner/GoogleService-Info.plist` with new file
2. Replace `mobile-app/android/app/google-services.json` with new file
3. DO NOT commit these files to git (they are in .gitignore)

#### Step 5: Update CI/CD Secrets
1. In GitHub repository settings > Secrets and variables > Actions
2. Update or create these secrets:
   - `GOOGLE_SERVICES_JSON` - Base64 encoded content of google-services.json
   - `GOOGLE_SERVICE_INFO_PLIST` - Base64 encoded content of GoogleService-Info.plist

#### Step 6: Verify
1. Build the app locally
2. Test Firebase features (push notifications, analytics, crashlytics)
3. Confirm old API keys no longer work

### Prevention Measures Implemented:
- Added credential files to `.gitignore`
- Removed credential files from git tracking
- Created `.example` placeholder files
- This documentation

### Contact
If you need help with credential rotation, contact the security team.
