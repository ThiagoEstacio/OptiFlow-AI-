#!/bin/bash
#
# SmartPort Automated Deployment Script
# Deploys SmartPort to production environment
#

set -e  # Exit on error

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
PROJECT_NAME="smartport"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# ================================
# Pre-deployment Checks
# ================================
pre_deployment_checks() {
    log_step "Pre-deployment Checks"

    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
        log_error "Please run with sudo or add user to docker group"
        exit 1
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check if .env.prod exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "$ENV_FILE not found!"
        log_info "Copy .env.prod.example to .env.prod and configure it"
        exit 1
    fi

    # Check if docker-compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "$COMPOSE_FILE not found!"
        exit 1
    fi

    log_info "All pre-deployment checks passed!"
}

# ================================
# Backup Current Database
# ================================
backup_before_deploy() {
    log_step "Creating Pre-deployment Backup"

    if [ -f "./scripts/backup.sh" ]; then
        log_info "Running backup script..."
        bash ./scripts/backup.sh || log_warn "Backup failed, but continuing with deployment"
    else
        log_warn "Backup script not found, skipping pre-deployment backup"
    fi
}

# ================================
# Pull Latest Images
# ================================
pull_images() {
    log_step "Pulling Latest Docker Images"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull || {
        log_error "Failed to pull images"
        exit 1
    }

    log_info "Images pulled successfully!"
}

# ================================
# Build Custom Images
# ================================
build_images() {
    log_step "Building Custom Docker Images"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache || {
        log_error "Failed to build images"
        exit 1
    }

    log_info "Images built successfully!"
}

# ================================
# Run Database Migrations
# ================================
run_migrations() {
    log_step "Running Database Migrations"

    # Check if backend container is running
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps backend | grep -q "Up"; then
        log_info "Running Alembic migrations..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend alembic upgrade head || {
            log_error "Migration failed"
            exit 1
        }
        log_info "Migrations completed successfully!"
    else
        log_warn "Backend container not running, skipping migrations"
    fi
}

# ================================
# Deploy Services
# ================================
deploy_services() {
    log_step "Deploying Services"

    # Stop old containers (graceful shutdown)
    log_info "Stopping old containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" down || true

    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d || {
        log_error "Failed to start containers"
        exit 1
    }

    log_info "Services deployed successfully!"
}

# ================================
# Health Checks
# ================================
health_checks() {
    log_step "Running Health Checks"

    # Wait for services to start
    log_info "Waiting for services to become healthy..."
    sleep 10

    # Check backend health
    log_info "Checking backend health..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec backend curl -f http://localhost:8000/health 2>/dev/null; then
            log_info "Backend is healthy!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Backend health check failed after 30 attempts"
            return 1
        fi
        sleep 2
    done

    # Check database connectivity
    log_info "Checking database connectivity..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec postgres pg_isready || {
        log_error "PostgreSQL is not ready"
        return 1
    }

    # Check InfluxDB
    log_info "Checking InfluxDB..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec influxdb influx ping || {
        log_error "InfluxDB is not ready"
        return 1
    }

    log_info "All health checks passed!"
    return 0
}

# ================================
# Show Service Status
# ================================
show_status() {
    log_step "Service Status"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" ps

    echo ""
    log_info "Logs are available with: docker-compose -f $COMPOSE_FILE logs -f [service]"
    log_info "Stop services with: docker-compose -f $COMPOSE_FILE down"
}

# ================================
# Rollback Function
# ================================
rollback() {
    log_error "Deployment failed! Rolling back..."

    # Stop new containers
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" down

    # Restore from backup if needed
    log_warn "To restore from backup, run: ./scripts/restore.sh --latest"

    exit 1
}

# ================================
# Main Deployment Flow
# ================================
main() {
    log_info "Starting SmartPort Production Deployment"
    log_info "Deployment started at: $(date)"

    # Set trap for errors
    trap rollback ERR

    # Run deployment steps
    pre_deployment_checks
    backup_before_deploy
    pull_images
    build_images
    deploy_services

    # Wait a bit for services to stabilize
    sleep 15

    # Run migrations
    run_migrations

    # Health checks
    if ! health_checks; then
        log_error "Health checks failed!"
        rollback
    fi

    # Show status
    show_status

    log_info "Deployment completed successfully at: $(date)"
    log_info "Application is now running!"
    echo ""
    log_info "Access the application at: https://yourdomain.com"
    log_info "API documentation at: https://api.yourdomain.com/docs"
}

# ================================
# Command Line Options
# ================================
case "${1:-deploy}" in
    deploy)
        main
        ;;
    pull)
        pull_images
        ;;
    build)
        build_images
        ;;
    migrate)
        run_migrations
        ;;
    health)
        health_checks
        ;;
    status)
        show_status
        ;;
    rollback)
        rollback
        ;;
    *)
        echo "Usage: $0 {deploy|pull|build|migrate|health|status|rollback}"
        exit 1
        ;;
esac
