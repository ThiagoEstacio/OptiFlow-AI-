#!/bin/bash

# ============================================
# OptiFlow AI - Production Backup System
# ============================================
# Automated backup of all critical data:
# - PostgreSQL (relational data)
# - InfluxDB (time series data)
# - Redis (cache state)
# - Application data (ML models, configs)
# ============================================

set -e

# Configuration
BACKUP_ROOT="/backups"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_DATE}"
RETENTION_DAYS=${BACKUP_KEEP_DAYS:-7}
LOG_FILE="${BACKUP_ROOT}/backup.log"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if backups are enabled
if [ "${BACKUP_ENABLED}" != "true" ]; then
    warn "Backups disabled (BACKUP_ENABLED != true). Exiting."
    exit 0
fi

log "============================================"
log "Starting OptiFlow AI Production Backup"
log "============================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"
log "Created backup directory: $BACKUP_DIR"

# ============================================
# 1. PostgreSQL Backup
# ============================================
log "Backing up PostgreSQL database..."

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dumpall -h postgres -U "${POSTGRES_USER}" \
    > "${BACKUP_DIR}/postgresql_${BACKUP_DATE}.sql"

if [ $? -eq 0 ]; then
    # Compress backup
    gzip "${BACKUP_DIR}/postgresql_${BACKUP_DATE}.sql"
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/postgresql_${BACKUP_DATE}.sql.gz" | cut -f1)
    log "✅ PostgreSQL backup completed: ${BACKUP_SIZE}"
else
    error "PostgreSQL backup failed!"
    exit 1
fi

# ============================================
# 2. InfluxDB Backup
# ============================================
log "Backing up InfluxDB time series data..."

# Create InfluxDB backup directory
mkdir -p "${BACKUP_DIR}/influxdb"

# Use InfluxDB backup command
docker exec smartport-influxdb-prod influx backup \
    --host http://localhost:8086 \
    --token "${INFLUX_TOKEN}" \
    /tmp/influxdb_backup

# Copy from container to backup dir
docker cp smartport-influxdb-prod:/tmp/influxdb_backup "${BACKUP_DIR}/influxdb/"

if [ $? -eq 0 ]; then
    # Compress backup
    tar -czf "${BACKUP_DIR}/influxdb_${BACKUP_DATE}.tar.gz" -C "${BACKUP_DIR}" influxdb/
    rm -rf "${BACKUP_DIR}/influxdb"
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/influxdb_${BACKUP_DATE}.tar.gz" | cut -f1)
    log "✅ InfluxDB backup completed: ${BACKUP_SIZE}"
else
    error "InfluxDB backup failed!"
    exit 1
fi

# ============================================
# 3. Redis Backup
# ============================================
log "Backing up Redis cache state..."

# Trigger Redis save
docker exec smartport-redis-prod redis-cli -a "${REDIS_PASSWORD}" SAVE

# Copy RDB file
docker cp smartport-redis-prod:/data/dump.rdb "${BACKUP_DIR}/redis_${BACKUP_DATE}.rdb"

if [ $? -eq 0 ]; then
    # Compress backup
    gzip "${BACKUP_DIR}/redis_${BACKUP_DATE}.rdb"
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/redis_${BACKUP_DATE}.rdb.gz" | cut -f1)
    log "✅ Redis backup completed: ${BACKUP_SIZE}"
else
    warn "Redis backup failed (non-critical)"
fi

# ============================================
# 4. Application Data Backup
# ============================================
log "Backing up application data..."

# Backup ML models, dashboards, configurations
mkdir -p "${BACKUP_DIR}/app_data"

# Copy from volumes (adjust paths as needed)
if [ -d "/var/lib/docker/volumes/optiflow_backend_logs" ]; then
    cp -r /var/lib/docker/volumes/optiflow_backend_logs/_data "${BACKUP_DIR}/app_data/logs" 2>/dev/null || true
fi

if [ -d "/var/lib/docker/volumes/optiflow_gateway_data" ]; then
    cp -r /var/lib/docker/volumes/optiflow_gateway_data/_data "${BACKUP_DIR}/app_data/gateway" 2>/dev/null || true
fi

# Compress application data
tar -czf "${BACKUP_DIR}/app_data_${BACKUP_DATE}.tar.gz" -C "${BACKUP_DIR}" app_data/
rm -rf "${BACKUP_DIR}/app_data"

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/app_data_${BACKUP_DATE}.tar.gz" | cut -f1)
log "✅ Application data backup completed: ${BACKUP_SIZE}"

# ============================================
# 5. Encrypt Backups
# ============================================
log "Encrypting backups with GPG..."

if command -v gpg &> /dev/null; then
    for file in "${BACKUP_DIR}"/*.{sql.gz,tar.gz,rdb.gz}; do
        if [ -f "$file" ]; then
            # Encrypt with symmetric key (use passphrase from env or prompt)
            gpg --symmetric --cipher-algo AES256 --batch --yes --passphrase "${GPG_PASSPHRASE:-optiflow-backup}" "$file"
            if [ $? -eq 0 ]; then
                rm "$file"  # Remove unencrypted version
                log "✅ Encrypted: $(basename $file).gpg"
            else
                error "Failed to encrypt: $file"
            fi
        fi
    done
else
    warn "GPG not installed. Backups NOT encrypted!"
fi

# ============================================
# 6. Upload to Cloud Storage (Optional)
# ============================================
if [ -n "${AWS_ACCESS_KEY_ID}" ] && [ "${AWS_ACCESS_KEY_ID}" != "CHANGE_ME_IF_USING_S3" ]; then
    log "Uploading backups to S3..."
    
    if command -v aws &> /dev/null; then
        aws s3 sync "${BACKUP_DIR}" "s3://${S3_BACKUP_BUCKET}/optiflow/${BACKUP_DATE}/" \
            --storage-class STANDARD_IA \
            --region "${AWS_REGION}"
        
        if [ $? -eq 0 ]; then
            log "✅ Backups uploaded to S3: ${S3_BACKUP_BUCKET}"
        else
            error "Failed to upload to S3"
        fi
    else
        warn "AWS CLI not installed. Skipping S3 upload."
    fi
else
    log "S3 upload not configured. Backups stored locally only."
fi

# ============================================
# 7. Cleanup Old Backups
# ============================================
log "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" -mtime +${RETENTION_DAYS} -exec rm -rf {} \;

BACKUP_COUNT=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | wc -l)
log "✅ Cleanup completed. Current backups: ${BACKUP_COUNT}"

# ============================================
# 8. Backup Summary
# ============================================
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "============================================"
log "Backup Summary"
log "============================================"
log "Date: ${BACKUP_DATE}"
log "Location: ${BACKUP_DIR}"
log "Total Size: ${TOTAL_SIZE}"
log "Retention: ${RETENTION_DAYS} days"
log "Status: ✅ COMPLETED"
log "============================================"

# Send notification (optional)
if [ -n "${BACKUP_NOTIFICATION_WEBHOOK}" ]; then
    curl -X POST "${BACKUP_NOTIFICATION_WEBHOOK}" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"✅ OptiFlow backup completed: ${BACKUP_DATE} (${TOTAL_SIZE})\"}" \
        &> /dev/null || true
fi

exit 0
