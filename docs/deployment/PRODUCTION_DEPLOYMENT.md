# Production Deployment Guide - OptiFlow AI Platform

Complete guide for deploying OptiFlow AI Platform to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Security Checklist](#security-checklist)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04 LTS or later (recommended)
- **CPU**: 8+ cores
- **RAM**: 16GB+ (32GB recommended for production)
- **Storage**: 500GB+ SSD
- **Network**: Static IP address, Domain name configured

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git
- SSL Certificate (Let's Encrypt or commercial)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd optiflow-platform
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with production values
nano .env
```

**Important variables to configure:**

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 32)
RABBITMQ_PASSWORD=$(openssl rand -hex 32)
INFLUXDB_TOKEN=$(openssl rand -hex 32)

# Set CORS origins to your domain
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# Set frontend URLs
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

### 3. SSL/TLS Configuration

```bash
# Install Certbot for Let's Encrypt
sudo apt-get update
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
```

---

## Docker Deployment

### 1. Build Images

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build
```

### 2. Initialize Databases

```bash
# Start database services
docker-compose -f docker-compose.prod.yml up -d postgres influxdb redis rabbitmq

# Wait for services to be healthy
sleep 30

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### 3. Start All Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Create Initial Admin User

```bash
# Access backend container
docker exec -it optiflow-backend-prod python

# In Python shell:
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

admin_user = User(
    email="admin@yourdomain.com",
    username="admin",
    hashed_password=get_password_hash("your-secure-password"),
    full_name="System Administrator",
    is_superuser=True,
    is_active=True
)

db.add(admin_user)
db.commit()
db.close()
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets generated using cryptographically secure random values
- [ ] Default passwords changed
- [ ] `.env` file permissions set to 600
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured (only necessary ports open)
- [ ] Database backups scheduled
- [ ] Monitoring and alerting configured

### Network Security

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Application Security

```bash
# Restrict file permissions
chmod 600 .env
chmod -R 755 backend/app
chmod -R 755 frontend/src

# Ensure non-root user in containers
# Already configured in Dockerfile.prod
```

---

## Monitoring & Logging

### Access Monitoring Dashboards

- **Grafana**: http://your-domain:3000
  - Default credentials: admin / (set in .env)
  - Import dashboards from `monitoring/grafana/dashboards/`

- **Prometheus**: http://your-domain:9090
  - Metrics scraping configured
  - Alert rules in `monitoring/prometheus/alerts/`

- **MLflow**: http://your-domain:5000
  - Model tracking and registry

### Log Management

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Export logs for analysis
docker-compose -f docker-compose.prod.yml logs backend > backend.log
```

### Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/optiflow

# Add configuration:
/opt/optiflow/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    sharedscripts
    postrotate
        docker-compose -f /opt/optiflow/docker-compose.prod.yml restart backend
    endscript
}
```

---

## Backup & Recovery

### Automated Backups

```bash
# Create backup script
nano /opt/optiflow/scripts/backup.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/optiflow/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec optiflow-postgres-prod pg_dump -U optiflow optiflow | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup InfluxDB
docker exec optiflow-influxdb-prod influx backup /tmp/backup
docker cp optiflow-influxdb-prod:/tmp/backup "$BACKUP_DIR/influxdb_$DATE"

# Backup application data
tar -czf "$BACKUP_DIR/mlflow_$DATE.tar.gz" -C /var/lib/docker/volumes optiflow_backend_mlflow

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /opt/optiflow/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/optiflow/scripts/backup.sh >> /var/log/optiflow-backup.log 2>&1
```

### Recovery

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore PostgreSQL
gunzip < postgres_backup.sql.gz | docker exec -i optiflow-postgres-prod psql -U optiflow optiflow

# Restore InfluxDB
docker cp influxdb_backup optiflow-influxdb-prod:/tmp/backup
docker exec optiflow-influxdb-prod influx restore /tmp/backup

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Scaling

### Horizontal Scaling

#### Scale Celery Workers

```bash
# Scale to 8 workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=8
```

#### Load Balancer (Nginx)

```nginx
# /etc/nginx/conf.d/optiflow.conf

upstream backend_servers {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Database Scaling

#### PostgreSQL Replication

```yaml
# docker-compose.prod.yml - add read replica
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: optiflow
    POSTGRES_USER: optiflow
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    PGDATA: /var/lib/postgresql/data/pgdata
  command: |
    postgres
    -c wal_level=replica
    -c max_wal_senders=3
    -c max_replication_slots=3
```

#### InfluxDB Clustering

For high availability, consider InfluxDB Enterprise or InfluxDB Cloud.

---

## Troubleshooting

### Common Issues

#### 1. Backend Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Database not ready: Wait for DB health check
# - Migration issues: Run migrations manually
# - Port conflict: Check if port 8000 is in use
```

#### 2. Database Connection Errors

```bash
# Test PostgreSQL connection
docker exec -it optiflow-postgres-prod psql -U optiflow -d optiflow

# Test InfluxDB connection
docker exec -it optiflow-influxdb-prod influx ping

# Verify connection strings in .env
```

#### 3. WebSocket Connection Failures

```bash
# Check Redis (required for WebSocket)
docker exec -it optiflow-redis-prod redis-cli ping

# Check CORS settings in .env
# Ensure WebSocket URL uses wss:// for HTTPS
```

#### 4. High Memory Usage

```bash
# Check container resource usage
docker stats

# Limit container resources
docker-compose -f docker-compose.prod.yml config

# Add to service definition:
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Database health
docker-compose -f docker-compose.prod.yml ps
```

---

## Performance Optimization

### 1. Enable Caching

Redis is already configured. Ensure cache keys are properly set in application.

### 2. Database Indexing

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_timeseries_tag_timestamp ON timeseries(tag_id, timestamp);
CREATE INDEX idx_annotations_device ON annotations(device_id);
```

### 3. Enable Compression

Already enabled via GZip middleware in FastAPI.

### 4. CDN for Static Assets

Use CloudFlare or AWS CloudFront for frontend static files.

---

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Review monitoring dashboards
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Review and optimize database

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Apply database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Restart services with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
```

---

## Support

For issues or questions:
- Documentation: `/docs`
- API Docs: `https://api.yourdomain.com/docs`
- Email: support@optiflow.ai
- GitHub Issues: https://github.com/your-org/optiflow-platform/issues

---

**Production deployment completed! Monitor your system and adjust resources as needed.**
