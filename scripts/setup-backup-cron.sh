#!/bin/bash
# ============================================
# OptiFlow AI - Backup Cron Setup
# ============================================
#
# Configures automated backup schedules:
# - Daily backup at 2:00 AM
# - Weekly full backup on Sunday at 3:00 AM
# - Monthly retention cleanup
#
# Usage:
#   ./setup-backup-cron.sh install    # Install cron jobs
#   ./setup-backup-cron.sh remove     # Remove cron jobs
#   ./setup-backup-cron.sh status     # Check cron status
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CRON_TAG="# OptiFlow-Backup"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

install_cron() {
    echo -e "${GREEN}Installing OptiFlow backup cron jobs...${NC}"

    # Remove existing OptiFlow cron jobs
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab - 2>/dev/null || true

    # Create new cron entries
    (crontab -l 2>/dev/null || true; cat <<EOF
# Daily backup at 2:00 AM (PostgreSQL + InfluxDB) $CRON_TAG
0 2 * * * cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh >> $PROJECT_ROOT/backups/logs/daily_backup.log 2>&1 $CRON_TAG

# Weekly full backup on Sunday at 3:00 AM $CRON_TAG
0 3 * * 0 cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh >> $PROJECT_ROOT/backups/logs/weekly_backup.log 2>&1 $CRON_TAG

# Monthly backup verification $CRON_TAG
0 4 1 * * cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh verify >> $PROJECT_ROOT/backups/logs/verify.log 2>&1 $CRON_TAG

# SSL certificate renewal check (for Let's Encrypt) $CRON_TAG
0 0 1 * * certbot renew --quiet && docker compose -f $PROJECT_ROOT/docker-compose.prod.yml restart nginx 2>&1 | tee -a $PROJECT_ROOT/backups/logs/ssl_renewal.log $CRON_TAG
EOF
) | crontab -

    echo -e "${GREEN}Cron jobs installed successfully!${NC}"
    echo ""
    echo "Installed schedules:"
    echo "  - Daily backup: 2:00 AM"
    echo "  - Weekly full backup: Sunday 3:00 AM"
    echo "  - Monthly verification: 1st of month, 4:00 AM"
    echo "  - SSL renewal: 1st of month, midnight"
    echo ""
    echo "Logs location: $PROJECT_ROOT/backups/logs/"
}

remove_cron() {
    echo -e "${YELLOW}Removing OptiFlow backup cron jobs...${NC}"
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab - 2>/dev/null || true
    echo -e "${GREEN}Cron jobs removed.${NC}"
}

show_status() {
    echo "Current OptiFlow cron jobs:"
    echo "=============================="
    crontab -l 2>/dev/null | grep "$CRON_TAG" || echo "No OptiFlow cron jobs found."
    echo ""
    echo "Recent backup logs:"
    echo "=============================="
    if [ -f "$PROJECT_ROOT/backups/logs/daily_backup.log" ]; then
        tail -20 "$PROJECT_ROOT/backups/logs/daily_backup.log"
    else
        echo "No backup logs found yet."
    fi
}

# Main
case "${1:-status}" in
    install)
        install_cron
        ;;
    remove)
        remove_cron
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {install|remove|status}"
        exit 1
        ;;
esac
