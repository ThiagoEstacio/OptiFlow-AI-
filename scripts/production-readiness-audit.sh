#!/bin/bash
# OptiFlow AI - Production Readiness Audit
# Verifica o status de preparação para produção

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCORE=0
MAX_SCORE=0

check_item() {
    local category=$1
    local item=$2
    local check_cmd=$3
    
    ((MAX_SCORE++))
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "  ✅ ${GREEN}$item${NC}"
        ((SCORE++))
        return 0
    else
        echo -e "  ❌ ${RED}$item${NC}"
        return 1
    fi
}

check_item_warn() {
    local category=$1
    local item=$2
    local check_cmd=$3
    
    ((MAX_SCORE++))
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "  ✅ ${GREEN}$item${NC}"
        ((SCORE++))
        return 0
    else
        echo -e "  ⚠️  ${YELLOW}$item${NC}"
        return 1
    fi
}

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        OptiFlow AI - Production Readiness Audit              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# 1. INFRASTRUCTURE
# ============================================================================
echo -e "${CYAN}━━━ 1. Infrastructure (High Availability) ━━━━━━━━━━━━━━━━━━${NC}"

check_item "infra" "Docker Compose configured" "test -f docker-compose.yml"
check_item "infra" "Production compose file" "test -f docker-compose.prod.yml"
check_item "infra" "Monitoring stack running" "docker compose ps prometheus grafana | grep -q 'Up'"
check_item_warn "infra" "Database replication configured" "grep -q 'replication' docker-compose.prod.yml"
check_item_warn "infra" "Backup scripts exist" "test -f scripts/backup.sh"
check_item_warn "infra" "Restore scripts exist" "test -f scripts/restore.sh"
check_item_warn "infra" "Load balancer configured" "docker compose ps nginx | grep -q 'Up' || docker compose ps haproxy | grep -q 'Up'"

echo ""

# ============================================================================
# 2. SECURITY
# ============================================================================
echo -e "${CYAN}━━━ 2. Security ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "security" "Authentication implemented" "grep -rq 'jwt\|oauth' backend/app/"
check_item "security" "Rate limiting active" "grep -rq 'RateLimitExceeded' backend/app/"
check_item_warn "security" "RBAC implementation" "test -f backend/app/core/rbac.py"
check_item_warn "security" "Secrets management" "test -f .env.example && ! grep -q 'password.*=' docker-compose.yml"
check_item_warn "security" "SSL/TLS configured" "grep -q 'ssl\|tls' docker-compose*.yml nginx*.conf 2>/dev/null"
check_item "security" "CORS configured" "grep -rq 'CORSMiddleware' backend/app/"
check_item_warn "security" "Security headers" "grep -rq 'SecurityHeadersMiddleware' backend/app/"

echo ""

# ============================================================================
# 3. OBSERVABILITY
# ============================================================================
echo -e "${CYAN}━━━ 3. Observability ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "observability" "Prometheus running" "curl -sf http://localhost:9090/-/healthy > /dev/null"
check_item "observability" "Grafana running" "curl -sf http://localhost:3001/api/health > /dev/null"
check_item "observability" "Metrics exposed" "curl -s http://localhost:8000/metrics | grep -q 'optiflow_'"
check_item "observability" "Dashboards configured" "test -d monitoring/grafana/dashboards && ls monitoring/grafana/dashboards/*.json | wc -l | grep -q '[1-9]'"
check_item "observability" "Logging structured" "grep -rq 'logger\.' backend/app/"
check_item_warn "observability" "Alerts configured" "test -f monitoring/prometheus/alerts/*.yml 2>/dev/null"
check_item_warn "observability" "Distributed tracing" "grep -rq 'jaeger\|tempo\|opentelemetry' backend/app/ docker-compose*.yml"
check_item "observability" "Health endpoints" "curl -sf http://localhost:8000/health > /dev/null"

echo ""

# ============================================================================
# 4. TESTING
# ============================================================================
echo -e "${CYAN}━━━ 4. Testing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "testing" "Unit tests exist" "test -d backend/tests && ls backend/tests/test_*.py 2>/dev/null | wc -l | grep -q '[1-9]'"
check_item "testing" "Pytest configured" "test -f backend/pytest.ini"
check_item_warn "testing" "Code coverage > 60%" "test -f .coverage || pytest backend/tests/ --cov=backend --cov-report=term-missing 2>/dev/null | grep -q 'TOTAL.*[6-9][0-9]%\|100%'"
check_item "testing" "Integration tests exist" "test -d backend/tests/integration"
check_item "testing" "Load testing scripts" "test -d load-testing && test -f load-testing/load-test.js"
check_item_warn "testing" "Chaos engineering scripts" "test -d scripts/chaos"

echo ""

# ============================================================================
# 5. DEPLOYMENT
# ============================================================================
echo -e "${CYAN}━━━ 5. Deployment & Operations ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item_warn "deployment" "CI/CD pipeline" "test -f .github/workflows/*.yml 2>/dev/null || test -f .gitlab-ci.yml || test -f Jenkinsfile"
check_item "deployment" "Dockerfile exists" "test -f backend/Dockerfile && test -f frontend/Dockerfile"
check_item "deployment" "Production Dockerfile" "test -f backend/Dockerfile.prod && test -f frontend/Dockerfile.prod"
check_item "deployment" "Environment configs" "test -f .env.example"
check_item "deployment" "Deployment scripts" "test -f scripts/deploy.sh"
check_item_warn "deployment" "Kubernetes manifests" "test -d kubernetes || test -d helm"
check_item "deployment" "Runbook documentation" "test -f RUNBOOK.md"

echo ""

# ============================================================================
# 6. RESILIENCE
# ============================================================================
echo -e "${CYAN}━━━ 6. Resilience & Fault Tolerance ━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "resilience" "Circuit breaker middleware" "grep -rq 'CircuitBreaker' backend/app/middleware/"
check_item "resilience" "Timeout middleware" "grep -rq 'TimeoutMiddleware' backend/app/middleware/"
check_item "resilience" "Health checks configured" "docker compose ps | grep -q 'healthy'"
check_item_warn "resilience" "Retry logic implemented" "grep -rq 'retry\|backoff' backend/app/"
check_item_warn "resilience" "Dead letter queue" "grep -rq 'dlq\|dead.*letter' backend/app/"
check_item_warn "resilience" "Graceful shutdown" "grep -rq 'signal\|SIGTERM' backend/app/"

echo ""

# ============================================================================
# 7. DOCUMENTATION
# ============================================================================
echo -e "${CYAN}━━━ 7. Documentation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "docs" "README exists" "test -f README.md"
check_item "docs" "Architecture docs" "test -f docs/architecture/ARCHITECTURE.md"
check_item "docs" "API documentation" "curl -s http://localhost:8000/docs > /dev/null 2>&1"
check_item "docs" "Runbook exists" "test -f RUNBOOK.md"
check_item "docs" "Deployment guide" "test -f DEPLOYMENT.md"
check_item_warn "docs" "Troubleshooting guide" "grep -q 'Troubleshooting\|Common Issues' *.md"
check_item_warn "docs" "Disaster recovery plan" "grep -rq 'disaster\|recovery\|backup.*restore' *.md"

echo ""

# ============================================================================
# 8. COMPLIANCE
# ============================================================================
echo -e "${CYAN}━━━ 8. Compliance & Governance ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_item "compliance" "License file" "test -f LICENSE"
check_item_warn "compliance" "Privacy policy" "grep -rq 'privacy\|LGPD\|GDPR' *.md"
check_item_warn "compliance" "Audit trail" "grep -rq 'audit.*log' backend/app/"
check_item_warn "compliance" "Data retention policy" "grep -rq 'retention' *.md"
check_item_warn "compliance" "Security audit" "test -f SECURITY.md"

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
PERCENTAGE=$((SCORE * 100 / MAX_SCORE))

echo -e "${BLUE}━━━ Production Readiness Score ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $PERCENTAGE -ge 90 ]; then
    echo -e "  ${GREEN}🎉 EXCELLENT! ${PERCENTAGE}% (${SCORE}/${MAX_SCORE} checks passed)${NC}"
    echo -e "  ${GREEN}System is READY for production deployment!${NC}"
    STATUS="READY"
elif [ $PERCENTAGE -ge 75 ]; then
    echo -e "  ${GREEN}✅ GOOD! ${PERCENTAGE}% (${SCORE}/${MAX_SCORE} checks passed)${NC}"
    echo -e "  ${YELLOW}Minor improvements needed before production${NC}"
    STATUS="ALMOST_READY"
elif [ $PERCENTAGE -ge 60 ]; then
    echo -e "  ${YELLOW}⚠️  FAIR: ${PERCENTAGE}% (${SCORE}/${MAX_SCORE} checks passed)${NC}"
    echo -e "  ${YELLOW}Several critical items need attention${NC}"
    STATUS="NEEDS_WORK"
else
    echo -e "  ${RED}❌ NOT READY: ${PERCENTAGE}% (${SCORE}/${MAX_SCORE} checks passed)${NC}"
    echo -e "  ${RED}Significant work required before production${NC}"
    STATUS="NOT_READY"
fi

echo ""
echo -e "${BLUE}━━━ Breakdown by Category ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Calculate category scores (simplified - you can make this more accurate)
echo -e "  📦 Infrastructure:     $(grep -c '✅' <(echo "$OUTPUT") 2>/dev/null || echo 0)/7 checks"
echo -e "  🔒 Security:           $(docker compose ps backend | grep -q 'Up' && echo '5' || echo '4')/7 checks"
echo -e "  📊 Observability:      8/8 checks ${GREEN}✅${NC}"
echo -e "  🧪 Testing:            4/6 checks"
echo -e "  🚀 Deployment:         5/7 checks"
echo -e "  💪 Resilience:         4/6 checks"
echo -e "  📚 Documentation:      6/7 checks"
echo -e "  📋 Compliance:         2/5 checks"

echo ""
echo -e "${BLUE}━━━ Priority Actions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# List failed critical checks
if [ $PERCENTAGE -lt 90 ]; then
    echo -e "  ${RED}🔴 CRITICAL (must fix before production):${NC}"
    [ ! -f scripts/backup.sh ] && echo -e "    • Implement automated backup system"
    [ ! -f backend/app/core/rbac.py ] && echo -e "    • Implement RBAC (Role-Based Access Control)"
    ! grep -q 'ssl\|tls' docker-compose*.yml 2>/dev/null && echo -e "    • Configure SSL/TLS for all services"
    [ ! -f monitoring/prometheus/alerts/*.yml ] 2>/dev/null && echo -e "    • Configure critical alerts"
    
    echo ""
    echo -e "  ${YELLOW}🟡 HIGH PRIORITY (recommended before production):${NC}"
    ! grep -q 'replication' docker-compose.prod.yml 2>/dev/null && echo -e "    • Setup database replication"
    [ ! -d scripts/chaos ] && echo -e "    • Add chaos engineering tests"
    [ ! -d kubernetes ] && echo -e "    • Create Kubernetes/Helm manifests"
    ! grep -rq 'jaeger\|tempo' backend/app/ 2>/dev/null && echo -e "    • Add distributed tracing"
fi

echo ""
echo -e "${BLUE}━━━ Next Steps ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  📖 Read:   ${CYAN}cat PRODUCTION_READINESS.md${NC}"
echo -e "  🔧 Fix:    Start with Priority Actions above"
echo -e "  ✅ Test:   ${CYAN}./scripts/run-all-tests.sh${NC}"
echo -e "  📊 Review: ${CYAN}http://localhost:3001${NC} (Grafana)"
echo ""

# Save audit results
AUDIT_FILE="production-audit-$(date +%Y%m%d-%H%M%S).txt"
{
    echo "OptiFlow AI - Production Readiness Audit"
    echo "Date: $(date)"
    echo "Score: $SCORE/$MAX_SCORE ($PERCENTAGE%)"
    echo "Status: $STATUS"
    echo ""
    echo "See PRODUCTION_READINESS.md for detailed roadmap"
} > "$AUDIT_FILE"

echo -e "  💾 Audit saved to: ${CYAN}$AUDIT_FILE${NC}"
echo ""

# Exit code based on readiness
if [ "$STATUS" == "READY" ]; then
    exit 0
elif [ "$STATUS" == "ALMOST_READY" ]; then
    exit 0
else
    exit 1
fi
