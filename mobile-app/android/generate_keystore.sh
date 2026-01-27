#!/bin/bash

# Generate Android keystore for signing
# Usage: ./generate_keystore.sh

KEYSTORE_FILE="../keystore.jks"
KEY_ALIAS="jobswipe_key"
STORE_PASSWORD="store_password_placeholder"
KEY_PASSWORD="key_password_placeholder"

if [ -f "$KEYSTORE_FILE" ]; then
    echo "Keystore already exists at $KEYSTORE_FILE"
    exit 1
fi

keytool -genkeypair \
    -v \
    -keystore "$KEYSTORE_FILE" \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -alias "$KEY_ALIAS" \
    -storepass "$STORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -dname "CN=JobSwipe, OU=Development, O=JobSwipe, L=City, ST=State, C=US"

echo "Keystore generated at $KEYSTORE_FILE"
echo "Update android/gradle.properties with the actual passwords"