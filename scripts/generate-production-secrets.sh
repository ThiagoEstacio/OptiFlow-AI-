#!/bin/bash

# ============================================
# OptiFlow AI - Production Secrets Generator
# ============================================
# Generates cryptographically secure passwords
# and creates production environment file
# ============================================

set -e

echo "============================================"
echo "OptiFlow AI - Production Secrets Generator"
echo "============================================"
echo ""

# Check if .env.production already exists
if [ -f ".env.production" ]; then
    echo "⚠️  WARNING: .env.production already exists!"
    echo "Backing up to .env.production.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env.production ".env.production.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Generate secure passwords
echo "🔐 Generating cryptographically secure credentials..."
echo ""

POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
INFLUX_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
INFLUX_TOKEN=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
KAFKA_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
GATEWAY_API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
GRAFANA_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

# Create .env.production file
cat > .env.production << EOF
# OptiFlow AI - Production Environment Variables
# ================================================
# AUTO-GENERATED ON: $(date)
# SECURITY: This file contains sensitive credentials
# DO NOT COMMIT TO GIT! Add to .gitignore
# ================================================

# ============================================
# Database - PostgreSQL
# ============================================
POSTGRES_DB=optiflow
POSTGRES_USER=optiflow_prod
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# ============================================
# Time Series Database - InfluxDB
# ============================================
INFLUX_USER=admin
INFLUX_PASSWORD=${INFLUX_PASSWORD}
INFLUX_TOKEN=${INFLUX_TOKEN}
INFLUX_ORG=optiflow
INFLUX_BUCKET=smartport

# ============================================
# Cache - Redis
# ============================================
REDIS_PASSWORD=${REDIS_PASSWORD}

# ============================================
# Message Queue - Kafka
# ============================================
KAFKA_SASL_PASSWORD=${KAFKA_PASSWORD}

# ============================================
# Backend API - Security
# ============================================
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gateway API Key
GATEWAY_API_KEY=${GATEWAY_API_KEY}

# Admin user (first time setup)
ADMIN_EMAIL=admin@optiflow.local
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# ============================================
# Monitoring - Grafana
# ============================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

# ============================================
# Alerting
# ============================================
ALERTMANAGER_SMTP_FROM=alerts@optiflow.com
ALERTMANAGER_SMTP_TO=team@optiflow.com
ALERTMANAGER_SMTP_HOST=smtp.gmail.com
ALERTMANAGER_SMTP_PORT=587
ALERTMANAGER_SMTP_USER=alerts@optiflow.com
ALERTMANAGER_SMTP_PASSWORD=CHANGE_ME_APP_SPECIFIC_PASSWORD

# PagerDuty (optional)
PAGERDUTY_SERVICE_KEY=CHANGE_ME_IF_USING_PAGERDUTY

# Slack (optional)
SLACK_WEBHOOK_URL=CHANGE_ME_IF_USING_SLACK

# ============================================
# External Services
# ============================================
# S3 for backups (optional)
AWS_ACCESS_KEY_ID=CHANGE_ME_IF_USING_S3
AWS_SECRET_ACCESS_KEY=CHANGE_ME_IF_USING_S3
AWS_REGION=us-east-1
S3_BACKUP_BUCKET=optiflow-backups

# ============================================
# Application Configuration
# ============================================
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# CORS (comma-separated origins)
CORS_ORIGINS=https://app.optiflow.com,https://optiflow.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Frontend API URL
VITE_API_URL=https://api.optiflow.com

# Backup Configuration
BACKUP_KEEP_DAYS=7
BACKUP_ENABLED=true

# ============================================
# SSL/TLS Certificates
# ============================================
SSL_CERT_PATH=/etc/ssl/certs/optiflow.crt
SSL_KEY_PATH=/etc/ssl/private/optiflow.key
EOF

# Set secure file permissions
chmod 600 .env.production

echo "✅ Production environment file created: .env.production"
echo ""
echo "============================================"
echo "🔑 GENERATED CREDENTIALS (ONLY TIME SHOWN)"
echo "============================================"
echo ""
echo "PostgreSQL:"
echo "  User: optiflow_prod"
echo "  Password: ${POSTGRES_PASSWORD}"
echo ""
echo "InfluxDB:"
echo "  User: admin"
echo "  Password: ${INFLUX_PASSWORD}"
echo "  Token: ${INFLUX_TOKEN}"
echo ""
echo "Redis:"
echo "  Password: ${REDIS_PASSWORD}"
echo ""
echo "Kafka:"
echo "  Password: ${KAFKA_PASSWORD}"
echo ""
echo "Backend:"
echo "  Secret Key: ${SECRET_KEY}"
echo "  JWT Secret: ${JWT_SECRET}"
echo "  Gateway API Key: ${GATEWAY_API_KEY}"
echo ""
echo "Admin User:"
echo "  Email: admin@optiflow.local"
echo "  Password: ${ADMIN_PASSWORD}"
echo ""
echo "Grafana:"
echo "  User: admin"
echo "  Password: ${GRAFANA_PASSWORD}"
echo ""
echo "============================================"
echo "⚠️  SECURITY REMINDERS"
echo "============================================"
echo "1. These credentials will NOT be shown again"
echo "2. Store them securely in a password manager"
echo "3. NEVER commit .env.production to git"
echo "4. File permissions set to 600 (owner read/write only)"
echo "5. Rotate credentials every 90 days"
echo ""

# Create encrypted backup
echo "🔒 Creating encrypted backup..."
if command -v gpg &> /dev/null; then
    cat .env.production | gpg --symmetric --cipher-algo AES256 -o ".env.production.$(date +%Y%m%d_%H%M%S).gpg"
    echo "✅ Encrypted backup created (requires passphrase to decrypt)"
else
    echo "⚠️  GPG not installed. Skipping encrypted backup."
    echo "   Install with: apt-get install gnupg (Debian/Ubuntu)"
fi

echo ""
echo "============================================"
echo "📋 NEXT STEPS"
echo "============================================"
echo "1. Update SMTP credentials in .env.production"
echo "2. Update CORS_ORIGINS and VITE_API_URL for your domain"
echo "3. Configure SSL certificates"
echo "4. Test with: docker-compose -f docker-compose.prod.yml config"
echo "5. Deploy with: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "✅ Done!"
