#!/bin/bash
# Validation Script for PDCA #1, #2, #5 Deployment
# ================================================
# Automated testing for production deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}=================================================="
echo "OptiFlow AI - PDCA Deployment Validation"
echo "=================================================="
echo -e "${NC}"

# ===========================================
# Helper Functions
# ===========================================

print_test() {
    echo -e "\n${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS${NC} - $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL${NC} - $1"
    ((TESTS_FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} - $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO${NC} - $1"
}

# ===========================================
# PDCA #1: Network Segmentation Tests
# ===========================================

echo -e "\n${BLUE}=========================================="
echo "PDCA #1: Network Segmentation OT/IT"
echo "==========================================${NC}\n"

print_test "Checking if containers are running..."
if docker ps | grep -q optiflow-backend && docker ps | grep -q optiflow-gateway; then
    print_pass "Backend and Gateway containers are running"
else
    print_fail "Required containers not running"
    echo "  Run: docker-compose up -d"
    exit 1
fi

print_test "Network isolation: Backend CANNOT reach OPC UA server..."
if docker exec optiflow-backend ping -c 1 -W 2 opcua-server 2>&1 | grep -q "Name or service not known\|Network is unreachable"; then
    print_pass "Backend correctly isolated from OT network"
elif ! docker ps | grep -q opcua-server; then
    print_warn "OPC UA server not running (test skipped)"
else
    print_fail "Backend can reach OPC UA server (security risk!)"
fi

print_test "Data diode: Gateway CAN reach OPC UA server..."
if ! docker ps | grep -q opcua-server; then
    print_warn "OPC UA server not running (test skipped)"
elif docker exec optiflow-gateway ping -c 1 -W 2 opcua-server > /dev/null 2>&1; then
    print_pass "Gateway can reach OPC UA server (data diode working)"
else
    print_fail "Gateway cannot reach OPC UA server"
fi

print_test "Gateway CAN reach Backend..."
if docker exec optiflow-gateway ping -c 1 -W 2 backend > /dev/null 2>&1; then
    print_pass "Gateway can reach Backend"
else
    print_fail "Gateway cannot reach Backend"
fi

print_test "Verifying network configuration..."
if docker network inspect optiflow_ot-network 2>/dev/null | grep -q '"Internal": true'; then
    print_pass "OT network is internal (isolated)"
else
    print_warn "OT network may not be properly isolated"
fi

if docker network inspect optiflow_it-network > /dev/null 2>&1; then
    print_pass "IT network exists"
else
    print_fail "IT network not found"
fi

# ===========================================
# PDCA #5: Critical Alarms Tests
# ===========================================

echo -e "\n${BLUE}=========================================="
echo "PDCA #5: Critical Alarms"
echo "==========================================${NC}\n"

print_test "Checking if frontend is accessible..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_pass "Frontend is accessible on port 3000"
else
    print_fail "Frontend not accessible (expected HTTP 200)"
fi

print_test "Checking if backend API is healthy..."
if curl -s http://localhost:8000/api/health | grep -q "healthy\|ok"; then
    print_pass "Backend API is healthy"
else
    print_fail "Backend API health check failed"
fi

print_test "Checking if alarm components exist..."
if [ -f "$PROJECT_ROOT/frontend/src/components/CriticalAlarmNotification.tsx" ]; then
    print_pass "CriticalAlarmNotification component exists"
else
    print_fail "CriticalAlarmNotification component not found"
fi

if [ -f "$PROJECT_ROOT/frontend/src/hooks/useCriticalAlarms.ts" ]; then
    print_pass "useCriticalAlarms hook exists"
else
    print_fail "useCriticalAlarms hook not found"
fi

print_info "Manual test required: Create test alarm and verify visual/audio alerts"
echo "  Run this command (replace TOKEN):"
echo "  curl -X POST http://localhost:8000/api/v1/alarms/events \\"
echo "    -H 'Authorization: Bearer \$TOKEN' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"severity\":\"CRITICAL\",\"state\":\"ACTIVE\",\"message\":\"Test\",\"value\":100,\"limit\":85}'"

# ===========================================
# PDCA #2: mTLS Tests
# ===========================================

echo -e "\n${BLUE}=========================================="
echo "PDCA #2: mTLS Gateway ↔ Backend"
echo "==========================================${NC}\n"

print_test "Checking if certificate generation script exists..."
if [ -x "$PROJECT_ROOT/scripts/generate_mtls_certs.sh" ]; then
    print_pass "Certificate generation script found and executable"
else
    print_fail "Certificate generation script not found or not executable"
fi

print_test "Checking if mTLS configuration exists in gateway..."
if grep -q "MTLS_ENABLED" "$PROJECT_ROOT/gateway/app/core/config.py"; then
    print_pass "mTLS configuration added to gateway config"
else
    print_fail "mTLS configuration not found in gateway config"
fi

print_test "Checking if mTLS client implementation exists..."
if [ -f "$PROJECT_ROOT/gateway/app/core/mtls_client.py" ]; then
    print_pass "mTLS client implementation exists"
else
    print_fail "mTLS client implementation not found"
fi

print_test "Checking if certificates directory exists..."
if [ -d "$PROJECT_ROOT/certs" ]; then
    print_info "Certificates directory exists"

    # Check if certificates are generated
    if [ -f "$PROJECT_ROOT/certs/gateway.crt" ] && [ -f "$PROJECT_ROOT/certs/gateway.key" ]; then
        print_pass "Gateway certificates exist"

        # Verify certificate validity
        if openssl verify -CAfile "$PROJECT_ROOT/certs/ca.crt" "$PROJECT_ROOT/certs/gateway.crt" 2>&1 | grep -q "OK"; then
            print_pass "Gateway certificate is valid"
        else
            print_fail "Gateway certificate validation failed"
        fi

        # Check expiration
        EXPIRY_DATE=$(openssl x509 -in "$PROJECT_ROOT/certs/gateway.crt" -noout -enddate | cut -d= -f2)
        print_info "Gateway certificate expires: $EXPIRY_DATE"
    else
        print_warn "Certificates not generated yet - run: ./scripts/generate_mtls_certs.sh"
    fi
else
    print_warn "Certificates directory not found - run: ./scripts/generate_mtls_certs.sh"
fi

print_test "Checking .gitignore for certificate security..."
if grep -q "certs/\*\.key" "$PROJECT_ROOT/.gitignore"; then
    print_pass "Private keys are gitignored (security)"
else
    print_fail "Private keys not gitignored (security risk!)"
fi

# ===========================================
# General System Health
# ===========================================

echo -e "\n${BLUE}=========================================="
echo "General System Health"
echo "==========================================${NC}\n"

print_test "Checking Docker containers status..."
RUNNING_CONTAINERS=$(docker ps --filter "name=optiflow-" --format "{{.Names}}" | wc -l)
if [ "$RUNNING_CONTAINERS" -ge 5 ]; then
    print_pass "$RUNNING_CONTAINERS OptiFlow containers running"
else
    print_warn "Only $RUNNING_CONTAINERS containers running (expected ≥5)"
fi

print_test "Checking for error logs in backend..."
ERROR_COUNT=$(docker logs optiflow-backend --since 5m 2>&1 | grep -i "error\|exception\|critical" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    print_pass "No errors in backend logs (last 5 minutes)"
elif [ "$ERROR_COUNT" -lt 5 ]; then
    print_warn "$ERROR_COUNT errors in backend logs"
else
    print_fail "$ERROR_COUNT errors in backend logs (investigate!)"
fi

print_test "Checking resource usage..."
BACKEND_MEM=$(docker stats --no-stream optiflow-backend --format "{{.MemPerc}}" 2>/dev/null | sed 's/%//')
if [ -n "$BACKEND_MEM" ]; then
    if (( $(echo "$BACKEND_MEM < 80" | bc -l) )); then
        print_pass "Backend memory usage: ${BACKEND_MEM}% (<80%)"
    else
        print_warn "Backend memory usage high: ${BACKEND_MEM}%"
    fi
else
    print_warn "Could not check memory usage"
fi

# ===========================================
# Summary
# ===========================================

echo -e "\n${BLUE}=========================================="
echo "Test Summary"
echo "==========================================${NC}\n"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - System is ready for production!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed - review before deploying to production${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review failed tests above"
    echo "2. Fix issues and re-run this script"
    echo "3. Run manual tests from PRODUCTION_DEPLOYMENT_CHECKLIST.md"
    exit 1
fi
