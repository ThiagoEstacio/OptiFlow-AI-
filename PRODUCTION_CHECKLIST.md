# SmartPort Production Deployment Checklist

**Version**: 1.0
**Last Updated**: 2025-10-28

Use this checklist for every production deployment to ensure nothing is missed.

---

## Pre-Deployment Checklist

### 1. Code & Testing (Development Team)

- [ ] All code merged to main branch
- [ ] All unit tests passing (`pytest tests/ -v`)
- [ ] All integration tests passing (`pytest tests/integration/ -v`)
- [ ] Load tests completed successfully (`k6 run load-testing/load-test.js`)
- [ ] Smoke tests passing (`./scripts/smoke-test.sh`)
- [ ] Code review completed and approved
- [ ] Security scan completed (no critical vulnerabilities)
- [ ] API documentation up to date (`/docs` endpoint)

**Verification Command**:
```bash
./scripts/run-all-tests.sh
```

**Expected Result**: All tests pass, no failures

---

### 2. Configuration & Secrets (DevOps Team)

- [ ] `.env.prod` created and configured
- [ ] All secrets generated and stored securely
  - [ ] `SECRET_KEY` (32+ characters, random)
  - [ ] `POSTGRES_PASSWORD` (strong password)
  - [ ] `REDIS_PASSWORD` (strong password)
  - [ ] `INFLUXDB_TOKEN` (generated via InfluxDB setup)
  - [ ] `GF_SECURITY_ADMIN_PASSWORD` (Grafana admin)
- [ ] CORS origins configured correctly
- [ ] Rate limiting configured appropriately
- [ ] Backup destinations configured (S3/local)
- [ ] Monitoring endpoints accessible
- [ ] SSL certificates obtained (Let's Encrypt)

**Verification Command**:
```bash
# Check all required environment variables are set
grep -E "CHANGE_ME|TODO" .env.prod
```

**Expected Result**: No matches (all placeholders replaced)

---

### 3. Infrastructure (Operations Team)

- [ ] Server provisioned and accessible
- [ ] Docker and Docker Compose installed
- [ ] Sufficient disk space (minimum 100GB)
- [ ] Sufficient RAM (minimum 16GB)
- [ ] Sufficient CPU (minimum 4 cores)
- [ ] Firewall rules configured
  - [ ] Port 80 (HTTP) open
  - [ ] Port 443 (HTTPS) open
  - [ ] Port 22 (SSH) restricted to admin IPs
  - [ ] All other ports blocked
- [ ] DNS records configured
  - [ ] `yourdomain.com` → Server IP
  - [ ] `api.yourdomain.com` → Server IP
  - [ ] `grafana.yourdomain.com` → Server IP
- [ ] SSL/TLS certificates configured
- [ ] Backup storage available (S3 or local)
- [ ] Log aggregation configured (optional)

**Verification Command**:
```bash
# Check disk space
df -h

# Check memory
free -h

# Check Docker installation
docker --version
docker-compose --version

# Test firewall
sudo iptables -L -n
```

---

### 4. Database Preparation

- [ ] PostgreSQL data directory prepared
- [ ] InfluxDB data directory prepared
- [ ] Database initialization scripts ready
- [ ] Database backups scheduled (cron job)
- [ ] Database connection pooling configured
- [ ] Database performance tuning applied

**Verification Command**:
```bash
# Check data directories exist
ls -la /var/lib/docker/volumes/smartport_postgres_data
ls -la /var/lib/docker/volumes/smartport_influxdb_data

# Check cron job configured
crontab -l | grep backup
```

---

### 5. Monitoring & Alerting

- [ ] Prometheus configured and running
- [ ] Grafana configured and accessible
- [ ] Alertmanager configured with notification channels
- [ ] Alert rules configured (66 alerts)
- [ ] Dashboards imported
- [ ] Test alert sent and received
- [ ] On-call rotation configured

**Verification Command**:
```bash
# Check Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Check Grafana is accessible
curl -I http://localhost:3001/api/health
```

**Expected Result**: All targets "up", Grafana returns 200 OK

---

## Deployment Checklist

### Phase 1: Staging Deployment (Required First)

- [ ] Deploy to staging environment
- [ ] Run full test suite in staging
- [ ] Perform manual QA in staging
- [ ] Load test staging environment
- [ ] Security scan staging environment
- [ ] Verify monitoring works in staging
- [ ] Staging sign-off obtained

**Deployment Command**:
```bash
# Copy staging environment file
cp .env.staging .env

# Deploy to staging
./scripts/deploy.sh
```

**Verification**: Complete [Post-Deployment Checklist](#post-deployment-checklist) for staging

---

### Phase 2: Production Deployment

#### Step 1: Pre-Deployment Backup

- [ ] Backup current production data (if updating existing)
- [ ] Backup location verified
- [ ] Backup restoration tested

**Command**:
```bash
./scripts/backup.sh
```

---

#### Step 2: Maintenance Mode (If Applicable)

- [ ] Maintenance banner displayed to users
- [ ] Users notified of maintenance window
- [ ] Current sessions allowed to complete

---

#### Step 3: Deploy Services

- [ ] Environment file copied to production
- [ ] Secrets file secured (600 permissions)
- [ ] Docker images pulled
- [ ] Containers started
- [ ] Health checks passing

**Command**:
```bash
# Copy production environment
cp .env.prod .env

# Set correct permissions
chmod 600 .env

# Deploy
./scripts/deploy.sh
```

---

#### Step 4: Database Migration

- [ ] Database schema migrations executed
- [ ] Migration logs reviewed
- [ ] No migration errors

**Command**:
```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic current
```

**Expected Result**: Shows latest migration applied

---

#### Step 5: Seed Initial Data (First Deployment Only)

- [ ] Default organization created
- [ ] Admin user created
- [ ] Test site created (optional)
- [ ] System settings configured

**Command**:
```bash
# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

---

## Post-Deployment Checklist

### Immediate Verification (5 minutes)

- [ ] All containers running
- [ ] Health endpoints responding
- [ ] API documentation accessible
- [ ] Frontend loads correctly
- [ ] Can login with admin credentials
- [ ] Database connections established
- [ ] InfluxDB accepting data
- [ ] Redis responding

**Verification Commands**:
```bash
# Check containers
docker-compose ps

# Run smoke test
./scripts/smoke-test.sh

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

### Functional Testing (15 minutes)

- [ ] **Authentication**
  - [ ] User can login
  - [ ] User can logout
  - [ ] Invalid credentials rejected
  - [ ] Token expiration works
- [ ] **Organizations**
  - [ ] Can create organization
  - [ ] Can list organizations
  - [ ] Can update organization
  - [ ] Can delete organization
- [ ] **Sites**
  - [ ] Can create site
  - [ ] Can list sites
  - [ ] Can update site
  - [ ] Can delete site
- [ ] **Devices**
  - [ ] Can create device
  - [ ] Can list devices
  - [ ] Can update device
  - [ ] Can delete device
- [ ] **Tags**
  - [ ] Can create tag
  - [ ] Can list tags
  - [ ] Can read tag data
  - [ ] Can write tag data
- [ ] **Alarms**
  - [ ] Alarms are generated
  - [ ] Can acknowledge alarm
  - [ ] Alarm history visible

**Test Script** (save as `test-production.sh`):
```bash
#!/bin/bash
API_URL="http://localhost:8000"
TOKEN=""

# Login
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"

# Test organization
ORG_ID=$(curl -s -X POST "$API_URL/api/v1/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Org"}' | jq -r '.id')

echo "Organization created: $ORG_ID"

# Continue with other tests...
```

---

### Performance Verification (10 minutes)

- [ ] **Response Times**
  - [ ] Health endpoint < 100ms
  - [ ] Login endpoint < 500ms
  - [ ] List endpoints < 500ms
  - [ ] Detail endpoints < 200ms
- [ ] **Resource Usage**
  - [ ] CPU usage < 50%
  - [ ] Memory usage < 70%
  - [ ] Disk I/O normal
  - [ ] Network latency < 50ms
- [ ] **Database Performance**
  - [ ] Query response time < 100ms
  - [ ] Connection pool healthy
  - [ ] No slow queries

**Verification Command**:
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Check resource usage
docker stats --no-stream

# Check database performance
docker-compose exec postgres psql -U smartport -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

---

### Security Verification (10 minutes)

- [ ] **HTTPS**
  - [ ] SSL certificate valid
  - [ ] HTTPS redirect working
  - [ ] No mixed content warnings
- [ ] **Authentication**
  - [ ] Unauthenticated requests rejected
  - [ ] Invalid tokens rejected
  - [ ] Expired tokens rejected
- [ ] **Rate Limiting**
  - [ ] Rate limits enforced
  - [ ] Rate limit headers present
  - [ ] 429 status code returned when exceeded
- [ ] **CORS**
  - [ ] Only allowed origins accepted
  - [ ] Credentials handled correctly
  - [ ] Preflight requests work
- [ ] **Security Headers**
  - [ ] X-Content-Type-Options present
  - [ ] X-Frame-Options present
  - [ ] Strict-Transport-Security present

**Verification Commands**:
```bash
# Check SSL
curl -vI https://yourdomain.com 2>&1 | grep "SSL certificate verify"

# Check rate limiting
for i in {1..10}; do
  curl -I http://localhost:8000/api/v1/auth/login
done

# Check CORS
curl -H "Origin: http://evil.com" -I http://localhost:8000/api/v1/organizations/

# Check security headers
curl -I https://yourdomain.com | grep -E "X-Content-Type|X-Frame|Strict-Transport"
```

---

### Monitoring Verification (5 minutes)

- [ ] **Prometheus**
  - [ ] All targets up and scraping
  - [ ] Metrics being collected
  - [ ] No missing time series
- [ ] **Grafana**
  - [ ] Dashboards loading
  - [ ] Data visible in panels
  - [ ] No panel errors
- [ ] **Alertmanager**
  - [ ] Alert rules loaded
  - [ ] Notification channels configured
  - [ ] Test alert works

**Verification Commands**:
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job:.labels.job, health:.health}'

# Check Grafana datasources
curl -s -u admin:$GRAFANA_PASSWORD http://localhost:3001/api/datasources | jq '.[].name'

# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert"}}]'
```

---

### Backup Verification (2 minutes)

- [ ] Backup script scheduled in cron
- [ ] Backup directory exists and writable
- [ ] Initial backup completed
- [ ] Backup size reasonable
- [ ] Backup restoration tested

**Verification Commands**:
```bash
# Check cron job
crontab -l | grep backup

# Run manual backup
./scripts/backup.sh

# Verify backup created
ls -lh /var/backups/smartport/ | head -5

# Test restore (in staging!)
./scripts/restore.sh --dry-run
```

---

## Post-Deployment Monitoring (24 hours)

### Hour 1-2: Intensive Monitoring

- [ ] Watch Grafana dashboards continuously
- [ ] Monitor error logs in real-time
- [ ] Check CPU/Memory trends
- [ ] Verify no alerts firing
- [ ] Respond to user reports immediately

**Commands**:
```bash
# Watch logs in real-time
docker-compose logs -f --tail=100 backend

# Watch metrics
watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=up | jq'
```

---

### Hour 2-24: Regular Monitoring

- [ ] Check dashboards every 2 hours
- [ ] Review error logs every 4 hours
- [ ] Check backup completed (after 2 AM)
- [ ] Review performance metrics
- [ ] Document any issues

---

### Day 2-7: Normal Operations

- [ ] Daily health check (morning)
- [ ] Review Grafana dashboards (daily)
- [ ] Check Prometheus alerts (daily)
- [ ] Verify backups (daily)
- [ ] Review logs for errors (daily)

---

## Rollback Procedure

If deployment fails or critical issues arise:

### Option 1: Quick Rollback (Service Restart)

```bash
# Restart services with previous configuration
docker-compose down
docker-compose up -d
```

---

### Option 2: Full Rollback (Restore from Backup)

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
./scripts/restore.sh

# 3. Select most recent backup
# Follow prompts

# 4. Start services
docker-compose up -d

# 5. Verify
./scripts/smoke-test.sh
```

---

### Option 3: Database-Only Rollback

```bash
# Restore database only
docker-compose exec postgres psql -U smartport < /path/to/backup.sql
```

---

## Sign-Off

### Development Team

- [ ] Code changes reviewed and approved
- [ ] All tests passing
- [ ] API documentation updated

**Name**: ________________  **Date**: ________  **Signature**: ________________

---

### QA Team

- [ ] Functional testing complete
- [ ] Performance testing complete
- [ ] Security testing complete

**Name**: ________________  **Date**: ________  **Signature**: ________________

---

### Operations Team

- [ ] Infrastructure ready
- [ ] Monitoring configured
- [ ] Backups configured

**Name**: ________________  **Date**: ________  **Signature**: ________________

---

### Management Approval

- [ ] Deployment window approved
- [ ] Resources allocated
- [ ] Risks accepted

**Name**: ________________  **Date**: ________  **Signature**: ________________

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Health check
./scripts/smoke-test.sh

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh

# Check status
docker-compose ps
```

### Essential URLs

- API Health: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Alertmanager: `http://localhost:9093`

### Emergency Contacts

- Operations: ops@smartport.com
- Engineering: dev@smartport.com
- Emergency Hotline: +1-555-0100

---

**Checklist Version**: 1.0
**Created**: 2025-10-28
**Next Review**: 2026-01-28 (quarterly review recommended)
