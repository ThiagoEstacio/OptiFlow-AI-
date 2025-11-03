#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    OptiFlow AI - Sistema Completo                        ║
# ║                Teste de Inicialização e Funcionalidades                  ║
# ║                          100% À Prova de Crash                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# Logging
LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    OptiFlow AI - Teste Completo                          ║${NC}"
echo -e "${CYAN}║                       $(date '+%Y-%m-%d %H:%M:%S')                                 ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${BLUE}[TEST $TOTAL_TESTS] ${test_name}${NC}"
    echo "Command: $test_command"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ PASS: $test_name")
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ FAIL: $test_name")
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name="$1"
    local health_url="$2"
    local max_attempts=30
    local attempt=0

    echo -e "${YELLOW}⏳ Aguardando $service_name...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name está pronto!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo -e "\n${RED}❌ Timeout esperando $service_name${NC}"
    return 1
}

# ════════════════════════════════════════════════════════════════════════════
# FASE 1: Verificação de Pré-requisitos
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                     FASE 1: Pré-requisitos                               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "Docker instalado" "command -v docker"
run_test "Docker rodando" "docker info > /dev/null 2>&1"
run_test "Docker Compose disponível" "docker compose version"
run_test "Arquivo docker-compose.yml existe" "test -f docker-compose.yml"
run_test "Backend existe" "test -d backend"
run_test "Frontend existe" "test -d frontend"
run_test "Gateway existe" "test -d gateway"

# ════════════════════════════════════════════════════════════════════════════
# FASE 2: Limpeza e Preparação
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                   FASE 2: Limpeza e Preparação                           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "${YELLOW}🧹 Parando serviços anteriores...${NC}"
docker compose down --remove-orphans 2>/dev/null || true

echo -e "${YELLOW}🧹 Removendo containers órfãos...${NC}"
docker ps -a -q -f status=exited | xargs -r docker rm 2>/dev/null || true

echo -e "${GREEN}✅ Sistema limpo${NC}"

# ════════════════════════════════════════════════════════════════════════════
# FASE 3: Inicialização de Serviços
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                 FASE 3: Inicialização de Serviços                        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "${BLUE}🚀 Iniciando serviços com Docker Compose...${NC}"
docker compose up -d

echo -e "\n${YELLOW}⏳ Aguardando inicialização (30 segundos)...${NC}"
sleep 30

# ════════════════════════════════════════════════════════════════════════════
# FASE 4: Health Checks dos Serviços Base
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                  FASE 4: Health Checks - Serviços Base                   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "PostgreSQL Health Check" "docker exec optiflow-postgres pg_isready -U optiflow"
run_test "InfluxDB Health Check" "curl -s -f http://localhost:8086/health"
run_test "Redis Health Check" "docker exec optiflow-redis redis-cli -a optiflow_redis_password ping | grep -q PONG"
run_test "RabbitMQ Health Check" "curl -s -u optiflow:optiflow_password http://localhost:15672/api/healthchecks/node"

# ════════════════════════════════════════════════════════════════════════════
# FASE 5: Health Checks - Aplicações
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                 FASE 5: Health Checks - Aplicações                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

wait_for_service "Backend API" "http://localhost:8000/health"
run_test "Backend Health Check" "curl -s -f http://localhost:8000/health | grep -q healthy"
run_test "Backend API Docs" "curl -s -f http://localhost:8000/docs"

wait_for_service "Frontend" "http://localhost:3000"
run_test "Frontend acessível" "curl -s -f http://localhost:3000"

run_test "Gateway em execução" "docker ps | grep -q optiflow-gateway"
run_test "OPC-UA Server em execução" "docker ps | grep -q optiflow-opcua-server"

# ════════════════════════════════════════════════════════════════════════════
# FASE 6: Testes de Banco de Dados
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                   FASE 6: Testes de Banco de Dados                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "PostgreSQL: Conexão" "docker exec optiflow-postgres psql -U optiflow -d optiflow -c 'SELECT 1;'"
run_test "PostgreSQL: Tabelas criadas" "docker exec optiflow-postgres psql -U optiflow -d optiflow -c '\\dt' | grep -q tables"
run_test "InfluxDB: Buckets" "docker exec optiflow-influxdb influx bucket list --token my-super-secret-influxdb-token --org optiflow | grep -q timeseries"

# ════════════════════════════════════════════════════════════════════════════
# FASE 7: Testes de API - Endpoints Básicos
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║               FASE 7: Testes de API - Endpoints Básicos                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "API: Root endpoint" "curl -s -f http://localhost:8000/ | grep -q 'OptiFlow'"
run_test "API: Health endpoint" "curl -s -f http://localhost:8000/health"
run_test "API: API v1 Organizations" "curl -s -f http://localhost:8000/api/v1/organizations"
run_test "API: API v1 Sites" "curl -s -f http://localhost:8000/api/v1/sites"
run_test "API: API v1 Tags" "curl -s -f http://localhost:8000/api/v1/tags"
run_test "API: API v1 Tag Labels" "curl -s -f http://localhost:8000/api/v1/tag-labels"

# ════════════════════════════════════════════════════════════════════════════
# FASE 8: Testes de AI Features
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                   FASE 8: Testes de AI Features                          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "API: AI Insights endpoint" "curl -s -f http://localhost:8000/api/v1/ai"
run_test "API: Chat endpoint" "curl -s -f http://localhost:8000/api/v1/chat"
run_test "API: Analytics endpoint" "curl -s -f http://localhost:8000/api/v1/analytics"
run_test "API: AI Agent endpoint" "curl -s -f http://localhost:8000/api/v1/agent/health"

# ════════════════════════════════════════════════════════════════════════════
# FASE 9: Testes de Simulador e Gateway
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              FASE 9: Testes de Simulador e Gateway                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "Simulador: Container ativo" "docker ps | grep -q optiflow-opcua-server"
run_test "Simulador: Porta 4840 aberta" "nc -zv localhost 4840 2>&1 | grep -q succeeded"
run_test "Gateway: Container ativo" "docker ps | grep -q optiflow-gateway"
run_test "Gateway: Logs sem erros críticos" "! docker logs optiflow-gateway 2>&1 | grep -i 'critical\\|fatal'"

# ════════════════════════════════════════════════════════════════════════════
# FASE 10: Testes de Stress e Estabilidade
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║            FASE 10: Testes de Stress e Estabilidade                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "${YELLOW}🔥 Executando 50 requisições simultâneas...${NC}"
run_test "Stress Test: 50 requisições" "for i in {1..50}; do curl -s -f http://localhost:8000/health & done; wait"

echo -e "${YELLOW}🔄 Testando recuperação após restart...${NC}"
docker restart optiflow-backend
sleep 10
wait_for_service "Backend após restart" "http://localhost:8000/health"
run_test "Recuperação: Backend voltou online" "curl -s -f http://localhost:8000/health"

# ════════════════════════════════════════════════════════════════════════════
# FASE 11: Verificação de Logs
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                   FASE 11: Verificação de Logs                           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

run_test "Backend: Sem erros críticos nos logs" "! docker logs optiflow-backend 2>&1 | grep -i 'error.*critical\\|fatal'"
run_test "Backend: Startup bem-sucedido" "docker logs optiflow-backend 2>&1 | grep -q 'Database initialized'"
run_test "PostgreSQL: Sem erros" "! docker logs optiflow-postgres 2>&1 | grep -i 'error'"
run_test "InfluxDB: Sem erros" "! docker logs optiflow-influxdb 2>&1 | grep -i 'error'"

# ════════════════════════════════════════════════════════════════════════════
# FASE 12: Testes de Crash Recovery
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                 FASE 12: Testes de Crash Recovery                        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "${YELLOW}💥 Simulando crash do backend...${NC}"
docker kill optiflow-backend
sleep 2
run_test "Crash Recovery: Container parado" "! docker ps | grep -q optiflow-backend"

echo -e "${YELLOW}🔄 Reiniciando backend...${NC}"
docker compose up -d backend
sleep 15
wait_for_service "Backend após crash" "http://localhost:8000/health"
run_test "Crash Recovery: Backend recuperado" "curl -s -f http://localhost:8000/health"

# ════════════════════════════════════════════════════════════════════════════
# RELATÓRIO FINAL
# ════════════════════════════════════════════════════════════════════════════

echo -e "\n\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                        RELATÓRIO FINAL                                   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}═══════════════════════ Resumo dos Testes ═══════════════════════${NC}\n"
echo -e "  Total de Testes:    ${CYAN}$TOTAL_TESTS${NC}"
echo -e "  Testes Passados:    ${GREEN}$PASSED_TESTS${NC}"
echo -e "  Testes Falhados:    ${RED}$FAILED_TESTS${NC}"

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "  Taxa de Sucesso:    ${GREEN}${SUCCESS_RATE}%${NC}"

echo -e "\n${BLUE}═══════════════════════ Detalhes dos Testes ═══════════════════════${NC}\n"
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

echo -e "\n${BLUE}═══════════════════════ Status dos Serviços ═══════════════════════${NC}\n"
docker compose ps

echo -e "\n${BLUE}═══════════════════════ URLs de Acesso ═══════════════════════${NC}\n"
echo -e "  ${GREEN}🌐 Frontend:           ${CYAN}http://localhost:3000${NC}"
echo -e "  ${GREEN}🎨 Dashboard Builder:  ${CYAN}http://localhost:3000/dashboard-builder${NC}"
echo -e "  ${GREEN}🤖 AI Insights:        ${CYAN}http://localhost:3000/ai-insights${NC}"
echo -e "  ${GREEN}🔧 Backend API:        ${CYAN}http://localhost:8000${NC}"
echo -e "  ${GREEN}📊 API Docs:           ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  ${GREEN}📈 Grafana:            ${CYAN}http://localhost:3001${NC}"
echo -e "  ${GREEN}🔍 RabbitMQ:           ${CYAN}http://localhost:15672${NC}"

echo -e "\n${BLUE}═══════════════════════ Arquivo de Log ═══════════════════════${NC}\n"
echo -e "  Log salvo em: ${CYAN}$LOG_FILE${NC}"

echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}║              ✅ TODOS OS TESTES PASSARAM - SISTEMA OK!                   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${GREEN}🎉 Sistema 100% funcional e à prova de crash!${NC}\n"
    exit 0
else
    echo -e "${RED}║              ❌ ALGUNS TESTES FALHARAM - REVISAR LOGS                    ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${YELLOW}⚠️  Verifique os logs acima e o arquivo $LOG_FILE${NC}\n"
    exit 1
fi
