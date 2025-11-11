#!/bin/bash
# OptiFlow AI - Complete ML/AI Monitoring Verification

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OptiFlow AI - ML/AI Monitoring Verification             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Check metrics availability
echo -e "${CYAN}━━━ 1. Backend Metrics Availability ━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
METRICS=$(curl -s http://localhost:8000/metrics | grep -E "^optiflow_(ollama|agent|mlflow|ml_)" | wc -l)
echo -e "  📊 ML/AI Metrics exposed: ${CYAN}$METRICS${NC} metrics"

if [ "$METRICS" -gt 10 ]; then
    echo -e "  ✅ ${GREEN}All ML/AI metrics are being exposed${NC}"
else
    echo -e "  ⚠️  ${YELLOW}Expected more metrics${NC}"
fi

# 2. Check Prometheus scraping
echo ""
echo -e "${CYAN}━━━ 2. Prometheus Scraping ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Ollama health metric
OLLAMA_HEALTH=$(curl -s "http://localhost:9090/api/v1/query?query=optiflow_ollama_health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else '0')" 2>/dev/null || echo "0")
if [ "$OLLAMA_HEALTH" == "1" ]; then
    echo -e "  ✅ ${GREEN}Ollama Health: Healthy${NC}"
else
    echo -e "  ❌ ${RED}Ollama Health: Unhealthy${NC}"
fi

# Check Agent status metric
AGENT_STATUS=$(curl -s "http://localhost:9090/api/v1/query?query=optiflow_agent_status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else '0')" 2>/dev/null || echo "0")
if [ "$AGENT_STATUS" == "1" ]; then
    echo -e "  ✅ ${GREEN}Agent Status: Healthy${NC}"
else
    echo -e "  ❌ ${RED}Agent Status: Unhealthy${NC}"
fi

# Check insights counter
INSIGHTS=$(curl -s "http://localhost:9090/api/v1/query?query=optiflow_agent_insights_total" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else '0')" 2>/dev/null || echo "0")
echo -e "  💡 ${CYAN}Total Insights Generated: $INSIGHTS${NC}"

# 3. Check Prometheus targets
echo ""
echo -e "${CYAN}━━━ 3. Prometheus Targets Status ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
curl -s "http://localhost:9090/api/v1/targets" | python3 -c "
import sys, json
data = json.load(sys.stdin)
targets = data['data']['activeTargets']
up_count = sum(1 for t in targets if t['health'] == 'up')
total = len(targets)
print(f'  📡 Total Targets: {total}')
print(f'  ✅ UP: {up_count}')
print(f'  ❌ DOWN: {total - up_count}')
print('')
for t in targets:
    job = t['labels']['job']
    health = t['health']
    if health == 'up':
        print(f'    ✅ {job}')
    elif health == 'down':
        print(f'    ❌ {job}')
    else:
        print(f'    ⏳ {job} (unknown)')
"

# 4. Check Grafana dashboards
echo ""
echo -e "${CYAN}━━━ 4. Grafana Dashboards ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
DASHBOARDS=$(curl -s -u admin:admin "http://localhost:3001/api/search?type=dash-db" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "0")
echo -e "  📊 Total Dashboards: ${CYAN}$DASHBOARDS${NC}"

ML_DASHBOARD=$(curl -s -u admin:admin "http://localhost:3001/api/search?query=ML" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "0")
if [ "$ML_DASHBOARD" -gt 0 ]; then
    echo -e "  ✅ ${GREEN}ML/AI Dashboard found${NC}"
    curl -s -u admin:admin "http://localhost:3001/api/search?query=ML" | python3 -c "
import sys, json
dashboards = json.load(sys.stdin)
for d in dashboards:
    print(f'    - {d[\"title\"]} (uid: {d[\"uid\"]})')
"
else
    echo -e "  ⚠️  ${YELLOW}ML/AI Dashboard not found${NC}"
fi

# 5. Test Grafana query
echo ""
echo -e "${CYAN}━━━ 5. Grafana → Prometheus Query Test ━━━━━━━━━━━━━━━━━━━${NC}"
GRAFANA_QUERY=$(curl -s -u admin:admin "http://localhost:3001/api/datasources/proxy/uid/PBFA97CFB590B2093/api/v1/query?query=optiflow_ollama_health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "error")
if [ "$GRAFANA_QUERY" == "success" ]; then
    echo -e "  ✅ ${GREEN}Grafana can query Prometheus successfully${NC}"
    HEALTH_VALUE=$(curl -s -u admin:admin "http://localhost:3001/api/datasources/proxy/uid/PBFA97CFB590B2093/api/v1/query?query=optiflow_ollama_health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else 'No data')" 2>/dev/null)
    echo -e "    📊 Ollama Health Query Result: ${CYAN}$HEALTH_VALUE${NC}"
else
    echo -e "  ❌ ${RED}Grafana query failed${NC}"
fi

# 6. Container status
echo ""
echo -e "${CYAN}━━━ 6. ML/AI Containers Status ━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
docker compose ps ollama backend mlflow prometheus grafana --format "table" 2>&1 | grep -v "WARN\|obsolete" || true

# 7. Summary
echo ""
echo -e "${BLUE}━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SUCCESS_COUNT=0
TOTAL_CHECKS=6

[ "$METRICS" -gt 10 ] && ((SUCCESS_COUNT++))
[ "$OLLAMA_HEALTH" == "1" ] && ((SUCCESS_COUNT++))
[ "$AGENT_STATUS" == "1" ] && ((SUCCESS_COUNT++))
[ "$DASHBOARDS" -gt 0 ] && ((SUCCESS_COUNT++))
[ "$GRAFANA_QUERY" == "success" ] && ((SUCCESS_COUNT++))
[ "$(docker compose ps ollama --format '{{.Status}}' | grep -c 'Up')" -gt 0 ] && ((SUCCESS_COUNT++))

PERCENTAGE=$((SUCCESS_COUNT * 100 / TOTAL_CHECKS))

if [ $PERCENTAGE -ge 80 ]; then
    echo -e "  ${GREEN}✅ Monitoring Health: ${PERCENTAGE}% (${SUCCESS_COUNT}/${TOTAL_CHECKS} checks passed)${NC}"
    echo -e "  ${GREEN}🎉 ML/AI monitoring is operational!${NC}"
elif [ $PERCENTAGE -ge 50 ]; then
    echo -e "  ${YELLOW}⚠️  Monitoring Health: ${PERCENTAGE}% (${SUCCESS_COUNT}/${TOTAL_CHECKS} checks passed)${NC}"
    echo -e "  ${YELLOW}Some components need attention${NC}"
else
    echo -e "  ${RED}❌ Monitoring Health: ${PERCENTAGE}% (${SUCCESS_COUNT}/${TOTAL_CHECKS} checks passed)${NC}"
    echo -e "  ${RED}Critical issues detected${NC}"
fi

# 8. Quick Access
echo ""
echo -e "${BLUE}━━━ Quick Access ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  📊 Grafana ML Dashboard:  ${CYAN}http://localhost:3001/d/ml-agent-dashboard${NC}"
echo -e "  📈 Prometheus Targets:     ${CYAN}http://localhost:9090/targets${NC}"
echo -e "  🧪 MLflow UI:              ${CYAN}http://localhost:5000${NC}"
echo -e "  🤖 Agent Health:           ${CYAN}curl http://localhost:8000/api/v1/agent/health${NC}"
echo -e "  📊 Backend Metrics:        ${CYAN}curl http://localhost:8000/metrics | grep optiflow_${NC}"
echo ""
