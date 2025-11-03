#!/bin/bash
#
# SmartPort Smoke Test
# Quick validation that all services are running and responding
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=5

# Test results
PASSED=0
FAILED=0

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

# Test 1: Health endpoint
log_test "Testing health endpoint..."
if curl -f -s --max-time $TIMEOUT "$API_URL/health" > /dev/null; then
    log_pass "Health endpoint is responding"
else
    log_fail "Health endpoint is not responding"
fi

# Test 2: API docs
log_test "Testing API documentation..."
if curl -f -s --max-time $TIMEOUT "$API_URL/docs" > /dev/null; then
    log_pass "API documentation is accessible"
else
    log_fail "API documentation is not accessible"
fi

# Test 3: OpenAPI spec
log_test "Testing OpenAPI spec..."
if curl -f -s --max-time $TIMEOUT "$API_URL/openapi.json" > /dev/null; then
    log_pass "OpenAPI spec is available"
else
    log_fail "OpenAPI spec is not available"
fi

# Test 4: Login endpoint
log_test "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s --max-time $TIMEOUT -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=wrongpassword" \
    -w "%{http_code}" -o /dev/null)

if [ "$LOGIN_RESPONSE" == "401" ]; then
    log_pass "Login endpoint is responding correctly"
else
    log_fail "Login endpoint returned unexpected status: $LOGIN_RESPONSE"
fi

# Test 5: Organizations endpoint (should require auth)
log_test "Testing organizations endpoint without auth..."
ORG_RESPONSE=$(curl -s --max-time $TIMEOUT "$API_URL/api/v1/organizations/" \
    -w "%{http_code}" -o /dev/null)

if [ "$ORG_RESPONSE" == "401" ]; then
    log_pass "Organizations endpoint requires authentication"
else
    log_fail "Organizations endpoint returned unexpected status: $ORG_RESPONSE"
fi

# Test 6: Prometheus metrics (if enabled)
log_test "Testing Prometheus metrics endpoint..."
if curl -f -s --max-time $TIMEOUT "$API_URL/metrics" > /dev/null; then
    log_pass "Prometheus metrics are available"
else
    log_fail "Prometheus metrics are not available"
fi

# Test 7: Database connectivity (via health check detail)
log_test "Testing database connectivity..."
HEALTH_DETAIL=$(curl -s --max-time $TIMEOUT "$API_URL/health")
if echo "$HEALTH_DETAIL" | grep -q "status"; then
    log_pass "Health check returns detailed status"
else
    log_fail "Health check does not return detailed status"
fi

# Test 8: CORS headers
log_test "Testing CORS headers..."
CORS_RESPONSE=$(curl -s --max-time $TIMEOUT -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -X OPTIONS "$API_URL/api/v1/organizations/" \
    -I | grep -i "access-control-allow")

if [ -n "$CORS_RESPONSE" ]; then
    log_pass "CORS headers are configured"
else
    log_fail "CORS headers are not configured"
fi

# Test 9: Rate limiting headers
log_test "Testing rate limiting..."
RATE_LIMIT=$(curl -s --max-time $TIMEOUT "$API_URL/health" -I | grep -i "ratelimit")
if [ -n "$RATE_LIMIT" ]; then
    log_pass "Rate limiting headers are present"
else
    echo -e "${YELLOW}[WARN]${NC} Rate limiting headers not found (may not be exposed)"
fi

# Test 10: Response time
log_test "Testing response time..."
RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null --max-time $TIMEOUT "$API_URL/health")
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    log_pass "Response time is acceptable (${RESPONSE_MS}ms)"
else
    log_fail "Response time is slow (${RESPONSE_MS}ms)"
fi

# Summary
echo ""
echo "================================="
echo "Smoke Test Summary"
echo "================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Smoke test FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}Smoke test PASSED${NC}"
    exit 0
fi
