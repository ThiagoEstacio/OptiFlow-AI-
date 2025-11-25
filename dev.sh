#!/bin/bash
# ============================================================================
# OptiFlow - Script de Desenvolvimento
# ============================================================================
#
# Facilita operações comuns durante desenvolvimento
#
# Uso: ./dev.sh {comando} [opções]
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funções helper
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Comandos
case "$1" in
    # ========================================
    # START - Iniciar OptiFlow
    # ========================================
    start)
        print_header "🚀 Iniciando OptiFlow"

        echo "Subindo serviços..."
        docker-compose up -d

        echo ""
        print_success "OptiFlow iniciado com sucesso!"
        echo ""
        print_info "Aguardando serviços ficarem prontos (pode levar 30-60s)..."
        echo ""

        # Aguardar alguns segundos
        sleep 5

        # Mostrar status
        docker-compose ps

        echo ""
        print_header "📊 Acesso aos Serviços"
        echo ""
        echo -e "  ${GREEN}Frontend:${NC}     http://localhost:3000"
        echo -e "  ${GREEN}Backend API:${NC}  http://localhost:8000/docs"
        echo -e "  ${GREEN}Grafana:${NC}      http://localhost:3001 (admin/admin)"
        echo -e "  ${GREEN}Prometheus:${NC}   http://localhost:9090"
        echo -e "  ${GREEN}Kafka UI:${NC}     http://localhost:8090"
        echo -e "  ${GREEN}MLflow:${NC}       http://localhost:5000"
        echo -e "  ${GREEN}RabbitMQ:${NC}     http://localhost:15672 (optiflow/optiflow_password)"
        echo ""
        print_info "Use './dev.sh logs' para ver logs em tempo real"
        ;;

    # ========================================
    # STOP - Parar OptiFlow
    # ========================================
    stop)
        print_header "🛑 Parando OptiFlow"

        docker-compose stop

        echo ""
        print_success "OptiFlow parado com sucesso!"
        print_info "Dados foram preservados. Use './dev.sh start' para reiniciar"
        ;;

    # ========================================
    # RESTART - Reiniciar serviços
    # ========================================
    restart)
        print_header "🔄 Reiniciando OptiFlow"

        if [ -z "$2" ]; then
            # Restart ALL
            echo "Reiniciando todos os serviços..."
            docker-compose restart
            print_success "Todos os serviços reiniciados!"
        else
            # Restart específico
            echo "Reiniciando $2..."
            docker-compose restart $2
            print_success "$2 reiniciado!"
        fi
        ;;

    # ========================================
    # LOGS - Ver logs
    # ========================================
    logs)
        SERVICE=${2:-""}

        if [ -z "$SERVICE" ]; then
            print_header "📋 Logs de Todos os Serviços"
            docker-compose logs -f
        else
            print_header "📋 Logs: $SERVICE"
            docker-compose logs -f $SERVICE
        fi
        ;;

    # ========================================
    # STATUS - Ver status dos serviços
    # ========================================
    status|ps)
        print_header "📊 Status dos Serviços"
        docker-compose ps
        ;;

    # ========================================
    # BUILD - Rebuild de serviços
    # ========================================
    build)
        print_header "🔨 Build de Serviços"

        if [ -z "$2" ]; then
            print_warning "Rebuilding TODOS os serviços..."
            docker-compose build
            print_success "Build completo!"
        else
            echo "Rebuilding $2..."
            docker-compose build $2
            print_success "$2 rebuilt!"
        fi

        echo ""
        print_info "Use './dev.sh restart $2' para aplicar mudanças"
        ;;

    # ========================================
    # CLEAN - Limpar tudo
    # ========================================
    clean)
        print_header "🧹 Limpando OptiFlow"

        print_warning "ATENÇÃO: Isso vai remover TODOS os dados!"
        echo ""
        read -p "Tem certeza? (y/N) " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Parando e removendo containers..."
            docker-compose down -v

            echo "Limpando volumes órfãos..."
            docker volume prune -f

            echo "Limpando imagens não usadas..."
            docker image prune -f

            print_success "Limpeza completa!"
            print_info "Use './dev.sh start' para começar do zero"
        else
            print_info "Operação cancelada"
        fi
        ;;

    # ========================================
    # SHELL - Entrar em um container
    # ========================================
    shell)
        if [ -z "$2" ]; then
            print_error "Especifique o serviço: ./dev.sh shell backend"
            exit 1
        fi

        print_header "💻 Shell: $2"
        docker-compose exec $2 bash || docker-compose exec $2 sh
        ;;

    # ========================================
    # DB - Operações de banco de dados
    # ========================================
    db)
        case "$2" in
            migrate)
                print_header "🗄️  Rodando Migrações"
                docker-compose exec backend alembic upgrade head
                print_success "Migrações aplicadas!"
                ;;
            reset)
                print_warning "Resetando banco de dados..."
                docker-compose down -v postgres
                docker-compose up -d postgres
                sleep 5
                docker-compose exec backend alembic upgrade head
                print_success "Banco resetado e migrado!"
                ;;
            psql)
                print_header "🗄️  PostgreSQL CLI"
                docker-compose exec postgres psql -U optiflow
                ;;
            *)
                print_error "Comando inválido. Use: ./dev.sh db {migrate|reset|psql}"
                ;;
        esac
        ;;

    # ========================================
    # TEST - Rodar testes
    # ========================================
    test)
        print_header "🧪 Rodando Testes"

        SERVICE=${2:-backend}

        if [ "$SERVICE" = "backend" ]; then
            docker-compose exec backend python -m pytest -v
        elif [ "$SERVICE" = "gateway" ]; then
            docker-compose exec gateway python -m pytest -v
        else
            print_error "Testes não configurados para $SERVICE"
        fi
        ;;

    # ========================================
    # HEALTH - Verificar saúde dos serviços
    # ========================================
    health)
        print_header "🏥 Health Check"

        echo "Verificando serviços..."
        echo ""

        # Backend
        if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
            print_success "Backend: Healthy"
        else
            print_error "Backend: Unhealthy"
        fi

        # Frontend
        if curl -sf http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend: Healthy"
        else
            print_error "Frontend: Unhealthy"
        fi

        # Grafana
        if curl -sf http://localhost:3001 > /dev/null 2>&1; then
            print_success "Grafana: Healthy"
        else
            print_error "Grafana: Unhealthy"
        fi

        # Prometheus
        if curl -sf http://localhost:9090 > /dev/null 2>&1; then
            print_success "Prometheus: Healthy"
        else
            print_error "Prometheus: Unhealthy"
        fi

        echo ""
        echo "Containers:"
        docker-compose ps
        ;;

    # ========================================
    # STATS - Ver uso de recursos
    # ========================================
    stats)
        print_header "📈 Uso de Recursos"
        docker stats --no-stream $(docker ps --filter name=optiflow -q)
        ;;

    # ========================================
    # BACKUP - Backup de volumes
    # ========================================
    backup)
        print_header "💾 Backup de Dados"

        BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR

        echo "Fazendo backup de volumes..."

        # Backup PostgreSQL
        docker-compose exec -T postgres pg_dump -U optiflow optiflow > $BACKUP_DIR/postgres.sql
        print_success "PostgreSQL backup: $BACKUP_DIR/postgres.sql"

        # Backup volumes
        docker run --rm \
            -v optiflow-ai-_postgres_data:/data \
            -v $(pwd)/$BACKUP_DIR:/backup \
            alpine tar czf /backup/postgres_data.tar.gz /data

        print_success "Backup completo em: $BACKUP_DIR"
        ;;

    # ========================================
    # ONLY-INFRA - Apenas infraestrutura
    # ========================================
    only-infra)
        print_header "🏗️  Subindo Apenas Infraestrutura"

        echo "Subindo databases e message brokers..."
        docker-compose up -d \
            postgres \
            influxdb \
            redis \
            rabbitmq \
            zookeeper \
            kafka-1 \
            kafka-2 \
            kafka-3 \
            vault

        echo ""
        print_success "Infraestrutura iniciada!"
        echo ""
        print_info "Agora você pode rodar backend/frontend localmente:"
        echo ""
        echo "  cd backend"
        echo "  python -m uvicorn app.main:app --reload"
        echo ""
        ;;

    # ========================================
    # PULL - Atualizar imagens
    # ========================================
    pull)
        print_header "⬇️  Atualizando Imagens"
        docker-compose pull
        print_success "Imagens atualizadas!"
        ;;

    # ========================================
    # HELP - Ajuda
    # ========================================
    help|--help|-h)
        cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OptiFlow - Script de Desenvolvimento
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USO: ./dev.sh {comando} [opções]

COMANDOS PRINCIPAIS:
  start              Iniciar OptiFlow completo
  stop               Parar OptiFlow (preserva dados)
  restart [serviço]  Reiniciar todos ou serviço específico
  logs [serviço]     Ver logs em tempo real
  status|ps          Ver status dos serviços

BUILD & DEPLOY:
  build [serviço]    Rebuild de serviços
  pull               Atualizar imagens do Docker Hub
  only-infra         Subir apenas DBs e message brokers

BANCO DE DADOS:
  db migrate         Rodar migrações (Alembic)
  db reset           Resetar banco e rodar migrações
  db psql            Abrir PostgreSQL CLI

DESENVOLVIMENTO:
  shell <serviço>    Abrir shell em um container
  test [serviço]     Rodar testes
  health             Verificar saúde dos serviços
  stats              Ver uso de recursos

MANUTENÇÃO:
  backup             Fazer backup de dados
  clean              Limpar tudo (⚠️ apaga dados!)

EXEMPLOS:
  ./dev.sh start                # Iniciar tudo
  ./dev.sh logs backend         # Ver logs do backend
  ./dev.sh restart gateway      # Reiniciar gateway
  ./dev.sh shell backend        # Entrar no container backend
  ./dev.sh db migrate           # Rodar migrações
  ./dev.sh test backend         # Rodar testes do backend
  ./dev.sh only-infra           # Só infraestrutura (DBs)

ACESSO:
  Frontend:   http://localhost:3000
  Backend:    http://localhost:8000/docs
  Grafana:    http://localhost:3001 (admin/admin)
  Prometheus: http://localhost:9090
  Kafka UI:   http://localhost:8090
  MLflow:     http://localhost:5000

EOF
        ;;

    # ========================================
    # Comando inválido
    # ========================================
    *)
        print_error "Comando inválido: $1"
        echo ""
        echo "Use './dev.sh help' para ver comandos disponíveis"
        exit 1
        ;;
esac
