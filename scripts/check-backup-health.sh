#!/bin/bash

# ============================================
# OptiFlow AI - Backup Health Check
# ============================================
# Verifies that backups are running successfully
# Sends alerts if issues detected
# ============================================

set -e

# Configuration
BACKUP_ROOT="/backups"
LOG_FILE="${BACKUP_ROOT}/backup.log"
MAX_BACKUP_AGE_HOURS=26  # Alert if no backup in 26 hours (daily + buffer)
MIN_BACKUP_SIZE_MB=10     # Alert if backup is suspiciously small

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Health status
HEALTH_OK=true
HEALTH_MESSAGES=()

echo "============================================"
echo "OptiFlow Backup Health Check"
echo "============================================"
echo ""

# ============================================
# 1. Check Last Backup Time
# ============================================
echo "Checking last backup time..."

LATEST_BACKUP=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | sort -r | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    HEALTH_OK=false
    HEALTH_MESSAGES+=("❌ No backups found")
else
    BACKUP_NAME=$(basename "$LATEST_BACKUP")
    BACKUP_AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
    
    if [ $BACKUP_AGE_HOURS -gt $MAX_BACKUP_AGE_HOURS ]; then
        HEALTH_OK=false
        HEALTH_MESSAGES+=("❌ Last backup is ${BACKUP_AGE_HOURS}h old (expected <${MAX_BACKUP_AGE_HOURS}h)")
    else
        echo "✅ Last backup: ${BACKUP_NAME} (${BACKUP_AGE_HOURS}h ago)"
    fi
fi

# ============================================
# 2. Check Backup Size
# ============================================
echo "Checking backup size..."

if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_SIZE_MB=$(du -sm "$LATEST_BACKUP" | cut -f1)
    
    if [ $BACKUP_SIZE_MB -lt $MIN_BACKUP_SIZE_MB ]; then
        HEALTH_OK=false
        HEALTH_MESSAGES+=("❌ Backup is only ${BACKUP_SIZE_MB}MB (expected >${MIN_BACKUP_SIZE_MB}MB)")
    else
        echo "✅ Backup size: ${BACKUP_SIZE_MB}MB"
    fi
fi

# ============================================
# 3. Check Required Files
# ============================================
echo "Checking backup contents..."

if [ -n "$LATEST_BACKUP" ]; then
    REQUIRED_FILES=(
        "postgresql_*.sql.gz.gpg"
        "influxdb_*.tar.gz.gpg"
    )
    
    for pattern in "${REQUIRED_FILES[@]}"; do
        if ! ls ${LATEST_BACKUP}/${pattern} 1> /dev/null 2>&1; then
            HEALTH_OK=false
            HEALTH_MESSAGES+=("❌ Missing: ${pattern}")
        else
            echo "✅ Found: ${pattern}"
        fi
    done
fi

# ============================================
# 4. Check Backup Log for Errors
# ============================================
echo "Checking backup logs..."

if [ -f "$LOG_FILE" ]; then
    # Check last 100 lines for errors
    ERROR_COUNT=$(tail -100 "$LOG_FILE" | grep -ci "error" || true)
    
    if [ $ERROR_COUNT -gt 0 ]; then
        HEALTH_OK=false
        HEALTH_MESSAGES+=("⚠️  ${ERROR_COUNT} errors found in recent logs")
    else
        echo "✅ No errors in recent logs"
    fi
else
    HEALTH_MESSAGES+=("⚠️  Backup log not found")
fi

# ============================================
# 5. Check Disk Space
# ============================================
echo "Checking disk space..."

DISK_USAGE=$(df -h "${BACKUP_ROOT}" | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $DISK_USAGE -gt 90 ]; then
    HEALTH_OK=false
    HEALTH_MESSAGES+=("❌ Disk usage at ${DISK_USAGE}% (critical)")
elif [ $DISK_USAGE -gt 80 ]; then
    HEALTH_MESSAGES+=("⚠️  Disk usage at ${DISK_USAGE}% (warning)")
else
    echo "✅ Disk usage: ${DISK_USAGE}%"
fi

# ============================================
# 6. Check Backup Count (Retention)
# ============================================
echo "Checking backup retention..."

BACKUP_COUNT=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | wc -l)
EXPECTED_COUNT=${BACKUP_KEEP_DAYS:-7}

if [ $BACKUP_COUNT -lt $((EXPECTED_COUNT - 1)) ]; then
    HEALTH_MESSAGES+=("⚠️  Only ${BACKUP_COUNT} backups (expected ~${EXPECTED_COUNT})")
else
    echo "✅ Backup count: ${BACKUP_COUNT}"
fi

# ============================================
# 7. Send Alert if Unhealthy
# ============================================
echo ""
echo "============================================"

if [ "$HEALTH_OK" = true ] && [ ${#HEALTH_MESSAGES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ BACKUP HEALTH: OK${NC}"
    echo "All backup checks passed"
    exit 0
else
    echo -e "${RED}❌ BACKUP HEALTH: ISSUES DETECTED${NC}"
    echo ""
    
    for msg in "${HEALTH_MESSAGES[@]}"; do
        echo "  $msg"
    done
    
    echo ""
    echo "Please investigate backup system immediately!"
    
    # Send alert via webhook (Slack, PagerDuty, etc)
    if [ -n "${BACKUP_ALERT_WEBHOOK}" ]; then
        ALERT_TEXT="🚨 OptiFlow Backup Health Check FAILED:\n$(printf '%s\n' "${HEALTH_MESSAGES[@]}")"
        
        curl -X POST "${BACKUP_ALERT_WEBHOOK}" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"${ALERT_TEXT}\"}" \
            &> /dev/null || true
    fi
    
    # Send email alert (if configured)
    if [ -n "${ALERT_EMAIL}" ]; then
        echo "Subject: [CRITICAL] OptiFlow Backup Health Check Failed" > /tmp/backup_alert.txt
        echo "" >> /tmp/backup_alert.txt
        echo "Backup health check detected the following issues:" >> /tmp/backup_alert.txt
        echo "" >> /tmp/backup_alert.txt
        printf '%s\n' "${HEALTH_MESSAGES[@]}" >> /tmp/backup_alert.txt
        echo "" >> /tmp/backup_alert.txt
        echo "Server: $(hostname)" >> /tmp/backup_alert.txt
        echo "Time: $(date)" >> /tmp/backup_alert.txt
        
        cat /tmp/backup_alert.txt | mail -s "[CRITICAL] OptiFlow Backup Health Check Failed" "${ALERT_EMAIL}" || true
        rm /tmp/backup_alert.txt
    fi
    
    exit 1
fi
