#!/bin/bash
#
# SmartPort Automated Backup Script
# Backs up PostgreSQL and InfluxDB databases
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="/backups"
POSTGRES_BACKUP_DIR="$BACKUP_DIR/postgres"
INFLUX_BACKUP_DIR="$BACKUP_DIR/influxdb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=${BACKUP_KEEP_DAYS:-7}

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
# Main Execution
# ================================

# Create backup directories if they don't exist
mkdir -p "$POSTGRES_BACKUP_DIR" "$INFLUX_BACKUP_DIR"

# Perform backups
BACKUP_STATUS=0

if ! backup_postgres; then
    BACKUP_STATUS=1
fi

if ! backup_influxdb; then
    BACKUP_STATUS=1
fi

# Cleanup old backups
cleanup_old_backups

# Verify backups
if ! verify_backups; then
    BACKUP_STATUS=1
    log_error "Backup verification failed!"
fi

# Generate report
generate_report

# Final status
if [ $BACKUP_STATUS -eq 0 ]; then
    log_info "Backup completed successfully at $(date)"
    exit 0
else
    log_error "Backup completed with errors at $(date)"
    exit 1
fi
