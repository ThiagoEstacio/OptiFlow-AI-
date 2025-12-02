#!/bin/bash
# ============================================
# OptiFlow AI Platform - Management Script
# ============================================
#
# Unified management script for development and production environments.
#
# Usage:
#   ./optiflow.sh [command] [options]
#
# Commands:
#   start       Start all services (dev by default)
#   stop        Stop all services
#   restart     Restart all services
#   status      Show container status
#   health      Check service health
#   logs        View logs (./optiflow.sh logs [service] [--follow])
#   build       Build containers
#   rebuild     Force rebuild and start
#   clean       Stop and remove volumes (WARNING: deletes data!)
#   backup      Run backup
#   restore     Restore from backup
#   urls        Show service URLs
#
# Production Commands:
#   prod-start      Start production environment
#   prod-stop       Stop production environment
#   prod-deploy     Full production deployment
#   prod-backup     Run production backup
#
# ============================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Environment (dev or prod)
ENV="${OPTIFLOW_ENV:-dev}"

# Função para exibir banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    OptiFlow AI Platform                   ║"
    echo "║              Industrial IoT & Analytics Suite             ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para exibir uso
show_usage() {
    echo -e "${YELLOW}Uso:${NC} $0 [comando] [opções]"
    echo ""
    echo -e "${YELLOW}Comandos de Desenvolvimento:${NC}"
    echo "  start       Inicia todos os serviços (dev)"
    echo "  stop        Para todos os serviços"
    echo "  restart     Reinicia todos os serviços"
    echo "  status      Exibe status dos containers"
    echo "  health      Verifica saúde dos serviços principais"
    echo "  logs        Exibe logs (use: $0 logs [serviço] [--follow])"
    echo "  build       Constrói os containers"
    echo "  rebuild     Reconstrói e inicia os containers"
    echo "  clean       Para e remove volumes (CUIDADO: apaga dados!)"
    echo ""
    echo -e "${YELLOW}Comandos de Produção:${NC}"
    echo "  prod-start   Inicia ambiente de produção"
    echo "  prod-stop    Para ambiente de produção"
    echo "  prod-deploy  Deploy completo (build + migrate + start)"
    echo "  prod-backup  Executa backup de produção"
    echo "  prod-restore Restaura backup (uso: $0 prod-restore YYYYMMDD)"
    echo ""
    echo -e "${YELLOW}Outros Comandos:${NC}"
    echo "  backup      Executa backup (dev)"
    echo "  urls        Exibe URLs dos serviços"
    echo "  version     Exibe versão"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  $0 start                  # Inicia em modo dev"
    echo "  $0 prod-start             # Inicia em modo prod"
    echo "  $0 logs backend --follow  # Logs do backend"
    echo "  $0 prod-backup            # Backup de produção"
}

# Função para iniciar serviços
start_services() {
    echo -e "${BLUE}[INFO]${NC} Iniciando OptiFlow..."

    # Inicia containers
    docker compose up -d

    echo -e "${BLUE}[INFO]${NC} Aguardando serviços ficarem saudáveis..."

    # Aguarda backend
    echo -n "  Backend: "
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}TIMEOUT${NC}"
        fi
        sleep 2
    done

    # Aguarda frontend
    echo -n "  Frontend: "
    for i in {1..20}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null | grep -q "200"; then
            echo -e "${GREEN}OK${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo -e "${RED}TIMEOUT${NC}"
        fi
        sleep 2
    done

    # Aguarda gateway
    echo -n "  Gateway: "
    for i in {1..15}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            break
        fi
        if [ $i -eq 15 ]; then
            echo -e "${YELLOW}AVISO${NC} (pode estar em modo read-only)"
        fi
        sleep 2
    done

    echo ""
    echo -e "${GREEN}[SUCCESS]${NC} OptiFlow iniciado!"
    echo ""
    show_urls
}

# Função para parar serviços
stop_services() {
    echo -e "${BLUE}[INFO]${NC} Parando OptiFlow..."
    docker compose down
    echo -e "${GREEN}[SUCCESS]${NC} OptiFlow parado!"
}

# Função para reiniciar serviços
restart_services() {
    echo -e "${BLUE}[INFO]${NC} Reiniciando OptiFlow..."
    stop_services
    echo ""
    sleep 3
    start_services
}

# Função para exibir status
show_status() {
    echo -e "${BLUE}[INFO]${NC} Status dos containers:"
    echo ""
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Função para verificar saúde
check_health() {
    echo -e "${BLUE}[INFO]${NC} Verificando saúde dos serviços..."
    echo ""

    # Backend
    echo -n "  Backend (8000):    "
    if curl -s http://localhost:8000/api/health 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi

    # Frontend
    echo -n "  Frontend (3000):   "
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null | grep -q "200"; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi

    # Gateway
    echo -n "  Gateway (8080):    "
    if curl -s http://localhost:8080/health 2>/dev/null | grep -q "status"; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${YELLOW}UNAVAILABLE${NC}"
    fi

    # InfluxDB
    echo -n "  InfluxDB (8086):   "
    if curl -s http://localhost:8086/health 2>/dev/null | grep -q "pass"; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi

    # PostgreSQL
    echo -n "  PostgreSQL (5432): "
    if docker compose exec -T postgres pg_isready -U optiflow > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi

    # Redis
    echo -n "  Redis (6379):      "
    if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi

    # Kafka
    echo -n "  Kafka (9092):      "
    if docker compose exec -T kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${YELLOW}CHECKING...${NC}"
    fi

    # Ollama
    echo -n "  Ollama (11435):    "
    if curl -s http://localhost:11435/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${YELLOW}UNAVAILABLE${NC}"
    fi

    echo ""
}

# Função para exibir URLs
show_urls() {
    echo -e "${YELLOW}URLs dos Serviços:${NC}"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  Gateway:      http://localhost:8080"
    echo "  Grafana:      http://localhost:3001"
    echo "  InfluxDB:     http://localhost:8086"
    echo "  Kafka UI:     http://localhost:8090"
    echo "  MLFlow:       http://localhost:5000"
    echo "  Prometheus:   http://localhost:9090"
    echo "  RabbitMQ:     http://localhost:15672"
    echo "  Vault:        http://localhost:8200"
}

# Função para exibir logs
show_logs() {
    local service=$1
    shift
    local args="$@"

    if [ -z "$service" ]; then
        echo -e "${BLUE}[INFO]${NC} Exibindo logs de todos os serviços (últimas 100 linhas)..."
        docker compose logs --tail=100 $args
    else
        echo -e "${BLUE}[INFO]${NC} Exibindo logs do serviço: $service"
        docker compose logs $service $args
    fi
}

# Função para limpeza completa
clean_all() {
    echo -e "${RED}[AVISO]${NC} Isso irá parar todos os containers e REMOVER TODOS OS DADOS!"
    read -p "Tem certeza? (digite 'sim' para confirmar): " confirm

    if [ "$confirm" = "sim" ]; then
        echo -e "${BLUE}[INFO]${NC} Parando e removendo containers e volumes..."
        docker compose down -v
        echo -e "${GREEN}[SUCCESS]${NC} Limpeza concluída!"
    else
        echo -e "${YELLOW}[INFO]${NC} Operação cancelada."
    fi
}

# Função para rebuild
rebuild_services() {
    echo -e "${BLUE}[INFO]${NC} Reconstruindo containers..."
    docker compose down
    docker compose build --no-cache
    start_services
}

# ========================================
# Production Functions
# ========================================

# Start production environment
prod_start() {
    echo -e "${CYAN}[PROD]${NC} Iniciando ambiente de produção..."

    # Check for .env.prod
    if [ ! -f ".env.prod" ]; then
        echo -e "${RED}[ERROR]${NC} Arquivo .env.prod não encontrado!"
        echo "Copie .env.prod.example para .env.prod e configure as variáveis."
        exit 1
    fi

    # Start with production compose
    docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

    echo -e "${BLUE}[INFO]${NC} Aguardando serviços ficarem saudáveis..."

    # Wait for backend
    echo -n "  Backend: "
    for i in {1..60}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            break
        fi
        if [ $i -eq 60 ]; then
            echo -e "${RED}TIMEOUT${NC}"
        fi
        sleep 2
    done

    echo -e "${GREEN}[PROD]${NC} Ambiente de produção iniciado!"
    show_prod_urls
}

# Stop production
prod_stop() {
    echo -e "${CYAN}[PROD]${NC} Parando ambiente de produção..."
    docker compose -f docker-compose.prod.yml down
    echo -e "${GREEN}[PROD]${NC} Ambiente de produção parado!"
}

# Full production deployment
prod_deploy() {
    echo -e "${CYAN}[PROD]${NC} Iniciando deploy de produção..."

    # Check for .env.prod
    if [ ! -f ".env.prod" ]; then
        echo -e "${RED}[ERROR]${NC} Arquivo .env.prod não encontrado!"
        exit 1
    fi

    # Step 1: Build
    echo -e "${BLUE}[STEP 1/4]${NC} Construindo containers..."
    docker compose -f docker-compose.prod.yml --env-file .env.prod build

    # Step 2: Stop old containers
    echo -e "${BLUE}[STEP 2/4]${NC} Parando containers antigos..."
    docker compose -f docker-compose.prod.yml down

    # Step 3: Start new containers
    echo -e "${BLUE}[STEP 3/4]${NC} Iniciando novos containers..."
    docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

    # Step 4: Run migrations
    echo -e "${BLUE}[STEP 4/4]${NC} Executando migrations..."
    docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || true

    echo -e "${GREEN}[PROD]${NC} Deploy concluído!"
    check_health
}

# Production backup
prod_backup() {
    echo -e "${CYAN}[PROD]${NC} Executando backup de produção..."
    docker compose -f docker-compose.prod.yml --profile backup run --rm backup /backup.sh
    echo -e "${GREEN}[PROD]${NC} Backup concluído!"
}

# Production restore
prod_restore() {
    local restore_date=$1
    if [ -z "$restore_date" ]; then
        echo -e "${RED}[ERROR]${NC} Data de restore necessária. Uso: $0 prod-restore YYYYMMDD"
        exit 1
    fi
    echo -e "${CYAN}[PROD]${NC} Restaurando backup de ${restore_date}..."
    docker compose -f docker-compose.prod.yml --profile backup run --rm backup /backup.sh --restore "$restore_date"
}

# Show production URLs
show_prod_urls() {
    echo -e "${YELLOW}URLs de Produção:${NC}"
    echo "  Frontend:     https://optiflow.example.com (porta 443)"
    echo "  Backend API:  https://optiflow.example.com/api"
    echo "  Grafana:      https://optiflow.example.com/grafana"
    echo ""
    echo -e "${YELLOW}URLs Internas (não expostas):${NC}"
    echo "  Prometheus:   http://prometheus:9090"
    echo "  Alertmanager: http://alertmanager:9093"
}

# Build containers
build_services() {
    echo -e "${BLUE}[INFO]${NC} Construindo containers..."
    docker compose build
    echo -e "${GREEN}[SUCCESS]${NC} Build concluído!"
}

# Run backup (dev)
run_backup() {
    echo -e "${BLUE}[INFO]${NC} Executando backup..."
    docker compose exec -T backup /backup.sh || ./scripts/backup.sh
    echo -e "${GREEN}[SUCCESS]${NC} Backup concluído!"
}

# Show version
show_version() {
    echo -e "${BLUE}OptiFlow AI Platform${NC}"
    echo "Versão: 1.0.0"
    echo "Build: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
}

# Main
show_banner

case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        show_urls
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    build)
        build_services
        ;;
    clean)
        clean_all
        ;;
    rebuild)
        rebuild_services
        ;;
    backup)
        run_backup
        ;;
    urls)
        show_urls
        ;;
    version)
        show_version
        ;;
    # Production commands
    prod-start)
        prod_start
        ;;
    prod-stop)
        prod_stop
        ;;
    prod-deploy)
        prod_deploy
        ;;
    prod-backup)
        prod_backup
        ;;
    prod-restore)
        prod_restore "$2"
        ;;
    prod-urls)
        show_prod_urls
        ;;
    *)
        show_usage
        ;;
esac
