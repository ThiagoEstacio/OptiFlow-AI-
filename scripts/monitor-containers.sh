#!/bin/bash
# OptiFlow AI - Container Health Monitor
# Monitora status de todos os containers do stack

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         OptiFlow AI - Container Health Monitor               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Função para verificar status de um container
check_container() {
    local service=$1
    local status=$(docker compose ps $service --format json 2>/dev/null | jq -r '.State // "not-found"')
    local health=$(docker compose ps $service --format json 2>/dev/null | jq -r '.Health // "none"')
    
    if [ "$status" == "running" ]; then
        if [ "$health" == "healthy" ]; then
            echo -e "  ✅ ${GREEN}$service${NC} - running (healthy)"
        elif [ "$health" == "none" ]; then
            echo -e "  ✅ ${GREEN}$service${NC} - running"
        else
            echo -e "  ⚠️  ${YELLOW}$service${NC} - running ($health)"
        fi
    elif [ "$status" == "not-found" ]; then
        echo -e "  ❓ ${YELLOW}$service${NC} - not configured"
    else
        echo -e "  ❌ ${RED}$service${NC} - $status"
    fi
}

# Core Services
echo -e "${BLUE}━━━ Core Application ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "backend"
check_container "frontend"
check_container "gateway"

# Infrastructure
echo ""
echo -e "${BLUE}━━━ Infrastructure ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "postgres"
check_container "redis"
check_container "influxdb"

# Messaging
echo ""
echo -e "${BLUE}━━━ Messaging ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "kafka"
check_container "zookeeper"
check_container "rabbitmq"
check_container "kafka-ui"

# Background Jobs
echo ""
echo -e "${BLUE}━━━ Background Jobs ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "celery-worker"
check_container "celery-beat"

# Monitoring
echo ""
echo -e "${BLUE}━━━ Monitoring Stack ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "prometheus"
check_container "grafana"
check_container "node-exporter"
check_container "cadvisor"
check_container "postgres-exporter"
check_container "redis-exporter"

# Simulation
echo ""
echo -e "${BLUE}━━━ Simulation & ML ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
check_container "opcua-server"
check_container "mlflow"

# Summary
echo ""
echo -e "${BLUE}━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Count containers
TOTAL=$(docker compose ps --format json 2>/dev/null | jq -s 'length')
RUNNING=$(docker compose ps --format json 2>/dev/null | jq -s '[.[] | select(.State == "running")] | length')
HEALTHY=$(docker compose ps --format json 2>/dev/null | jq -s '[.[] | select(.Health == "healthy")] | length')
UNHEALTHY=$(docker compose ps --format json 2>/dev/null | jq -s '[.[] | select(.Health == "unhealthy" or .Health == "starting")] | length')

echo -e "  Total Containers: ${BLUE}$TOTAL${NC}"
echo -e "  Running: ${GREEN}$RUNNING${NC}"
echo -e "  Healthy: ${GREEN}$HEALTHY${NC}"
if [ "$UNHEALTHY" -gt 0 ]; then
    echo -e "  Unhealthy: ${RED}$UNHEALTHY${NC}"
fi

echo ""
echo -e "${BLUE}━━━ Quick Access URLs ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  🌐 Frontend:       ${GREEN}http://localhost:3000${NC}"
echo -e "  🔧 Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  📊 Grafana:        ${GREEN}http://localhost:3001${NC} (admin/admin)"
echo -e "  🔍 Prometheus:     ${GREEN}http://localhost:9090${NC}"
echo -e "  📬 RabbitMQ:       ${GREEN}http://localhost:15672${NC} (guest/guest)"
echo -e "  📨 Kafka UI:       ${GREEN}http://localhost:8090${NC}"
echo -e "  🧪 MLflow:         ${GREEN}http://localhost:5000${NC}"
echo -e "  🏭 OPC-UA Server:  ${GREEN}opc.tcp://localhost:4840${NC}"

echo ""
echo -e "${BLUE}━━━ Health Check Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Backend:    curl http://localhost:8000/health"
echo -e "  Gateway:    curl http://localhost:8001/health"
echo -e "  Prometheus: curl http://localhost:9090/-/healthy"

echo ""
echo -e "${YELLOW}💡 Tip: Run 'docker compose logs -f [service]' to see logs${NC}"
echo ""
