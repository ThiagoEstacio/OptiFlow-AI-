#!/bin/bash
#
# SmartPort Failover Test
# Tests system recovery from component failures
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
API_URL="${API_URL:-http://localhost:8000}"
RECOVERY_TIMEOUT=60

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

wait_for_service() {
    local service=$1
    local max_attempts=$2
    local attempt=1

    log_info "Waiting for $service to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up (healthy)"; then
            log_pass "$service is healthy"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 5
        ((attempt++))
    done

    log_fail "$service did not become healthy within timeout"
    return 1
}

test_api_responding() {
    log_info "Testing if API is responding..."
    if curl -f -s --max-time 5 "$API_URL/health" > /dev/null; then
        log_pass "API is responding"
        return 0
    else
        log_fail "API is not responding"
        return 1
    fi
}

# Test 1: Backend restart
log_info "================================="
log_info "Test 1: Backend Restart"
log_info "================================="

log_info "Stopping backend..."
docker-compose -f $COMPOSE_FILE stop backend

sleep 5

log_info "Checking API is down..."
if ! test_api_responding; then
    log_pass "API correctly stopped"
else
    log_warn "API still responding (cached?)"
fi

log_info "Starting backend..."
docker-compose -f $COMPOSE_FILE start backend

if wait_for_service "backend" 12; then
    if test_api_responding; then
        log_pass "Backend recovered successfully"
    else
        log_fail "Backend started but not responding"
    fi
else
    log_fail "Backend failed to recover"
fi

sleep 5

# Test 2: Database restart
log_info "================================="
log_info "Test 2: Database Restart"
log_info "================================="

log_info "Stopping PostgreSQL..."
docker-compose -f $COMPOSE_FILE stop postgres

sleep 5

log_info "Starting PostgreSQL..."
docker-compose -f $COMPOSE_FILE start postgres

if wait_for_service "postgres" 12; then
    log_pass "PostgreSQL recovered successfully"

    # Test if backend can reconnect
    sleep 10
    if test_api_responding; then
        log_pass "Backend reconnected to database"
    else
        log_warn "Backend may not have reconnected to database"
    fi
else
    log_fail "PostgreSQL failed to recover"
fi

sleep 5

# Test 3: Redis restart
log_info "================================="
log_info "Test 3: Redis Restart"
log_info "================================="

log_info "Stopping Redis..."
docker-compose -f $COMPOSE_FILE stop redis

sleep 5

log_info "Starting Redis..."
docker-compose -f $COMPOSE_FILE start redis

if wait_for_service "redis" 12; then
    log_pass "Redis recovered successfully"

    # Test if backend still works
    if test_api_responding; then
        log_pass "Backend still functional after Redis restart"
    else
        log_warn "Backend affected by Redis restart"
    fi
else
    log_fail "Redis failed to recover"
fi

sleep 5

# Test 4: InfluxDB restart
log_info "================================="
log_info "Test 4: InfluxDB Restart"
log_info "================================="

log_info "Stopping InfluxDB..."
docker-compose -f $COMPOSE_FILE stop influxdb

sleep 5

log_info "Starting InfluxDB..."
docker-compose -f $COMPOSE_FILE start influxdb

if wait_for_service "influxdb" 12; then
    log_pass "InfluxDB recovered successfully"

    # Test if system still works
    if test_api_responding; then
        log_pass "System still functional after InfluxDB restart"
    else
        log_warn "System affected by InfluxDB restart"
    fi
else
    log_fail "InfluxDB failed to recover"
fi

sleep 5

# Test 5: Gateway restart
log_info "================================="
log_info "Test 5: Gateway Restart"
log_info "================================="

log_info "Stopping Gateway..."
docker-compose -f $COMPOSE_FILE stop gateway

sleep 5

log_info "Starting Gateway..."
docker-compose -f $COMPOSE_FILE start gateway

# Gateway doesn't have health check, so just wait
sleep 15

if docker-compose -f $COMPOSE_FILE ps gateway | grep -q "Up"; then
    log_pass "Gateway recovered successfully"
else
    log_fail "Gateway failed to recover"
fi

# Test 6: Full stack restart
log_info "================================="
log_info "Test 6: Full Stack Restart"
log_info "================================="

log_info "Restarting all services..."
docker-compose -f $COMPOSE_FILE restart

log_info "Waiting for services to stabilize..."
sleep 30

# Check all critical services
SERVICES=("postgres" "influxdb" "redis" "backend")
ALL_UP=true

for service in "${SERVICES[@]}"; do
    if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
        log_pass "$service is running"
    else
        log_fail "$service is not running"
        ALL_UP=false
    fi
done

if $ALL_UP && test_api_responding; then
    log_pass "Full stack recovered successfully"
else
    log_fail "Full stack recovery incomplete"
fi

# Summary
log_info "================================="
log_info "Failover Test Complete"
log_info "================================="
log_info "All services should be running now"
log_info "Check logs for any errors: docker-compose -f $COMPOSE_FILE logs"
