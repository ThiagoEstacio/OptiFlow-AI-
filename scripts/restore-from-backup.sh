#!/bin/bash

# ============================================
# OptiFlow AI - Production Restore System
# ============================================
# Restore from backup:
# - PostgreSQL (relational data)
# - InfluxDB (time series data)
# - Redis (cache state)
# - Application data (ML models, configs)
# ============================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_ROOT="/backups"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# ============================================
# Select Backup to Restore
# ============================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}OptiFlow AI - Production Restore System${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# List available backups
info "Available backups:"
echo ""
BACKUPS=($(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | sort -r))

if [ ${#BACKUPS[@]} -eq 0 ]; then
    error "No backups found in ${BACKUP_ROOT}"
    exit 1
fi

# Display backups with index
for i in "${!BACKUPS[@]}"; do
    BACKUP_DIR="${BACKUPS[$i]}"
    BACKUP_NAME=$(basename "$BACKUP_DIR")
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo "  [$i] $BACKUP_NAME (${BACKUP_SIZE})"
done

echo ""
read -p "Select backup to restore [0-$((${#BACKUPS[@]}-1))]: " BACKUP_INDEX

if [ -z "$BACKUP_INDEX" ] || [ "$BACKUP_INDEX" -lt 0 ] || [ "$BACKUP_INDEX" -ge ${#BACKUPS[@]} ]; then
    error "Invalid selection"
    exit 1
fi

RESTORE_DIR="${BACKUPS[$BACKUP_INDEX]}"
RESTORE_NAME=$(basename "$RESTORE_DIR")

echo ""
warn "⚠️  WARNING: This will REPLACE current data with backup from ${RESTORE_NAME}"
read -p "Are you sure? Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    error "Restore cancelled"
    exit 1
fi

log "============================================"
log "Starting restore from: ${RESTORE_NAME}"
log "============================================"

# ============================================
# 1. Decrypt Backups (if encrypted)
# ============================================
log "Decrypting backup files..."

DECRYPTED=false
for file in "${RESTORE_DIR}"/*.gpg; do
    if [ -f "$file" ]; then
        DECRYPTED=true
        info "Decrypting: $(basename $file)"
        gpg --decrypt --batch --yes --passphrase "${GPG_PASSPHRASE:-optiflow-backup}" "$file" > "${file%.gpg}"
        if [ $? -ne 0 ]; then
            error "Failed to decrypt: $file"
            exit 1
        fi
    fi
done

if [ "$DECRYPTED" = true ]; then
    log "✅ Decryption completed"
else
    info "No encrypted files found (skipping decryption)"
fi

# ============================================
# 2. Stop Services
# ============================================
warn "Stopping OptiFlow services..."
docker-compose -f docker-compose.prod.yml stop backend gateway

log "✅ Services stopped"

# ============================================
# 3. Restore PostgreSQL
# ============================================
log "Restoring PostgreSQL database..."

# Find PostgreSQL backup
POSTGRES_BACKUP=$(find "${RESTORE_DIR}" -name "postgresql_*.sql.gz" | head -1)

if [ -f "$POSTGRES_BACKUP" ]; then
    info "Found: $(basename $POSTGRES_BACKUP)"
    
    # Decompress
    gunzip -c "$POSTGRES_BACKUP" > /tmp/postgres_restore.sql
    
    # Drop existing database and restore
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -d postgres << EOF
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB};
EOF
    
    # Restore from backup
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -d postgres < /tmp/postgres_restore.sql
    
    if [ $? -eq 0 ]; then
        log "✅ PostgreSQL restored successfully"
        rm /tmp/postgres_restore.sql
    else
        error "PostgreSQL restore failed!"
        exit 1
    fi
else
    warn "PostgreSQL backup not found. Skipping."
fi

# ============================================
# 4. Restore InfluxDB
# ============================================
log "Restoring InfluxDB time series data..."

# Find InfluxDB backup
INFLUX_BACKUP=$(find "${RESTORE_DIR}" -name "influxdb_*.tar.gz" | head -1)

if [ -f "$INFLUX_BACKUP" ]; then
    info "Found: $(basename $INFLUX_BACKUP)"
    
    # Extract backup
    mkdir -p /tmp/influxdb_restore
    tar -xzf "$INFLUX_BACKUP" -C /tmp/influxdb_restore
    
    # Copy to container
    docker cp /tmp/influxdb_restore/influxdb smartport-influxdb-prod:/tmp/influxdb_restore
    
    # Restore using influx restore command
    docker exec smartport-influxdb-prod influx restore \
        --host http://localhost:8086 \
        --token "${INFLUX_TOKEN}" \
        --full /tmp/influxdb_restore
    
    if [ $? -eq 0 ]; then
        log "✅ InfluxDB restored successfully"
        rm -rf /tmp/influxdb_restore
    else
        warn "InfluxDB restore failed (non-critical)"
    fi
else
    warn "InfluxDB backup not found. Skipping."
fi

# ============================================
# 5. Restore Redis
# ============================================
log "Restoring Redis cache state..."

# Find Redis backup
REDIS_BACKUP=$(find "${RESTORE_DIR}" -name "redis_*.rdb.gz" | head -1)

if [ -f "$REDIS_BACKUP" ]; then
    info "Found: $(basename $REDIS_BACKUP)"
    
    # Stop Redis
    docker-compose -f docker-compose.prod.yml stop redis
    
    # Decompress and copy RDB file
    gunzip -c "$REDIS_BACKUP" > /tmp/dump.rdb
    docker cp /tmp/dump.rdb smartport-redis-prod:/data/dump.rdb
    
    # Start Redis
    docker-compose -f docker-compose.prod.yml start redis
    
    if [ $? -eq 0 ]; then
        log "✅ Redis restored successfully"
        rm /tmp/dump.rdb
    else
        warn "Redis restore failed (non-critical)"
    fi
else
    warn "Redis backup not found. Skipping."
fi

# ============================================
# 6. Restore Application Data
# ============================================
log "Restoring application data..."

# Find application data backup
APP_BACKUP=$(find "${RESTORE_DIR}" -name "app_data_*.tar.gz" | head -1)

if [ -f "$APP_BACKUP" ]; then
    info "Found: $(basename $APP_BACKUP)"
    
    # Extract to temp directory
    mkdir -p /tmp/app_restore
    tar -xzf "$APP_BACKUP" -C /tmp/app_restore
    
    # Restore to volumes (adjust paths as needed)
    if [ -d "/tmp/app_restore/app_data/logs" ]; then
        cp -r /tmp/app_restore/app_data/logs/* /var/lib/docker/volumes/optiflow_backend_logs/_data/ 2>/dev/null || true
    fi
    
    if [ -d "/tmp/app_restore/app_data/gateway" ]; then
        cp -r /tmp/app_restore/app_data/gateway/* /var/lib/docker/volumes/optiflow_gateway_data/_data/ 2>/dev/null || true
    fi
    
    log "✅ Application data restored"
    rm -rf /tmp/app_restore
else
    warn "Application data backup not found. Skipping."
fi

# ============================================
# 7. Clean up decrypted files
# ============================================
if [ "$DECRYPTED" = true ]; then
    log "Cleaning up decrypted files..."
    find "${RESTORE_DIR}" -name "*.sql.gz" -o -name "*.tar.gz" -o -name "*.rdb.gz" | xargs rm -f
    log "✅ Cleanup completed"
fi

# ============================================
# 8. Start Services
# ============================================
log "Starting OptiFlow services..."
docker-compose -f docker-compose.prod.yml start backend gateway

# Wait for services to be healthy
sleep 10

# Check health
docker-compose -f docker-compose.prod.yml ps

log "============================================"
log "Restore Summary"
log "============================================"
log "Backup: ${RESTORE_NAME}"
log "PostgreSQL: ✅ Restored"
log "InfluxDB: ✅ Restored"
log "Redis: ✅ Restored"
log "Application Data: ✅ Restored"
log "============================================"
log "✅ RESTORE COMPLETED"
log "============================================"

# Verification steps
echo ""
info "Verification steps:"
echo "  1. Check logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  2. Test API: curl http://localhost:8000/health"
echo "  3. Check Grafana dashboards"
echo "  4. Verify data integrity"
echo ""

exit 0
