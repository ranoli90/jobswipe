#!/bin/bash
#
# Incremental Backup Script using pg_basebackup
#
# This script performs incremental backups of PostgreSQL databases using
# pg_basebackup with WAL archiving support for Point-in-Time Recovery (PITR).
#
# Features:
# - Incremental backups using pg_basebackup
# - WAL archiving for PITR capability
# - Backup verification and integrity checks
# - Encryption at rest using GPG
# - Compression using pigz (parallel gzip)
# - Retention policy management
# - Cloud storage upload (AWS S3, GCS, Azure)
#
# Usage: ./incremental_backup.sh [full|incremental|verify|cleanup]
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/var/backups/postgres}"
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-/var/backups/postgres/wal}"
BACKUP_LOG_DIR="${BACKUP_LOG_DIR:-/var/log/postgres-backup}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/backup/encryption.key}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
INCREMENTAL_RETENTION_DAYS="${INCREMENTAL_RETENTION_DAYS:-7}"

# Database configuration
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDATABASE="${PGDATABASE:-postgres}"
PGPASSWORD="${PGPASSWORD:-}"

# Cloud storage configuration
S3_BUCKET="${S3_BUCKET:-}"
S3_REGION="${S3_REGION:-us-east-1}"
GCS_BUCKET="${GCS_BUCKET:-}"
AZURE_CONTAINER="${AZURE_CONTAINER:-}"

# Compression and encryption
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-true}"
PARALLEL_WORKERS="${PARALLEL_WORKERS:-4}"

# Logging
LOG_FILE="${BACKUP_LOG_DIR}/backup-$(date +%Y%m%d-%H%M%S).log"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DATE=$(date +%Y%m%d)

# Export password for PostgreSQL commands
export PGPASSWORD

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Initialize directories
init_directories() {
    log_info "Initializing backup directories..."
    
    mkdir -p "$BACKUP_BASE_DIR"/{full,incremental,manifests}
    mkdir -p "$WAL_ARCHIVE_DIR"
    mkdir -p "$BACKUP_LOG_DIR"
    
    # Set appropriate permissions
    chmod 700 "$BACKUP_BASE_DIR"
    chmod 700 "$WAL_ARCHIVE_DIR"
    chmod 755 "$BACKUP_LOG_DIR"
    
    log_info "Backup directories initialized"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("pg_basebackup" "psql" "pg_verifybackup" "gzip")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check optional tools
    if command -v pigz &> /dev/null; then
        log_info "Using pigz for parallel compression"
        USE_PIGZ=true
    else
        log_warn "pigz not found, falling back to gzip"
        USE_PIGZ=false
    fi
    
    # Check encryption
    if [[ "$ENABLE_ENCRYPTION" == "true" ]]; then
        if ! command -v gpg &> /dev/null; then
            log_error "GPG not found but encryption is enabled"
            exit 1
        fi
        
        if [[ ! -f "$ENCRYPTION_KEY_FILE" ]]; then
            log_warn "Encryption key file not found, generating new key..."
            generate_encryption_key
        fi
    fi
    
    # Test database connection
    if ! psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT 1;" &> /dev/null; then
        log_error "Cannot connect to PostgreSQL database"
        exit 1
    fi
    
    # Check if WAL archiving is enabled
    local wal_level
    wal_level=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SHOW wal_level;" 2>/dev/null | xargs)
    if [[ "$wal_level" != "replica" && "$wal_level" != "logical" ]]; then
        log_warn "WAL level is '$wal_level', PITR may not work properly. Set wal_level to 'replica' or 'logical'."
    fi
    
    log_info "Prerequisites check passed"
}

# Generate encryption key
generate_encryption_key() {
    local key_dir
    key_dir=$(dirname "$ENCRYPTION_KEY_FILE")
    mkdir -p "$key_dir"
    chmod 700 "$key_dir"
    
    # Generate a random 256-bit key
    openssl rand -base64 32 > "$ENCRYPTION_KEY_FILE"
    chmod 400 "$ENCRYPTION_KEY_FILE"
    
    log_info "Encryption key generated: $ENCRYPTION_KEY_FILE"
    log_warn "IMPORTANT: Store this key securely! Without it, backups cannot be decrypted."
}

# Encrypt file
encrypt_file() {
    local input_file="$1"
    local output_file="${2:-$input_file.gpg}"
    
    if [[ "$ENABLE_ENCRYPTION" != "true" ]]; then
        mv "$input_file" "$output_file"
        return 0
    fi
    
    log_info "Encrypting: $input_file"
    
    gpg --symmetric \
        --cipher-algo AES256 \
        --compress-algo 0 \
        --passphrase-file "$ENCRYPTION_KEY_FILE" \
        --batch \
        --yes \
        --output "$output_file" \
        "$input_file"
    
    rm -f "$input_file"
    log_info "Encrypted: $output_file"
}

# Decrypt file
decrypt_file() {
    local input_file="$1"
    local output_file="$2"
    
    log_info "Decrypting: $input_file"
    
    gpg --decrypt \
        --passphrase-file "$ENCRYPTION_KEY_FILE" \
        --batch \
        --yes \
        --output "$output_file" \
        "$input_file"
    
    log_info "Decrypted: $output_file"
}

# Compress directory
compress_directory() {
    local input_dir="$1"
    local output_file="$2"
    
    log_info "Compressing: $input_dir -> $output_file"
    
    if [[ "$USE_PIGZ" == "true" ]]; then
        tar -cf - -C "$(dirname "$input_dir")" "$(basename "$input_dir")" | \
            pigz -p "$PARALLEL_WORKERS" -"$COMPRESSION_LEVEL" > "$output_file"
    else
        tar -czf "$output_file" -C "$(dirname "$input_dir")" "$(basename "$input_dir")"
    fi
    
    local original_size
    local compressed_size
    original_size=$(du -sb "$input_dir" | cut -f1)
    compressed_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file")
    
    local ratio
    ratio=$(echo "scale=2; ($original_size - $compressed_size) * 100 / $original_size" | bc)
    log_info "Compression ratio: ${ratio}% (${original_size} -> ${compressed_size} bytes)"
}

# Decompress archive
decompress_archive() {
    local input_file="$1"
    local output_dir="$2"
    
    log_info "Decompressing: $input_file -> $output_dir"
    
    mkdir -p "$output_dir"
    
    if [[ "$USE_PIGZ" == "true" ]]; then
        pigz -dc "$input_file" | tar -xf - -C "$output_dir"
    else
        tar -xzf "$input_file" -C "$output_dir"
    fi
    
    log_info "Decompressed successfully"
}

# Get last backup information
get_last_backup_info() {
    local backup_type="$1"
    local manifest_file="$BACKUP_BASE_DIR/manifests/${backup_type}-latest.json"
    
    if [[ -f "$manifest_file" ]]; then
        cat "$manifest_file"
    else
        echo "{}"
    fi
}

# Create backup manifest
create_manifest() {
    local backup_type="$1"
    local backup_path="$2"
    local backup_size="$3"
    local checksum="$4"
    local parent_backup="${5:-null}"
    
    local manifest
    manifest=$(cat <<EOF
{
    "version": "1.0",
    "backup_type": "$backup_type",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "backup_path": "$backup_path",
    "backup_size": $backup_size,
    "checksum": "$checksum",
    "parent_backup": $parent_backup,
    "database": {
        "host": "$PGHOST",
        "port": $PGPORT,
        "database": "$PGDATABASE",
        "user": "$PGUSER"
    },
    "postgresql_version": "$(psql -V | awk '{print $3}')",
    "wal_level": "$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SHOW wal_level;" 2>/dev/null | xargs)",
    "encryption": $([[ "$ENABLE_ENCRYPTION" == "true" ]] && echo "true" || echo "false"),
    "compression": {
        "enabled": true,
        "tool": $([[ "$USE_PIGZ" == "true" ]] && echo '"pigz"' || echo '"gzip"'),
        "level": $COMPRESSION_LEVEL
    },
    "retention_days": $([[ "$backup_type" == "full" ]] && echo "$RETENTION_DAYS" || echo "$INCREMENTAL_RETENTION_DAYS")
}
EOF
)
    
    echo "$manifest"
}

# Save manifest
save_manifest() {
    local backup_type="$1"
    local manifest="$2"
    
    local manifest_file="$BACKUP_BASE_DIR/manifests/${backup_type}-${TIMESTAMP}.json"
    local latest_manifest="$BACKUP_BASE_DIR/manifests/${backup_type}-latest.json"
    
    echo "$manifest" > "$manifest_file"
    cp "$manifest_file" "$latest_manifest"
    
    log_info "Manifest saved: $manifest_file"
}

# Calculate checksum
calculate_checksum() {
    local file="$1"
    sha256sum "$file" | awk '{print $1}'
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    local expected_checksum="$2"
    
    log_info "Verifying backup integrity: $backup_file"
    
    # Check file exists
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Verify checksum
    local actual_checksum
    actual_checksum=$(calculate_checksum "$backup_file")
    
    if [[ "$actual_checksum" != "$expected_checksum" ]]; then
        log_error "Checksum mismatch! Expected: $expected_checksum, Got: $actual_checksum"
        return 1
    fi
    
    log_info "Checksum verified: $actual_checksum"
    
    # Test archive integrity
    if [[ "$backup_file" == *.gpg ]]; then
        log_info "Skipping archive test for encrypted file (decrypt first)"
        return 0
    fi
    
    if [[ "$USE_PIGZ" == "true" ]]; then
        if ! pigz -t "$backup_file" 2>/dev/null; then
            log_error "Archive integrity test failed"
            return 1
        fi
    else
        if ! gzip -t "$backup_file" 2>/dev/null; then
            log_error "Archive integrity test failed"
            return 1
        fi
    fi
    
    log_info "Archive integrity verified"
    return 0
}

# Perform full backup
perform_full_backup() {
    log_info "Starting full backup..."
    
    local backup_dir="$BACKUP_BASE_DIR/full/backup-${TIMESTAMP}"
    local archive_file="${backup_dir}.tar.gz"
    local encrypted_file="${archive_file}.gpg"
    
    # Create backup directory
    mkdir -p "$backup_dir"
    
    # Perform pg_basebackup
    log_info "Running pg_basebackup..."
    pg_basebackup \
