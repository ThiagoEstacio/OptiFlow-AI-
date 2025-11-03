#!/bin/bash
#
# SmartPort Restore Script
# Restores PostgreSQL and InfluxDB databases from backup
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="/backups"
POSTGRES_BACKUP_DIR="$BACKUP_DIR/postgres"
INFLUX_BACKUP_DIR="$BACKUP_DIR/influxdb"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_prompt() {
    echo -e "${BLUE}[PROMPT]${NC} $1"
}

# ================================
# List Available Backups
# ================================
list_backups() {
    log_info "Available PostgreSQL backups:"
    echo "----------------------------------------"
    ls -lh "$POSTGRES_BACKUP_DIR"/*.sql.gz 2>/dev/null | nl || log_warn "No PostgreSQL backups found"
    echo ""

    log_info "Available InfluxDB backups:"
    echo "----------------------------------------"
    ls -lh "$INFLUX_BACKUP_DIR"/*.tar.gz 2>/dev/null | nl || log_warn "No InfluxDB backups found"
    echo ""
}

# ================================
# Restore PostgreSQL
# ================================
restore_postgres() {
    local BACKUP_FILE=$1

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        return 1
    fi

    log_warn "This will DROP and RECREATE the database!"
    log_prompt "Are you sure you want to restore PostgreSQL from $BACKUP_FILE? (yes/no)"
    read -r CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled"
        return 1
    fi

    log_info "Restoring PostgreSQL from $BACKUP_FILE..."

    # Drop existing connections
    psql -U "$POSTGRES_USER" -h "$PGHOST" -d postgres -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" || true

    # Drop and recreate database
    dropdb -U "$POSTGRES_USER" -h "$PGHOST" --if-exists "$POSTGRES_DB"
    createdb -U "$POSTGRES_USER" -h "$PGHOST" "$POSTGRES_DB"

    # Restore from backup
    if gunzip -c "$BACKUP_FILE" | psql -U "$POSTGRES_USER" -h "$PGHOST" "$POSTGRES_DB"; then
        log_info "PostgreSQL restored successfully!"
        return 0
    else
        log_error "PostgreSQL restore failed!"
        return 1
    fi
}

# ================================
# Restore InfluxDB
# ================================
restore_influxdb() {
    local BACKUP_FILE=$1

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        return 1
    fi

    log_warn "This will restore InfluxDB data!"
    log_prompt "Are you sure you want to restore InfluxDB from $BACKUP_FILE? (yes/no)"
    read -r CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled"
        return 1
    fi

    log_info "Restoring InfluxDB from $BACKUP_FILE..."

    # Extract backup
    TEMP_DIR="/tmp/influxdb_restore_$$"
    mkdir -p "$TEMP_DIR"
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

    # Find the backup directory
    BACKUP_PATH=$(find "$TEMP_DIR" -type d -name "influxdb_backup_*" | head -1)

    if [ -z "$BACKUP_PATH" ]; then
        log_error "Could not find backup data in archive"
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Restore using influx CLI
    if influx restore "$BACKUP_PATH" \
        --host http://influxdb:8086 \
        --token "$INFLUX_TOKEN" \
        --org "$INFLUX_ORG" \
        --full; then

        log_info "InfluxDB restored successfully!"
        rm -rf "$TEMP_DIR"
        return 0
    else
        log_error "InfluxDB restore failed!"
        rm -rf "$TEMP_DIR"
        return 1
    fi
}

# ================================
# Interactive Restore
# ================================
interactive_restore() {
    log_info "SmartPort Interactive Restore"
    echo "======================================"
    echo ""

    list_backups

    log_prompt "What would you like to restore?"
    echo "1) PostgreSQL"
    echo "2) InfluxDB"
    echo "3) Both"
    echo "4) Cancel"
    read -r CHOICE

    case $CHOICE in
        1)
            log_prompt "Enter PostgreSQL backup filename:"
            read -r PG_FILE
            restore_postgres "$POSTGRES_BACKUP_DIR/$PG_FILE"
            ;;
        2)
            log_prompt "Enter InfluxDB backup filename:"
            read -r INFLUX_FILE
            restore_influxdb "$INFLUX_BACKUP_DIR/$INFLUX_FILE"
            ;;
        3)
            log_prompt "Enter PostgreSQL backup filename:"
            read -r PG_FILE
            log_prompt "Enter InfluxDB backup filename:"
            read -r INFLUX_FILE

            restore_postgres "$POSTGRES_BACKUP_DIR/$PG_FILE"
            restore_influxdb "$INFLUX_BACKUP_DIR/$INFLUX_FILE"
            ;;
        4)
            log_info "Restore cancelled"
            exit 0
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
}

# ================================
# Restore Latest Backups
# ================================
restore_latest() {
    log_warn "This will restore from the LATEST backups!"
    log_prompt "Are you sure? (yes/no)"
    read -r CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi

    restore_postgres "$POSTGRES_BACKUP_DIR/latest.sql.gz"
    restore_influxdb "$INFLUX_BACKUP_DIR/latest.tar.gz"
}

# ================================
# Main Execution
# ================================

if [ "$1" == "--latest" ]; then
    restore_latest
elif [ "$1" == "--postgres" ] && [ -n "$2" ]; then
    restore_postgres "$2"
elif [ "$1" == "--influxdb" ] && [ -n "$2" ]; then
    restore_influxdb "$2"
elif [ "$1" == "--list" ]; then
    list_backups
else
    interactive_restore
fi
