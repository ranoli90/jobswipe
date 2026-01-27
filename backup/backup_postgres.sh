#!/bin/bash

# JobSwipe PostgreSQL Backup Script
# Creates encrypted backups and uploads to cloud storage

set -e

# Configuration
BACKUP_DIR="/tmp/jobswipe_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="jobswipe_backup_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_NAME}.sql.gz"
ENCRYPTED_FILE="${BACKUP_FILE}.enc"

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup: $BACKUP_NAME"

# Create backup using pg_dump
echo "Creating database dump..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="${BACKUP_DIR}/${BACKUP_NAME}.backup"

# Compress the backup
echo "Compressing backup..."
gzip "${BACKUP_DIR}/${BACKUP_NAME}.backup"

# Encrypt the backup
echo "Encrypting backup..."
openssl enc -aes-256-cbc \
    -salt \
    -pbkdf2 \
    -in "${BACKUP_DIR}/${BACKUP_NAME}.backup.gz" \
    -out "${BACKUP_DIR}/${ENCRYPTED_FILE}" \
    -k "$ENCRYPTION_PASSWORD"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "${BACKUP_DIR}/${ENCRYPTED_FILE}" "s3://${S3_BUCKET}/backups/${ENCRYPTED_FILE}" \
    --region "$S3_REGION" \
    --storage-class STANDARD_IA

# Verify upload
echo "Verifying upload..."
aws s3 ls "s3://${S3_BUCKET}/backups/${ENCRYPTED_FILE}" > /dev/null

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups..."
aws s3api list-objects-v2 \
    --bucket "$S3_BUCKET" \
    --prefix "backups/" \
    --query 'Contents[?LastModified<`'"$(date -d '7 days ago' +%Y-%m-%d)"'`].Key' \
    --output text | \
while read -r key; do
    if [ -n "$key" ]; then
        echo "Deleting old backup: $key"
        aws s3 rm "s3://${S3_BUCKET}/${key}"
    fi
done

# Clean up local files
echo "Cleaning up local files..."
rm -rf "$BACKUP_DIR"

echo "Backup completed successfully: $ENCRYPTED_FILE"
echo "Backup size: $(aws s3 ls s3://${S3_BUCKET}/backups/${ENCRYPTED_FILE} --summarize --human-readable | tail -n1 | awk '{print $3}')"