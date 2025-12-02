#!/bin/bash
# ===========================================
# OptiFlow AI Platform - Cron Backup Setup
# ===========================================
#
# Sets up automated backup schedules
#
# Usage:
#   ./setup-cron-backup.sh
#
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "================================================"
echo "  OptiFlow AI Platform - Backup Scheduler"
echo "================================================"
echo -e "${NC}"

# Create backups directory
mkdir -p "$PROJECT_ROOT/backups"/{postgres,influxdb,redis,config,logs}
chmod -R 755 "$PROJECT_ROOT/backups"

# Create the crontab entries
CRON_FILE="/tmp/optiflow_cron"

cat > "$CRON_FILE" << EOF
# ===========================================
# OptiFlow AI Platform - Automated Backups
# ===========================================
#
# Run full backup every day at 2 AM
0 2 * * * cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh >> $PROJECT_ROOT/backups/logs/backup_\$(date +\%Y\%m\%d).log 2>&1

# Run PostgreSQL backup every 6 hours
0 */6 * * * cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh postgres >> $PROJECT_ROOT/backups/logs/postgres_\$(date +\%Y\%m\%d).log 2>&1

# Verify backups weekly (Sunday at 3 AM)
0 3 * * 0 cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh verify >> $PROJECT_ROOT/backups/logs/verify_\$(date +\%Y\%m\%d).log 2>&1

# Generate weekly report (Sunday at 4 AM)
0 4 * * 0 cd $PROJECT_ROOT && docker compose exec -T backup /backup.sh report >> $PROJECT_ROOT/backups/logs/report_\$(date +\%Y\%m\%d).log 2>&1

# Cleanup old backup logs monthly
0 5 1 * * find $PROJECT_ROOT/backups/logs -name "*.log" -mtime +30 -delete
EOF

echo "Backup schedule configuration:"
echo ""
cat "$CRON_FILE"
echo ""

echo -e "${YELLOW}To install the cron jobs, run:${NC}"
echo "  crontab $CRON_FILE"
echo ""
echo -e "${YELLOW}Or to merge with existing crontab:${NC}"
echo "  (crontab -l 2>/dev/null; cat $CRON_FILE) | crontab -"
echo ""

# Alternative: systemd timer (for systems without cron)
echo -e "${GREEN}Creating systemd timer alternative...${NC}"

mkdir -p "$PROJECT_ROOT/systemd"

# Service file
cat > "$PROJECT_ROOT/systemd/optiflow-backup.service" << EOF
[Unit]
Description=OptiFlow AI Platform Backup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker compose exec -T backup /backup.sh
StandardOutput=journal
StandardError=journal
User=root
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# Timer file
cat > "$PROJECT_ROOT/systemd/optiflow-backup.timer" << EOF
[Unit]
Description=OptiFlow AI Platform Daily Backup Timer

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

echo ""
echo -e "${GREEN}Systemd timer files created in $PROJECT_ROOT/systemd/${NC}"
echo ""
echo "To install systemd timers (as root):"
echo "  cp $PROJECT_ROOT/systemd/optiflow-backup.* /etc/systemd/system/"
echo "  systemctl daemon-reload"
echo "  systemctl enable optiflow-backup.timer"
echo "  systemctl start optiflow-backup.timer"
echo ""

# Manual backup instructions
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Manual Backup Commands:${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Full backup:"
echo "  docker compose exec backup /backup.sh"
echo ""
echo "PostgreSQL only:"
echo "  docker compose exec backup /backup.sh postgres"
echo ""
echo "InfluxDB only:"
echo "  docker compose exec backup /backup.sh influxdb"
echo ""
echo "Verify backups:"
echo "  docker compose exec backup /backup.sh verify"
echo ""
echo "Restore from backup (CAUTION!):"
echo "  docker compose exec backup /backup.sh --restore 20241201"
echo ""

echo -e "${GREEN}Setup complete!${NC}"
