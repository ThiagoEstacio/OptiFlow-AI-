# Production Deployment Checklist
## OptiFlow AI Platform - PDCAs #1, #2, #5

**Date**: 2025-11-18
**Version**: Post-PDCA Security Enhancements
**Branch**: `claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf`

---

## 📋 Pre-Deployment Validation

### ✅ PDCA #1: Network Segmentation OT/IT

#### Test 1: Verify Network Isolation
```bash
# Start containers
docker-compose down
docker-compose up -d

# Wait for services to be healthy
sleep 30

# TEST: Backend CANNOT reach OPC UA server (isolated OT network)
docker exec optiflow-backend ping -c 3 opcua-server
# Expected: "ping: opcua-server: Name or service not known" ✅

# TEST: Gateway CAN reach OPC UA server (has access to both networks)
docker exec optiflow-gateway ping -c 3 opcua-server
# Expected: "3 packets transmitted, 3 received" ✅

# TEST: Gateway CAN reach Backend
docker exec optiflow-gateway ping -c 3 backend
# Expected: "3 packets transmitted, 3 received" ✅
```

#### Test 2: Verify Network Configuration
```bash
# Check network assignments
docker network ls | grep optiflow

# Expected output:
# ot-network    (internal: true)
# it-network    (internal: false)
# optiflow-network (legacy)

# Inspect OT network (should be internal)
docker network inspect optiflow_ot-network | grep Internal
# Expected: "Internal": true ✅

# List services on each network
docker network inspect optiflow_ot-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Expected: opcua-server, gateway ✅

docker network inspect optiflow_it-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Expected: gateway, backend, frontend, postgres, redis, etc. ✅
```

**Status**: [ ] Pass  [ ] Fail
**Notes**: _______________________________________________________

---

### ✅ PDCA #5: Critical Alarms

#### Test 1: Trigger Critical Alarm
```bash
# Start frontend (if not running)
docker-compose up -d frontend

# Wait for frontend to be ready
sleep 10

# Create test CRITICAL alarm via API
TOKEN="<YOUR_JWT_TOKEN>"  # Get from http://localhost:3000 after login

curl -X POST http://localhost:8000/api/v1/alarms/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "state": "ACTIVE",
    "message": "TEST: Critical temperature alarm",
    "tag_name": "Silo 1 - Temperatura",
    "value": 95.5,
    "limit": 85.0,
    "alarm_type": "HIGH_LIMIT"
  }'

# Expected: Alarm created successfully (HTTP 200/201)
```

#### Test 2: Visual/Audio Verification
Open browser: http://localhost:3000

**Expected Behavior**:
- [ ] Screen flashes red every 500ms
- [ ] Audio beep plays (3x beeps, 880Hz)
- [ ] Notification appears in top-right corner
- [ ] Shows alarm details (tag name, value, limit, time)
- [ ] "ACKNOWLEDGE ALARM" button is visible
- [ ] Clicking button dismisses alarm
- [ ] Screen flash stops after acknowledgement

#### Test 3: Multiple Alarms Queue
```bash
# Create multiple alarms with different severities
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/v1/alarms/events \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"severity\": \"CRITICAL\",
      \"state\": \"ACTIVE\",
      \"message\": \"Test alarm $i\",
      \"tag_name\": \"Test Tag $i\",
      \"value\": 100,
      \"limit\": 85
    }"
  sleep 1
done
```

**Expected**:
- [ ] Shows first CRITICAL alarm immediately
- [ ] After acknowledging, shows next alarm in queue
- [ ] Processes all alarms sequentially

#### Test 4: Sound Toggle
**Expected**:
- [ ] Mute button (🔇) appears in notification
- [ ] Clicking mute stops audio beeps
- [ ] Icon changes to 🔊 when sound enabled

**Status**: [ ] Pass  [ ] Fail
**Notes**: _______________________________________________________

---

### ✅ PDCA #2: mTLS Gateway ↔ Backend

#### Test 1: Generate Certificates
```bash
# Generate test certificates
cd /home/thiestacio/OptiFlow-AI-
./scripts/generate_mtls_certs.sh

# Expected output:
# ✅ Root CA created: ca.crt (valid 10 years)
# ✅ Gateway certificate created: gateway.crt (valid 90 days)
# ✅ Backend certificate created: backend.crt (valid 90 days)

# Verify certificates exist
ls -la certs/
# Expected files:
# ca.crt, ca.key
# gateway.crt, gateway.key
# backend.crt, backend.key
```

#### Test 2: Verify Certificate Chain
```bash
# Verify gateway certificate
openssl verify -CAfile certs/ca.crt certs/gateway.crt
# Expected: "certs/gateway.crt: OK" ✅

# Verify backend certificate
openssl verify -CAfile certs/ca.crt certs/backend.crt
# Expected: "certs/backend.crt: OK" ✅

# Check expiration dates
openssl x509 -in certs/gateway.crt -noout -dates
# Expected: Valid for 90 days from today ✅
```

#### Test 3: mTLS Configuration (Optional - Disabled by Default)
```bash
# mTLS is DISABLED by default (requires backend changes)
# To enable in future:

# 1. Update docker-compose.yml
#   gateway:
#     environment:
#       MTLS_ENABLED: "true"
#     volumes:
#       - ./certs:/app/certs:ro

# 2. Update backend to require client certificates
# 3. Restart services
# 4. Test connection
```

**Note**: mTLS implementation is **infrastructure-ready** but disabled by default.
Enable only after backend supports certificate verification.

**Status**: [ ] Certificates Generated  [ ] mTLS Enabled (Optional)
**Notes**: _______________________________________________________

---

## 🚀 Production Deployment Steps

### Step 1: Backup Current State
```bash
# Backup database
docker exec optiflow-postgres pg_dump -U optiflow optiflow > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup InfluxDB
docker exec optiflow-influxdb influx backup /tmp/influx_backup
docker cp optiflow-influxdb:/tmp/influx_backup ./influx_backup_$(date +%Y%m%d_%H%M%S)

# Backup .env files
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
cp docker-compose.yml docker-compose.yml.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Deploy Network Segmentation
```bash
# Stop all containers
docker-compose down

# Pull latest code (if from git)
git pull origin <branch-name>

# Rebuild containers (network changes)
docker-compose build --no-cache backend gateway frontend

# Start with new network configuration
docker-compose up -d

# Verify all services healthy
docker-compose ps
# Expected: All services "healthy" or "running" ✅
```

### Step 3: Verify Services
```bash
# Check backend health
curl http://localhost:8000/api/health
# Expected: {"status": "healthy"} ✅

# Check frontend
curl http://localhost:3000
# Expected: HTML response ✅

# Check gateway logs (should show network isolation)
docker logs optiflow-gateway --tail 50 | grep "network"
```

### Step 4: Monitor for Issues
```bash
# Watch logs in real-time
docker-compose logs -f --tail=100 backend gateway

# Monitor resource usage
docker stats optiflow-backend optiflow-gateway optiflow-influxdb

# Expected:
# - CPU < 50% (normal load)
# - Memory < 80% of limit
# - No error spikes in logs
```

### Step 5: Rollback Plan (If Issues)
```bash
# If deployment fails, rollback to previous version:

# 1. Stop containers
docker-compose down

# 2. Restore previous docker-compose.yml
cp docker-compose.yml.backup_<timestamp> docker-compose.yml

# 3. Restore database (if needed)
cat backup_<timestamp>.sql | docker exec -i optiflow-postgres psql -U optiflow

# 4. Start containers
docker-compose up -d
```

---

## 📊 Post-Deployment Validation

### Functional Tests

#### Test 1: Data Collection (Gateway → Backend)
```bash
# Verify tags are being collected
curl http://localhost:8000/api/v1/tags | jq '.[] | .name'

# Check recent timeseries data
curl http://localhost:8000/api/v1/timeseries?limit=10 | jq '.[].value'

# Expected: Fresh data with recent timestamps ✅
```

#### Test 2: Real-time Dashboard
1. Open http://localhost:3000
2. Login with credentials
3. Navigate to "Real-time" page
4. **Expected**:
   - [ ] Tags updating every 1-2 seconds
   - [ ] Charts rendering correctly
   - [ ] No console errors

#### Test 3: Alarm System
1. Navigate to "Alarms" page
2. Check active alarms
3. Create test alarm (see PDCA #5 Test 1)
4. **Expected**:
   - [ ] Critical alarm notification appears
   - [ ] Audio beep plays
   - [ ] Acknowledgement works

---

## 🔒 Security Validation

### Network Security
- [ ] OT network isolated (backend cannot reach PLCs)
- [ ] Gateway can reach both OT and IT networks
- [ ] No unexpected network connections

### Certificate Security
- [ ] Private keys (*.key) NOT committed to git
- [ ] Certificates valid and not expired
- [ ] Certificate permissions: 600 for keys, 644 for certs

### Access Control
- [ ] Frontend requires authentication
- [ ] API endpoints require valid JWT tokens
- [ ] No default passwords in production

---

## 📈 Performance Validation

### Resource Usage
```bash
# Check CPU/Memory usage
docker stats --no-stream | grep optiflow

# Expected:
# - Backend: <2GB RAM, <50% CPU
# - Gateway: <500MB RAM, <30% CPU
# - Frontend: <200MB RAM, <10% CPU
# - Databases: <4GB RAM combined
```

### Latency
```bash
# Test API response time
time curl http://localhost:8000/api/health

# Expected: <100ms ✅

# Test WebSocket latency (check browser console)
# Expected: <50ms ping/pong ✅
```

### Throughput (1000 tags @ 1Hz test)
```bash
# Monitor gateway performance
docker logs optiflow-gateway | grep "batch"

# Expected:
# - Batch reading: ~100ms per batch (100 tags)
# - No backpressure warnings
# - CPU usage stable (<50%)
```

---

## ✅ Production Readiness Checklist

### Pre-Deployment
- [ ] All tests passed
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Team notified of deployment

### During Deployment
- [ ] Network segmentation verified
- [ ] Services started successfully
- [ ] No critical errors in logs
- [ ] Health checks passing

### Post-Deployment
- [ ] Data collection working
- [ ] Alarms functioning
- [ ] Dashboards loading
- [ ] Performance acceptable
- [ ] No security issues

### Documentation
- [ ] PDCA implementations documented
- [ ] Production config documented
- [ ] Troubleshooting guide available
- [ ] Team trained on new features

---

## 🆘 Troubleshooting

### Issue: Backend Cannot Reach Database
**Symptom**: Backend errors: "connection refused"
**Cause**: Database not on `it-network`
**Fix**:
```bash
# Check database network
docker inspect optiflow-postgres | grep NetworkMode

# Should be: "optiflow_it-network"
# If not, check docker-compose.yml networks section
```

### Issue: Critical Alarms Not Showing
**Symptom**: No notification appears after creating alarm
**Possible Causes**:
1. Frontend not polling: Check browser console for errors
2. API authentication: Check JWT token validity
3. Alarm severity: Only CRITICAL/HIGH trigger notifications

**Debug**:
```bash
# Check alarm was created
curl http://localhost:8000/api/v1/alarms/events?state=ACTIVE

# Check frontend logs
docker logs optiflow-frontend | grep -i alarm
```

### Issue: Audio Beep Not Playing
**Symptom**: Screen flashes but no sound
**Cause**: Browser autoplay policy
**Fix**: User must interact with page first (click anywhere)

### Issue: Network Isolation Not Working
**Symptom**: Backend CAN ping opcua-server (should fail)
**Debug**:
```bash
# Verify network is internal
docker network inspect optiflow_ot-network | grep Internal
# Should be: "Internal": true

# Check service networks
docker inspect optiflow-backend | grep -A 10 Networks
# Should NOT include "ot-network"
```

---

## 📞 Support Contacts

**Deployment Issues**: DevOps Team
**Security Concerns**: Security Team
**Performance Issues**: Backend Team
**UI/UX Issues**: Frontend Team

---

## 📝 Deployment Log

| Date | Version | Deployed By | Status | Notes |
|------|---------|-------------|--------|-------|
| 2025-11-18 | PDCA #1,#2,#5 | Claude Code | ⏳ Pending | Initial deployment |
|      |         |             |        |       |
|      |         |             |        |       |

---

**Last Updated**: 2025-11-18
**Next Review**: After 7 days in production
**OptiFlow AI Platform** - Industrial IoT & ML Platform
