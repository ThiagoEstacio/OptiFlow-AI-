#!/bin/bash
# ============================================
# OptiFlow AI Platform - Automated Backup Script
# ============================================
#
# Backs up PostgreSQL, InfluxDB, Redis, and configuration
#
# Usage:
#   ./backup.sh                    # Full backup
#   ./backup.sh postgres           # PostgreSQL only
#   ./backup.sh influxdb           # InfluxDB only
#   ./backup.sh redis              # Redis only
#   ./backup.sh config             # Configuration only
#   ./backup.sh --restore <date>   # Restore from backup (YYYYMMDD)
#   ./backup.sh verify             # Verify latest backups
#   ./backup.sh report             # Generate backup report
#
# Environment variables:
#   BACKUP_DIR         - Backup destination (default: /backups)
#   BACKUP_KEEP_DAYS   - Days to keep backups (default: 30)
#
# ============================================

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_BACKUP_DIR="$BACKUP_DIR/postgres"
INFLUX_BACKUP_DIR="$BACKUP_DIR/influxdb"
REDIS_BACKUP_DIR="$BACKUP_DIR/redis"
CONFIG_BACKUP_DIR="$BACKUP_DIR/config"
LOG_DIR="$BACKUP_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=${BACKUP_KEEP_DAYS:-30}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if backup is enabled
if [ "${BACKUP_ENABLED:-true}" != "true" ]; then
    log_warn "Backup is disabled. Set BACKUP_ENABLED=true to enable."
    exit 0
fi

log_info "Starting SmartPort backup at $(date)"

# ================================
# PostgreSQL Backup
# ================================
backup_postgres() {
    log_info "Backing up PostgreSQL database..."

    POSTGRES_FILE="$POSTGRES_BACKUP_DIR/smartport_postgres_${TIMESTAMP}.sql.gz"

    if pg_dump -U "$POSTGRES_USER" -h "$PGHOST" "$POSTGRES_DB" | gzip > "$POSTGRES_FILE"; then
        log_info "PostgreSQL backup created: $POSTGRES_FILE"

        # Get file size
        SIZE=$(du -h "$POSTGRES_FILE" | cut -f1)
        log_info "Backup size: $SIZE"

        # Create latest symlink
        ln -sf "$(basename "$POSTGRES_FILE")" "$POSTGRES_BACKUP_DIR/latest.sql.gz"

        return 0
    else
        log_error "PostgreSQL backup failed!"
        return 1
    fi
}

# ================================
# InfluxDB Backup
# ================================
backup_influxdb() {
    log_info "Backing up InfluxDB database..."

    INFLUX_FILE="$INFLUX_BACKUP_DIR/smartport_influxdb_${TIMESTAMP}.tar.gz"
    TEMP_BACKUP_DIR="/tmp/influxdb_backup_${TIMESTAMP}"

    # Create temporary backup directory
    mkdir -p "$TEMP_BACKUP_DIR"

    # Backup using influx CLI
    if influx backup "$TEMP_BACKUP_DIR" \
        --host http://influxdb:8086 \
        --token "$INFLUX_TOKEN" \
        --org "$INFLUX_ORG"; then

        # Compress the backup
        tar -czf "$INFLUX_FILE" -C /tmp "influxdb_backup_${TIMESTAMP}"

        # Clean up temp directory
        rm -rf "$TEMP_BACKUP_DIR"

        log_info "InfluxDB backup created: $INFLUX_FILE"

        # Get file size
        SIZE=$(du -h "$INFLUX_FILE" | cut -f1)
        log_info "Backup size: $SIZE"

        # Create latest symlink
        ln -sf "$(basename "$INFLUX_FILE")" "$INFLUX_BACKUP_DIR/latest.tar.gz"

        return 0
    else
        log_error "InfluxDB backup failed!"
        rm -rf "$TEMP_BACKUP_DIR"
        return 1
    fi
}

# ================================
# Cleanup Old Backups
# ================================
cleanup_old_backups() {
    log_info "Cleaning up backups older than $KEEP_DAYS days..."

    # PostgreSQL backups
    DELETED_PG=$(find "$POSTGRES_BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -type f -delete -print | wc -l)
    log_info "Deleted $DELETED_PG old PostgreSQL backup(s)"

    # InfluxDB backups
    DELETED_INFLUX=$(find "$INFLUX_BACKUP_DIR" -name "*.tar.gz" -mtime +$KEEP_DAYS -type f -delete -print | wc -l)
    log_info "Deleted $DELETED_INFLUX old InfluxDB backup(s)"
}

# ================================
# Verify Backups
# ================================
verify_backups() {
    log_info "Verifying backups..."

    # Check PostgreSQL backup
    if [ -f "$POSTGRES_BACKUP_DIR/latest.sql.gz" ]; then
        if gzip -t "$POSTGRES_BACKUP_DIR/latest.sql.gz" 2>/dev/null; then
            log_info "PostgreSQL backup verification: OK"
        else
            log_error "PostgreSQL backup verification: FAILED (corrupted)"
            return 1
        fi
    else
        log_error "PostgreSQL backup not found"
        return 1
    fi

    # Check InfluxDB backup
    if [ -f "$INFLUX_BACKUP_DIR/latest.tar.gz" ]; then
        if tar -tzf "$INFLUX_BACKUP_DIR/latest.tar.gz" >/dev/null 2>&1; then
            log_info "InfluxDB backup verification: OK"
        else
            log_error "InfluxDB backup verification: FAILED (corrupted)"
            return 1
        fi
    else
        log_error "InfluxDB backup not found"
        return 1
    fi

    return 0
}

# ================================
# Generate Backup Report
# ================================
generate_report() {
    log_info "Generating backup report..."

    REPORT_FILE="$BACKUP_DIR/backup_report_${TIMESTAMP}.txt"

    cat > "$REPORT_FILE" <<EOF
SmartPort Backup Report
=======================
Date: $(date)
Hostname: $(hostname)

PostgreSQL Backups:
-------------------
$(ls -lh "$POSTGRES_BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "No backups found")

Total PostgreSQL backups: $(ls "$POSTGRES_BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l)
Total size: $(du -sh "$POSTGRES_BACKUP_DIR" | cut -f1)

InfluxDB Backups:
-----------------
$(ls -lh "$INFLUX_BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found")

Total InfluxDB backups: $(ls "$INFLUX_BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
Total size: $(du -sh "$INFLUX_BACKUP_DIR" | cut -f1)

Retention Policy: $KEEP_DAYS days
EOF

    log_info "Report generated: $REPORT_FILE"
    cat "$REPORT_FILE"
}

# ================================
# Redis Backup
# ================================
backup_redis() {
    log_info "Backing up Redis database..."

    REDIS_FILE="$REDIS_BACKUP_DIR/optiflow_redis_${TIMESTAMP}.rdb.gz"

    # Trigger BGSAVE
    if redis-cli -h redis -a "${REDIS_PASSWORD:-optiflow_redis_password}" BGSAVE 2>/dev/null; then
        sleep 3  # Wait for save to complete

        if [ -f "/data/dump.rdb" ]; then
            gzip -c /data/dump.rdb > "$REDIS_FILE"
            SIZE=$(du -h "$REDIS_FILE" | cut -f1)
            log_info "Redis backup created: $REDIS_FILE ($SIZE)"
            ln -sf "$(basename "$REDIS_FILE")" "$REDIS_BACKUP_DIR/latest.rdb.gz"
            return 0
        fi
    fi

    log_warn "Redis backup skipped (not available or no data)"
    return 0
}

# ================================
# Configuration Backup
# ================================
backup_config() {
    log_info "Backing up configuration..."

    CONFIG_FILE="$CONFIG_BACKUP_DIR/optiflow_config_${TIMESTAMP}.tar.gz"

    tar -czf "$CONFIG_FILE" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        -C /app \
        .env* \
        docker-compose*.yml \
        nginx/ \
        monitoring/ \
        gateway/config/ \
        2>/dev/null || true

    if [ -f "$CONFIG_FILE" ]; then
        SIZE=$(du -h "$CONFIG_FILE" | cut -f1)
        log_info "Config backup created: $CONFIG_FILE ($SIZE)"
        ln -sf "$(basename "$CONFIG_FILE")" "$CONFIG_BACKUP_DIR/latest.tar.gz"
        return 0
    fi

    log_warn "Config backup may be incomplete"
    return 0
}

# ================================
# Restore from Backup
# ================================
restore_backup() {
    local restore_date=$1

    if [ -z "$restore_date" ]; then
        log_error "Usage: ./backup.sh --restore YYYYMMDD"
        exit 1
    fi

    log_warn "This will restore data from backups dated ${restore_date}"
    log_warn "Current data will be OVERWRITTEN!"
    read -p "Are you sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi

    # Restore PostgreSQL
    local pg_backup=$(ls "${POSTGRES_BACKUP_DIR}/"*${restore_date}*.sql.gz 2>/dev/null | head -1)
    if [ -n "$pg_backup" ]; then
        log_info "Restoring PostgreSQL from: ${pg_backup}"
        gunzip -c "$pg_backup" | psql -U "$POSTGRES_USER" -h "$PGHOST" -d "$POSTGRES_DB"
        log_info "PostgreSQL restored successfully"
    else
        log_warn "No PostgreSQL backup found for date: ${restore_date}"
    fi

    # Restore InfluxDB
    local influx_backup=$(ls "${INFLUX_BACKUP_DIR}/"*${restore_date}*.tar.gz 2>/dev/null | head -1)
    if [ -n "$influx_backup" ]; then
        log_info "Restoring InfluxDB from: ${influx_backup}"
        local temp_dir=$(mktemp -d)
        tar -xzf "$influx_backup" -C "$temp_dir"
        influx restore "$temp_dir"/* \
            --host http://influxdb:8086 \
            --token "$INFLUX_TOKEN" \
            --org "$INFLUX_ORG" \
            --full
        rm -rf "$temp_dir"
        log_info "InfluxDB restored successfully"
    else
        log_warn "No InfluxDB backup found for date: ${restore_date}"
    fi
}

# ================================
# Full Backup
# ================================
full_backup() {
    log_info "Starting full OptiFlow backup..."
    local start_time=$(date +%s)

    BACKUP_STATUS=0

    if ! backup_postgres; then
        BACKUP_STATUS=1
    fi

    if ! backup_influxdb; then
        BACKUP_STATUS=1
    fi

    backup_redis || true
    backup_config || true

    cleanup_old_backups

    if ! verify_backups; then
        BACKUP_STATUS=1
        log_error "Backup verification failed!"
    fi

    generate_report

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $BACKUP_STATUS -eq 0 ]; then
        log_info "Full backup completed successfully in ${duration}s"
        exit 0
    else
        log_error "Backup completed with errors in ${duration}s"
        exit 1
    fi
}

# ================================
# Main Execution
# ================================

# Create backup directories if they don't exist
mkdir -p "$POSTGRES_BACKUP_DIR" "$INFLUX_BACKUP_DIR" "$REDIS_BACKUP_DIR" "$CONFIG_BACKUP_DIR" "$LOG_DIR"

# Check if backup is enabled
if [ "${BACKUP_ENABLED:-true}" != "true" ]; then
    log_warn "Backup is disabled. Set BACKUP_ENABLED=true to enable."
    exit 0
fi

# Handle command line arguments
case "${1:-}" in
    postgres)
        backup_postgres
        ;;
    influxdb)
        backup_influxdb
        ;;
    redis)
        backup_redis
        ;;
    config)
        backup_config
        ;;
    --restore)
        restore_backup "$2"
        ;;
    verify)
        verify_backups
        ;;
    report)
        generate_report
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    *)
        full_backup
        ;;
esac
