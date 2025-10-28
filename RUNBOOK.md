# SmartPort Operational Runbook

**Version**: 1.0
**Last Updated**: 2025-10-28
**Maintainer**: SmartPort DevOps Team

## Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Health Checks](#health-checks)
4. [Common Issues & Solutions](#common-issues--solutions)
5. [Incident Response](#incident-response)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Backup & Recovery](#backup--recovery)
8. [Scaling Procedures](#scaling-procedures)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [Contact Information](#contact-information)

---

## System Overview

### Architecture Components

| Component | Purpose | Port | Health Check |
|-----------|---------|------|--------------|
| Backend API | FastAPI application | 8000 | `http://localhost:8000/health` |
| PostgreSQL | Relational database | 5432 | `docker-compose ps postgres` |
| InfluxDB | Time series database | 8086 | `http://localhost:8086/health` |
| Redis | Cache & pub/sub | 6379 | `redis-cli ping` |
| Gateway | Industrial protocol handler | 8081 | Check logs |
| Nginx | Reverse proxy | 80, 443 | `curl http://localhost` |
| Prometheus | Metrics collection | 9090 | `http://localhost:9090/-/healthy` |
| Grafana | Monitoring dashboards | 3001 | `http://localhost:3001/api/health` |

### Critical Dependencies

- **Backend** requires: PostgreSQL, InfluxDB, Redis
- **Gateway** requires: Backend API
- **Frontend** requires: Backend API, Nginx

---

## Daily Operations

### Morning Checklist (5 minutes)

```bash
# 1. Check all services are running
docker-compose -f docker-compose.prod.yml ps

# 2. Run smoke test
./scripts/smoke-test.sh

# 3. Check disk space
df -h

# 4. Check recent errors in logs
docker-compose -f docker-compose.prod.yml logs --tail=100 --since=24h | grep -i error

# 5. Verify backups completed
ls -lth /var/backups/smartport/ | head -n 5
```

### Evening Checklist (3 minutes)

```bash
# 1. Review Grafana dashboards for anomalies
# Open: http://your-domain:3001/d/smartport-overview

# 2. Check Prometheus alerts
# Open: http://your-domain:9090/alerts

# 3. Verify backup completed today
ls -l /var/backups/smartport/*$(date +%Y-%m-%d)*

# 4. Check system resource usage
docker stats --no-stream
```

---

## Health Checks

### Quick Health Check (30 seconds)

```bash
#!/bin/bash
# Save as: quick-health-check.sh

echo "=== SmartPort Quick Health Check ==="
echo ""

# API Health
echo -n "API: "
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# Database
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U smartport > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# InfluxDB
echo -n "InfluxDB: "
if curl -f -s http://localhost:8086/health > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

echo ""
echo "Check complete at $(date)"
```

### Detailed Health Check (2 minutes)

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check resource usage
docker stats --no-stream

# Check database connections
docker-compose exec postgres psql -U smartport -c "SELECT count(*) FROM pg_stat_activity;"

# Check InfluxDB buckets
docker-compose exec influxdb influx bucket list

# Check Redis memory
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

---

## Common Issues & Solutions

### Issue 1: API Not Responding

**Symptoms**:
- Health check returns 502/504
- Frontend shows "Connection refused"
- `curl http://localhost:8000/health` fails

**Diagnosis**:
```bash
# Check if backend container is running
docker-compose ps backend

# Check backend logs
docker-compose logs backend --tail=50

# Check if database is accessible
docker-compose exec backend ping -c 3 postgres
```

**Solution**:
```bash
# Restart backend
docker-compose restart backend

# Wait 30 seconds
sleep 30

# Verify health
curl http://localhost:8000/health
```

**If still not working**:
```bash
# Check database migrations
docker-compose exec backend alembic current

# Restart all dependent services
docker-compose restart postgres redis influxdb backend
```

---

### Issue 2: High CPU Usage

**Symptoms**:
- CPU usage > 80% for extended period
- Slow API responses
- Prometheus alert: `HighCPUUsage`

**Diagnosis**:
```bash
# Check which container is consuming CPU
docker stats --no-stream

# Check backend workers
docker-compose exec backend ps aux

# Check active database queries
docker-compose exec postgres psql -U smartport -c "SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle';"
```

**Solution**:
```bash
# Option 1: Scale backend horizontally (if using swarm/k8s)
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# Option 2: Identify and kill slow queries
docker-compose exec postgres psql -U smartport -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';"

# Option 3: Restart services (last resort)
docker-compose restart backend
```

---

### Issue 3: Database Connection Pool Exhausted

**Symptoms**:
- Error: "QueuePool limit exceeded"
- API returns 500 errors
- Backend logs show "TimeoutError: QueuePool limit"

**Diagnosis**:
```bash
# Check active connections
docker-compose exec postgres psql -U smartport -c "SELECT count(*) FROM pg_stat_activity WHERE state != 'idle';"

# Check max connections
docker-compose exec postgres psql -U smartport -c "SHOW max_connections;"

# Check connection pool config
grep "POOL_SIZE" .env.prod
```

**Solution**:
```bash
# Option 1: Increase pool size (edit .env.prod)
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Restart backend
docker-compose restart backend

# Option 2: Kill idle connections
docker-compose exec postgres psql -U smartport -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '1 hour';"
```

---

### Issue 4: Disk Space Full

**Symptoms**:
- Cannot write to database
- Logs show "No space left on device"
- Prometheus alert: `HighDiskUsage`

**Diagnosis**:
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Check largest directories
du -sh /* | sort -h | tail -10
```

**Solution**:
```bash
# Clean Docker images/containers
docker system prune -a --volumes -f

# Clean old logs
find /var/log -name "*.log" -mtime +30 -delete

# Clean old backups (keep last 7 days)
find /var/backups/smartport -name "*.gz" -mtime +7 -delete

# Rotate logs
docker-compose logs --no-log-prefix > /dev/null
```

---

### Issue 5: Gateway Not Collecting Data

**Symptoms**:
- No data in InfluxDB
- Devices show as "disconnected"
- Gateway logs show connection errors

**Diagnosis**:
```bash
# Check gateway logs
docker-compose logs gateway --tail=100

# Check if devices are reachable
docker-compose exec gateway ping -c 3 <device-ip>

# Check InfluxDB for recent data
docker-compose exec influxdb influx query 'from(bucket:"smartport") |> range(start:-1h) |> limit(n:10)'
```

**Solution**:
```bash
# Restart gateway
docker-compose restart gateway

# Check device configuration
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/devices/

# If device is unreachable, check network
docker-compose exec gateway traceroute <device-ip>
```

---

### Issue 6: InfluxDB Memory Issues

**Symptoms**:
- InfluxDB container restarts frequently
- OOMKilled in docker logs
- Slow query performance

**Diagnosis**:
```bash
# Check memory usage
docker stats influxdb --no-stream

# Check bucket cardinality
docker-compose exec influxdb influx query 'import "influxdata/influxdb/schema" schema.measurements(bucket:"smartport")'
```

**Solution**:
```bash
# Increase InfluxDB memory limit (docker-compose.prod.yml)
mem_limit: 4g

# Delete old data
docker-compose exec influxdb influx delete --bucket smartport --start 2024-01-01T00:00:00Z --stop 2024-06-01T00:00:00Z

# Restart InfluxDB
docker-compose restart influxdb
```

---

## Incident Response

### Severity Levels

| Level | Response Time | Description |
|-------|--------------|-------------|
| **P0 - Critical** | 15 minutes | Complete system outage |
| **P1 - High** | 1 hour | Major feature unavailable |
| **P2 - Medium** | 4 hours | Minor feature degraded |
| **P3 - Low** | 24 hours | Cosmetic issue |

### Incident Response Process

#### Step 1: Acknowledge (2 minutes)

```bash
# 1. Acknowledge alert in Prometheus/Grafana
# 2. Post in incident channel (Slack/Teams):
#    "🚨 INCIDENT: [Brief description]
#     Status: Investigating
#     Owner: [Your name]
#     Started: [Time]"

# 3. Start incident log
echo "$(date) - Incident started - [description]" >> /var/log/smartport/incidents.log
```

#### Step 2: Diagnose (5-10 minutes)

```bash
# Check all services
docker-compose ps

# Check recent logs for errors
docker-compose logs --tail=200 --since=15m | grep -i error

# Check system resources
docker stats --no-stream

# Check database health
docker-compose exec postgres pg_isready

# Run quick health check
./scripts/smoke-test.sh
```

#### Step 3: Communicate (During incident)

```
Update incident channel every 15 minutes:
"⏱️ UPDATE: [What you found]
 Status: [Investigating/Fixing/Testing/Resolved]
 ETA: [Estimated resolution time]
 Next update: [Time]"
```

#### Step 4: Mitigate (Variable)

```bash
# For API issues - restart backend
docker-compose restart backend

# For database issues - restart postgres
docker-compose restart postgres

# For complete outage - full restart
docker-compose restart

# For data corruption - restore from backup
./scripts/restore.sh
```

#### Step 5: Verify (5 minutes)

```bash
# Run full smoke test
./scripts/smoke-test.sh

# Check all services healthy
docker-compose ps

# Verify user can login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=testuser&password=testpass123"

# Check monitoring dashboards
# Open Grafana and verify metrics
```

#### Step 6: Document (10 minutes)

```bash
# Update incident log
cat >> /var/log/smartport/incidents.log <<EOF
$(date) - RESOLVED
Root cause: [Cause]
Solution: [What was done]
Prevention: [How to prevent]
Duration: [Total time]
EOF

# Post resolution
"✅ RESOLVED: [Description]
 Root cause: [Cause]
 Solution: [Action taken]
 Duration: [Total downtime]
 Follow-up: [Ticket number]"
```

---

## Maintenance Procedures

### Scheduled Maintenance Window

**Recommended**: Sunday 2:00 AM - 4:00 AM (low traffic period)

```bash
# 1. Notify users 48 hours in advance
# 2. Create maintenance banner on frontend
# 3. Execute maintenance during window
# 4. Verify everything works
# 5. Remove maintenance banner
```

### Rolling Restart (Zero Downtime)

```bash
# For backend (with multiple instances)
for i in {1..4}; do
    docker-compose restart backend_$i
    sleep 30
    ./scripts/smoke-test.sh
done
```

### Database Maintenance

```bash
# Vacuum and analyze (weekly - Sunday 3:00 AM)
docker-compose exec postgres psql -U smartport -d smartport -c "VACUUM ANALYZE;"

# Reindex (monthly - First Sunday 3:00 AM)
docker-compose exec postgres psql -U smartport -d smartport -c "REINDEX DATABASE smartport;"

# Update statistics
docker-compose exec postgres psql -U smartport -d smartport -c "ANALYZE;"
```

### Log Rotation

```bash
# Rotate Docker logs (daily via cron)
0 2 * * * /usr/sbin/logrotate /etc/logrotate.d/docker-compose

# Manual rotation if needed
docker-compose logs --no-log-prefix > /dev/null
```

---

## Backup & Recovery

### Automated Daily Backup

**Schedule**: Daily at 2:00 AM (configured in crontab)

```bash
# Backup script runs automatically
0 2 * * * /opt/smartport/scripts/backup.sh

# Verify backup completed
ls -lh /var/backups/smartport/*$(date +%Y-%m-%d)*
```

### Manual Backup (Before Maintenance)

```bash
# Full backup
./scripts/backup.sh

# Backup specific database only
docker-compose exec postgres pg_dump -U smartport smartport | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Recovery Procedures

#### Full System Recovery

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
./scripts/restore.sh

# 3. Follow prompts to select backup
# 4. Wait for restoration to complete

# 5. Start services
docker-compose up -d

# 6. Verify health
./scripts/smoke-test.sh
```

#### Point-in-Time Recovery (PostgreSQL)

```bash
# 1. Stop backend
docker-compose stop backend

# 2. Restore to specific timestamp
./scripts/restore.sh --timestamp "2025-10-27 14:30:00"

# 3. Start backend
docker-compose start backend

# 4. Verify data
docker-compose exec postgres psql -U smartport -c "SELECT * FROM alembic_version;"
```

---

## Scaling Procedures

### Horizontal Scaling (Backend)

```bash
# Increase backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# Verify all instances are healthy
docker-compose ps backend

# Update load balancer (if using external LB)
# Update nginx upstream configuration
```

### Vertical Scaling (Resources)

```yaml
# Edit docker-compose.prod.yml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

### Database Scaling

```bash
# Increase PostgreSQL shared_buffers
# Edit postgresql.conf
shared_buffers = 2GB
effective_cache_size = 6GB

# Restart PostgreSQL
docker-compose restart postgres
```

---

## Monitoring & Alerts

### Critical Alerts (Immediate Action Required)

| Alert | Threshold | Action |
|-------|-----------|--------|
| SystemDown | 0 successful probes | See [Incident Response](#incident-response) |
| HighCPUUsage | CPU > 80% for 5min | See [Issue 2](#issue-2-high-cpu-usage) |
| HighMemoryUsage | Memory > 85% for 5min | Restart services or scale up |
| HighDiskUsage | Disk > 90% | See [Issue 4](#issue-4-disk-space-full) |
| DatabaseDown | Database unreachable | Restart postgres, check logs |

### Warning Alerts (Action Within 1 Hour)

| Alert | Threshold | Action |
|-------|-----------|--------|
| HighResponseTime | P95 > 1s for 10min | Check slow queries, consider scaling |
| HighErrorRate | Errors > 5% for 5min | Check backend logs, investigate errors |
| BackupFailed | Backup not completed in 24h | Run manual backup, check disk space |

### Key Metrics to Monitor

```bash
# API Response Time (should be < 500ms P95)
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Error Rate (should be < 1%)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Database Connections (should be < 80% of max)
pg_stat_database_numbackends / pg_settings_max_connections * 100

# Disk Usage (should be < 80%)
(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100
```

---

## Contact Information

### Escalation Path

| Level | Contact | Response Time |
|-------|---------|---------------|
| **L1 - Operations** | ops@smartport.com | 15 minutes |
| **L2 - Engineering** | dev@smartport.com | 1 hour |
| **L3 - Architect** | architect@smartport.com | 4 hours |
| **Emergency** | +1-555-0100 (24/7 hotline) | Immediate |

### Team Contacts

- **Operations Lead**: ops-lead@smartport.com
- **Database Admin**: dba@smartport.com
- **Security Team**: security@smartport.com
- **DevOps**: devops@smartport.com

### External Vendors

- **Cloud Provider**: support.aws.com (if using AWS)
- **Monitoring**: support@grafana.com
- **SSL Certificates**: support@letsencrypt.org

---

## Appendix

### Useful Commands

```bash
# View all containers
docker-compose ps

# View logs for specific service
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Check database size
docker-compose exec postgres psql -U smartport -c "SELECT pg_size_pretty(pg_database_size('smartport'));"

# Check InfluxDB cardinality
docker-compose exec influxdb influx query 'import "influxdata/influxdb/schema" schema.measurementCardinality(bucket:"smartport")'

# Export Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Nginx access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Log Locations

- **Backend**: `docker-compose logs backend`
- **Gateway**: `docker-compose logs gateway`
- **PostgreSQL**: `docker-compose logs postgres`
- **InfluxDB**: `docker-compose logs influxdb`
- **Redis**: `docker-compose logs redis`
- **Nginx**: `/var/log/nginx/` (inside container)
- **System**: `/var/log/smartport/`

---

**Document Version History**:
- v1.0 (2025-10-28): Initial operational runbook created
