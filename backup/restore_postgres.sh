#!/bin/bash

# JobSwipe PostgreSQL Restore Script
# Restores encrypted backups from cloud storage

set -e

# Configuration
RESTORE_DIR="/tmp/jobswipe_restore"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file-name>"
    echo "Example: $0 jobswipe_backup_20240126_020000.sql.gz.enc"
    exit 1
fi

# Database connection details (from environment variables)
DB_HOST=${DATABASE_URL#postgresql://}
DB_HOST=${DB_HOST%%/*}
DB_USER=${DATABASE_URL#postgresql://}
DB_USER=${DB_USER%%:*}
DB_PASSWORD=${DATABASE_URL#postgresql://*:}
DB_PASSWORD=${DB_PASSWORD%%@*}
DB_NAME=${DATABASE_URL##*/}

# AWS S3 configuration
S3_BUCKET=${AWS_S3_BUCKET_NAME}
S3_REGION=${AWS_S3_REGION:-us-east-1}

# Encryption configuration
ENCRYPTION_PASSWORD=${ENCRYPTION_PASSWORD}

# Create restore directory
mkdir -p "$RESTORE_DIR"

echo "Starting PostgreSQL restore from: $BACKUP_FILE"

# Download from S3
echo "Downloading backup from S3..."
aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_FILE}" "${RESTORE_DIR}/${BACKUP_FILE}" \
    --region "$S3_REGION"

# Decrypt the backup
echo "Decrypting backup..."
DECRYPTED_FILE="${RESTORE_DIR}/${BACKUP_FILE%.enc}"
openssl enc -d -aes-256-cbc \
    -pbkdf2 \
    -in "${RESTORE_DIR}/${BACKUP_FILE}" \
    -out "$DECRYPTED_FILE" \
    -k "$ENCRYPTION_PASSWORD"

# Decompress the backup
echo "Decompressing backup..."
BACKUP_FILE_UNCOMPRESSED="${DECRYPTED_FILE%.gz}"
gunzip "$DECRYPTED_FILE"

# Terminate active connections to the database
echo "Terminating active connections to database..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# Drop and recreate the database
echo "Recreating database..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "DROP DATABASE IF EXISTS $DB_NAME;"

PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "CREATE DATABASE $DB_NAME;"

# Restore the backup
echo "Restoring database..."
PGPASSWORD="$DB_PASSWORD" pg_restore \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    "$BACKUP_FILE_UNCOMPRESSED"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$RESTORE_DIR"

echo "Database restore completed successfully from: $BACKUP_FILE"