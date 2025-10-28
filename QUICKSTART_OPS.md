# SmartPort - Quick Start Guide for Operations Team

**Version**: 1.0
**Audience**: New Operations Team Members
**Time to Complete**: 30 minutes

---

## Welcome!

This guide will get you up and running with SmartPort operations in 30 minutes. For comprehensive details, see:
- **RUNBOOK.md** - Daily operations and troubleshooting
- **DEPLOYMENT.md** - Deployment procedures
- **MONITORING.md** - Monitoring and alerting
- **PRODUCTION_CHECKLIST.md** - Deployment checklists

---

## Step 1: Get Access (5 minutes)

### Server Access

```bash
# SSH to production server
ssh ops@your-server-ip

# Verify you can access Docker
docker ps

# Navigate to SmartPort directory
cd /opt/smartport
```

### Monitoring Access

1. **Grafana**: https://grafana.yourdomain.com:3001
   - Username: `admin`
   - Password: (get from team lead)

2. **Prometheus**: http://your-server-ip:9090
   - No auth (internal only)

3. **API Docs**: https://api.yourdomain.com/docs
   - Interactive API documentation

---

## Step 2: Essential Commands (5 minutes)

### Check System Status

```bash
# View all running containers
docker-compose -f docker-compose.prod.yml ps

# Should see all with status "Up (healthy)":
# ✓ backend
# ✓ postgres
# ✓ influxdb
# ✓ redis
# ✓ gateway
# ✓ frontend
```

### Quick Health Check

```bash
# Run automated smoke test (10 checks, ~30 seconds)
./scripts/smoke-test.sh

# Expected output: "Smoke test PASSED" in green
```

### View Logs

```bash
# View logs for all services (live)
docker-compose -f docker-compose.prod.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# View last 50 lines
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# Search for errors in last hour
docker-compose -f docker-compose.prod.yml logs --since=1h | grep -i error
```

### Resource Usage

```bash
# Check CPU, Memory, Network usage
docker stats --no-stream

# Check disk space
df -h

# Check Docker disk usage
docker system df
```

---

## Step 3: Daily Routine (5 minutes)

### Morning Checklist (5 minutes)

```bash
# 1. Check all services healthy
docker-compose -f docker-compose.prod.yml ps

# 2. Run smoke test
./scripts/smoke-test.sh

# 3. Check disk space (should be < 80%)
df -h | grep -E '(Filesystem|/$)'

# 4. Check for errors in last 24 hours
docker-compose -f docker-compose.prod.yml logs --since=24h | grep -i error | wc -l

# 5. Verify last backup exists
ls -lh /var/backups/smartport/ | head -5
```

### Evening Checklist (3 minutes)

```bash
# 1. Open Grafana dashboard
# URL: https://grafana.yourdomain.com:3001/d/smartport-overview

# 2. Check Prometheus for active alerts
# URL: http://your-server-ip:9090/alerts
# Expected: No firing alerts (or only warnings)

# 3. Verify today's backup completed
ls -l /var/backups/smartport/*$(date +%Y-%m-%d)*
```

---

## Step 4: Common Tasks (5 minutes)

### Restart a Service

```bash
# Restart backend only
docker-compose -f docker-compose.prod.yml restart backend

# Wait for health check
sleep 30

# Verify it's healthy
docker-compose -f docker-compose.prod.yml ps backend
./scripts/smoke-test.sh
```

### Restart All Services

```bash
# Restart everything (brief downtime)
docker-compose -f docker-compose.prod.yml restart

# Wait for all services
sleep 60

# Verify all healthy
docker-compose -f docker-compose.prod.yml ps
./scripts/smoke-test.sh
```

### Manual Backup

```bash
# Run backup script
./scripts/backup.sh

# Verify backup created
ls -lh /var/backups/smartport/ | head -5

# Backup files:
# - smartport_postgres_YYYYMMDD_HHMMSS.sql.gz (PostgreSQL)
# - smartport_influxdb_YYYYMMDD_HHMMSS.tar.gz (InfluxDB)
```

### Check API Health

```bash
# Health endpoint (should return 200)
curl -I http://localhost:8000/health

# Test login endpoint (should return 401 for wrong password)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=wrong"

# Should return: {"detail":"Incorrect username or password"}
```

---

## Step 5: Troubleshooting Basics (5 minutes)

### Problem: API Not Responding

```bash
# Check if backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs --tail=50 backend

# Try restarting backend
docker-compose restart backend
sleep 30
curl http://localhost:8000/health
```

### Problem: High CPU Usage

```bash
# Find which container is using CPU
docker stats --no-stream

# Check for slow database queries
docker-compose exec postgres psql -U smartport -c \
  "SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle';"

# If needed, restart the heavy service
docker-compose restart <service-name>
```

### Problem: Disk Space Full

```bash
# Check what's using space
du -sh /* | sort -h | tail -10

# Clean Docker (safe, removes unused images/containers)
docker system prune -a --volumes -f

# Clean old logs
docker-compose logs --no-log-prefix > /dev/null

# Clean old backups (keep last 7 days)
find /var/backups/smartport -name "*.gz" -mtime +7 -delete
```

### Problem: Service Won't Start

```bash
# Check why service failed
docker-compose logs <service-name>

# Check if port is already in use
sudo netstat -tuln | grep <port-number>

# Force recreate container
docker-compose up -d --force-recreate <service-name>
```

---

## Step 6: Monitoring Basics (5 minutes)

### Grafana Dashboards

1. **Open**: https://grafana.yourdomain.com:3001
2. **Login**: admin / (your password)
3. **Navigate**: Dashboards → SmartPort Overview

**Key Panels to Watch**:
- **System Overview**: All services status (should be green/up)
- **API Response Time**: Should be < 500ms (P95)
- **Error Rate**: Should be < 1%
- **CPU Usage**: Should be < 70%
- **Memory Usage**: Should be < 80%
- **Database Connections**: Should be < 80% of max

### Prometheus Alerts

1. **Open**: http://your-server-ip:9090/alerts
2. **Check Status**:
   - **Green (Inactive)**: Good, no issues
   - **Yellow (Pending)**: Warning, monitor closely
   - **Red (Firing)**: Critical, take action now

**Critical Alerts** (require immediate action):
- `SystemDown` - System completely unavailable
- `HighCPUUsage` - CPU > 80% for 5 minutes
- `HighMemoryUsage` - Memory > 85% for 5 minutes
- `HighDiskUsage` - Disk > 90%
- `DatabaseDown` - Cannot connect to database

### Checking Metrics

```bash
# API response time (should be < 0.5 seconds)
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Create curl-format.txt file:
cat > curl-format.txt <<'EOF'
time_namelookup:  %{time_namelookup}\n
time_connect:     %{time_connect}\n
time_starttransfer: %{time_starttransfer}\n
time_total:       %{time_total}\n
EOF
```

---

## Emergency Contacts

| Severity | Contact | Response Time |
|----------|---------|---------------|
| **P0 - System Down** | Emergency Hotline: +1-555-0100 | Immediate |
| **P1 - Major Issue** | Engineering Team: dev@smartport.com | 1 hour |
| **P2 - Minor Issue** | Operations Team: ops@smartport.com | 4 hours |
| **Questions** | Slack: #smartport-ops | Best effort |

---

## Quick Reference

### File Locations

```bash
# Application
/opt/smartport/                    # Main directory

# Backups
/var/backups/smartport/            # Backup storage

# Logs
docker-compose logs <service>      # Container logs
/var/log/smartport/               # System logs (if configured)

# Configuration
/opt/smartport/.env.prod          # Production config
/opt/smartport/docker-compose.prod.yml  # Docker services
```

### Essential Scripts

```bash
./scripts/smoke-test.sh           # Quick health check
./scripts/backup.sh               # Manual backup
./scripts/restore.sh              # Restore from backup
./scripts/deploy.sh               # Deploy new version
./scripts/failover-test.sh        # Test service recovery
./scripts/run-all-tests.sh        # Run all tests
```

### Service Ports

| Service | Internal Port | External Access |
|---------|---------------|-----------------|
| Frontend | 3000 | https://yourdomain.com |
| Backend API | 8000 | https://api.yourdomain.com |
| PostgreSQL | 5432 | Internal only |
| InfluxDB | 8086 | Internal only |
| Redis | 6379 | Internal only |
| Gateway | 8081 | Internal only |
| Prometheus | 9090 | Internal/VPN only |
| Grafana | 3001 | Internal/VPN only |

---

## Next Steps

After completing this quick start:

1. **Read RUNBOOK.md** - Comprehensive operations guide
2. **Review MONITORING.md** - Detailed monitoring procedures
3. **Practice in staging** - Try common tasks safely
4. **Shadow experienced operator** - Learn from their workflow
5. **Complete certification** - Pass operations quiz

---

## Cheat Sheet

### One-Liner Commands

```bash
# Status check
docker-compose -f docker-compose.prod.yml ps && ./scripts/smoke-test.sh

# Full restart with health check
docker-compose -f docker-compose.prod.yml restart && sleep 60 && ./scripts/smoke-test.sh

# Quick troubleshoot
docker stats --no-stream && df -h && docker-compose -f docker-compose.prod.yml logs --tail=50 | grep -i error

# Emergency: restart everything
docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d && sleep 60 && ./scripts/smoke-test.sh

# Backup and verify
./scripts/backup.sh && ls -lh /var/backups/smartport/ | head -5
```

---

## Success Criteria

You've successfully completed the quick start when you can:

- [ ] SSH to the server and navigate to /opt/smartport
- [ ] Run smoke test and interpret results
- [ ] View logs for any service
- [ ] Check system status and resource usage
- [ ] Restart a service safely
- [ ] Access and understand Grafana dashboards
- [ ] Run manual backup
- [ ] Identify and escalate critical alerts

---

## Tips from Experienced Operators

1. **Always check logs first** - Most issues show up in logs before alerts
2. **Don't panic restart** - Check logs and metrics before restarting
3. **Document everything** - Update runbook with new issues/solutions
4. **Test in staging first** - Never try new commands in production first
5. **Keep backups current** - Verify backups daily, test restores weekly
6. **Monitor trends** - Daily small changes can indicate future problems
7. **Know your limits** - Escalate early rather than make it worse

---

## Questions?

- **Slack**: #smartport-ops
- **Email**: ops@smartport.com
- **Emergency**: +1-555-0100 (24/7)
- **Documentation**: /opt/smartport/docs/

---

**Welcome to the SmartPort Operations Team!**

You've got this! 🚀
