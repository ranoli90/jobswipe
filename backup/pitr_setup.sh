#!/bin/bash

# JobSwipe PostgreSQL Point-in-Time Recovery (PITR) Setup Script
# Configures WAL archiving and streaming replication for PITR
#
# This script sets up the necessary configuration for PostgreSQL
# to support Point-in-Time Recovery using WAL archiving.
#
# Usage: ./pitr_setup.sh [setup|verify|disable]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PG_CONF_DIR="${PG_CONF_DIR:-/etc/postgresql/$(psql -V | awk '{print $3}' | cut -d'.' -f1,2)/main}"
PG_DATA_DIR="${PG_DATA_DIR:-/var/lib/postgresql/$(psql -V | awk '{print $3}' | cut -d'.' -f1,2)/main}"
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-/var/backups/postgres/wal}"
REPLICATION_USER="${REPLICATION_USER:-repluser}"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-$(openssl rand -base64 16)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running as root or postgres user
    if [[ "$(id -u)" -ne 0 && "$(whoami)" != "postgres" ]]; then
        log_error "Script must be run as root or postgres user"
        exit 1
    fi

    # Check required tools
    local required_tools=("psql" "pg_ctl" "openssl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Check PostgreSQL is running
    if ! pg_ctl -D "$PG_DATA_DIR" status &> /dev/null; then
        log_error "PostgreSQL is not running"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Setup WAL archiving configuration
setup_wal_archiving() {
    log_info "Setting up WAL archiving..."

    # Create WAL archive directory
    mkdir -p "$WAL_ARCHIVE_DIR"
    chown postgres:postgres "$WAL_ARCHIVE_DIR"
    chmod 700 "$WAL_ARCHIVE_DIR"

    log_info "WAL archive directory created: $WAL_ARCHIVE_DIR"

    # Backup current postgresql.conf
    local pg_conf_backup="${PG_CONF_DIR}/postgresql.conf.backup.$(date +%Y%m%d%H%M%S)"
    cp "${PG_CONF_DIR}/postgresql.conf" "$pg_conf_backup"
    log_info "Backup of postgresql.conf created: $pg_conf_backup"

    # Configure WAL settings
    local wal_settings=(
        "wal_level = replica"
        "archive_mode = on"
        "archive_command = 'cp %p ${WAL_ARCHIVE_DIR}/%f'"
        "archive_timeout = 600"
        "max_wal_senders = 10"
        "wal_keep_size = 1024"
    )

    log_info "Updating postgresql.conf with WAL settings..."
    for setting in "${wal_settings[@]}"; do
        local key="${setting%% =*}"
        if grep -qE "^${key}\s*=" "${PG_CONF_DIR}/postgresql.conf"; then
            # Replace existing setting
            sed -i "s/^${key}\s*=.*$/${setting}/" "${PG_CONF_DIR}/postgresql.conf"
        else
            # Add new setting at end of file
            echo "$setting" >> "${PG_CONF_DIR}/postgresql.conf"
        fi
    done

    # Backup current pg_hba.conf
    local pg_hba_backup="${PG_CONF_DIR}/pg_hba.conf.backup.$(date +%Y%m%d%H%M%S)"
    cp "${PG_CONF_DIR}/pg_hba.conf" "$pg_hba_backup"
    log_info "Backup of pg_hba.conf created: $pg_hba_backup"

    # Add replication user authentication
    if ! grep -qE "host.*replication.*${REPLICATION_USER}" "${PG_CONF_DIR}/pg_hba.conf"; then
        log_info "Adding replication user authentication to pg_hba.conf..."
        echo "host    replication     ${REPLICATION_USER}    0.0.0.0/0    md5" >> "${PG_CONF_DIR}/pg_hba.conf"
        echo "host    replication     ${REPLICATION_USER}    ::/0         md5" >> "${PG_CONF_DIR}/pg_hba.conf"
    fi

    log_info "WAL archiving configuration completed"
}

# Create replication user
create_replication_user() {
    log_info "Creating replication user: $REPLICATION_USER"

    # Check if user exists
    if psql -U postgres -t -c "SELECT 1 FROM pg_roles WHERE rolname = '${REPLICATION_USER}'" | grep -q 1; then
        log_warn "Replication user $REPLICATION_USER already exists"
        return 0
    fi

    # Create replication user with appropriate permissions
    psql -U postgres <<SQL
CREATE ROLE ${REPLICATION_USER} WITH
    REPLICATION
    LOGIN
    PASSWORD '${REPLICATION_PASSWORD}'
    CONNECTION LIMIT 5
    VALID UNTIL 'infinity';
SQL

    log_info "Replication user created successfully"
}

# Restart PostgreSQL to apply changes
restart_postgresql() {
    log_info "Restarting PostgreSQL to apply changes..."
    pg_ctl -D "$PG_DATA_DIR" restart -m fast
    sleep 5

    # Verify PostgreSQL is running
    if ! pg_ctl -D "$PG_DATA_DIR" status &> /dev/null; then
        log_error "PostgreSQL failed to restart"
        exit 1
    fi

    log_info "PostgreSQL restarted successfully"
}

# Verify WAL archiving is working
verify_wal_archiving() {
    log_info "Verifying WAL archiving..."

    # Check current WAL settings
    local wal_level
    wal_level=$(psql -U postgres -t -c "SHOW wal_level;" | xargs)
    log_info "WAL level: $wal_level"

    local archive_mode
    archive_mode=$(psql -U postgres -t -c "SHOW archive_mode;" | xargs)
    log_info "Archive mode: $archive_mode"

    local archive_command
    archive_command=$(psql -U postgres -t -c "SHOW archive_command;" | xargs)
    log_info "Archive command: $archive_command"

    # Check if we can create a new WAL segment
    log_info "Forcing WAL switch to test archiving..."
    psql -U postgres -c "SELECT pg_switch_wal();" > /dev/null

    # Wait for archive to be created
    sleep 2

    # Check if WAL file exists in archive
    local wal_file_count
    wal_file_count=$(ls -1 "$WAL_ARCHIVE_DIR" | grep -E "^[0-9A-F]{24}$" | wc -l)
    log_info "WAL files in archive: $wal_file_count"

    if [[ "$wal_level" != "replica" && "$wal_level" != "logical" ]]; then
        log_warn "WAL level should be replica or logical for PITR"
    fi

    if [[ "$archive_mode" != "on" ]]; then
        log_error "Archive mode is not enabled"
        exit 1
    fi

    if [[ "$wal_file_count" -eq 0 ]]; then
        log_error "No WAL files found in archive directory"
        exit 1
    fi

    log_info "WAL archiving verification passed"
}

# Verify replication user can connect
verify_replication_connection() {
    log_info "Verifying replication user connection..."

    # Test replication connection
    if ! psql -h localhost -U "$REPLICATION_USER" -d replication -c "SELECT 1;" &> /dev/null; then
        log_error "Cannot connect as replication user"
        exit 1
    fi

    log_info "Replication user connection verified"
}

# Disable WAL archiving
disable_wal_archiving() {
    log_info "Disabling WAL archiving..."

    # Update postgresql.conf
    local wal_settings=(
        "wal_level = minimal"
        "archive_mode = off"
        "max_wal_senders = 0"
        "wal_keep_size = 0"
    )

    for setting in "${wal_settings[@]}"; do
        local key="${setting%% =*}"
        if grep -qE "^${key}\s*=" "${PG_CONF_DIR}/postgresql.conf"; then
            sed -i "s/^${key}\s*=.*$/${setting}/" "${PG_CONF_DIR}/postgresql.conf"
        fi
    done

    # Remove replication user authentication from pg_hba.conf
    sed -i "/host.*replication.*${REPLICATION_USER}/d" "${PG_CONF_DIR}/pg_hba.conf"

    log_info "WAL archiving disabled"
}

# Drop replication user
drop_replication_user() {
    log_info "Dropping replication user: $REPLICATION_USER"

    if psql -U postgres -t -c "SELECT 1 FROM pg_roles WHERE rolname = '${REPLICATION_USER}'" | grep -q 1; then
        psql -U postgres -c "DROP ROLE ${REPLICATION_USER};"
        log_info "Replication user dropped"
    else
        log_warn "Replication user $REPLICATION_USER does not exist"
    fi
}

# Main function
main() {
    local action="${1:-setup}"

    case "$action" in
        setup)
            log_info "Starting PITR setup..."
            check_prerequisites
            setup_wal_archiving
            create_replication_user
            restart_postgresql
            verify_wal_archiving
            verify_replication_connection
            log_info "PITR setup completed successfully!"
            log_warn "IMPORTANT: Save the replication password securely!"
            log_info "Replication user: $REPLICATION_USER"
            log_info "Replication password: $REPLICATION_PASSWORD"
            ;;
        verify)
            log_info "Verifying PITR configuration..."
            check_prerequisites
            verify_wal_archiving
            verify_replication_connection
            log_info "PITR configuration is valid"
            ;;
        disable)
            log_info "Disabling PITR..."
            check_prerequisites
            disable_wal_archiving
            drop_replication_user
            restart_postgresql
            log_info "PITR disabled successfully"
            ;;
        *)
            echo "Usage: $0 [setup|verify|disable]"
            echo "  setup   - Configure PITR with WAL archiving"
            echo "  verify  - Verify PITR configuration"
            echo "  disable - Disable PITR and remove configuration"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
