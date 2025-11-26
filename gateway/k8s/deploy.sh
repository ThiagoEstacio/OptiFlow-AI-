#!/bin/bash
# ============================================================================
# OptiFlow Gateway - Kubernetes Deploy Script
# ============================================================================
#
# Usage:
#   ./deploy.sh [environment]
#
# Environments:
#   dev|development  - Development (minimal resources, no HA)
#   prod|production  - Production (HA, HPA, NetworkPolicy)
#   base             - Base config (default)
#
# Examples:
#   ./deploy.sh                 # Deploy base config
#   ./deploy.sh dev             # Deploy to development
#   ./deploy.sh prod            # Deploy to production
#   ./deploy.sh delete          # Delete deployment
#   ./deploy.sh status          # Check status
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=${1:-base}

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}   OptiFlow Gateway - Kubernetes Deploy    ${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster."
        exit 1
    fi

    print_status "kubectl connected to cluster"
}

build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"

    cd "$SCRIPT_DIR/../.."

    docker build \
        -f gateway/Dockerfile.microservice \
        -t optiflow-gateway:edge \
        .

    print_status "Image built: optiflow-gateway:edge"
}

deploy_base() {
    echo -e "${YELLOW}Deploying base configuration...${NC}"

    kubectl apply -k "$SCRIPT_DIR"

    print_status "Base deployment applied"
}

deploy_development() {
    echo -e "${YELLOW}Deploying to DEVELOPMENT environment...${NC}"

    # Create namespace if not exists
    kubectl create namespace optiflow-gateway-dev --dry-run=client -o yaml | kubectl apply -f -

    kubectl apply -k "$SCRIPT_DIR/overlays/development"

    print_status "Development deployment applied"
}

deploy_production() {
    echo -e "${YELLOW}Deploying to PRODUCTION environment...${NC}"
    print_warning "Make sure secrets are configured!"

    kubectl apply -k "$SCRIPT_DIR/overlays/production"

    print_status "Production deployment applied"
}

delete_deployment() {
    echo -e "${YELLOW}Deleting deployment...${NC}"

    kubectl delete -k "$SCRIPT_DIR" --ignore-not-found
    kubectl delete namespace optiflow-gateway --ignore-not-found
    kubectl delete namespace optiflow-gateway-dev --ignore-not-found

    print_status "Deployment deleted"
}

show_status() {
    echo -e "${YELLOW}Deployment Status:${NC}"
    echo ""

    # Check namespaces
    echo -e "${BLUE}Namespaces:${NC}"
    kubectl get namespace | grep optiflow-gateway || echo "  No namespaces found"
    echo ""

    # Check pods
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods -n optiflow-gateway 2>/dev/null || echo "  No pods in optiflow-gateway"
    kubectl get pods -n optiflow-gateway-dev 2>/dev/null || echo "  No pods in optiflow-gateway-dev"
    echo ""

    # Check services
    echo -e "${BLUE}Services:${NC}"
    kubectl get svc -n optiflow-gateway 2>/dev/null || true
    echo ""

    # Check ingress
    echo -e "${BLUE}Ingress:${NC}"
    kubectl get ingress -n optiflow-gateway 2>/dev/null || true
    echo ""

    # Check HPA
    echo -e "${BLUE}HPA:${NC}"
    kubectl get hpa -n optiflow-gateway 2>/dev/null || true
}

wait_for_ready() {
    echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"

    local namespace="optiflow-gateway"
    if [ "$ENVIRONMENT" == "dev" ] || [ "$ENVIRONMENT" == "development" ]; then
        namespace="optiflow-gateway-dev"
    fi

    kubectl rollout status deployment/gateway -n $namespace --timeout=120s || true

    # Show pod status
    kubectl get pods -n $namespace -l app=optiflow,component=gateway
}

# Main
print_header
check_prerequisites

case "$ENVIRONMENT" in
    build)
        build_image
        ;;
    dev|development)
        deploy_development
        wait_for_ready
        ;;
    prod|production)
        deploy_production
        wait_for_ready
        ;;
    base)
        deploy_base
        wait_for_ready
        ;;
    delete|remove)
        delete_deployment
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${RED}Unknown environment: $ENVIRONMENT${NC}"
        echo ""
        echo "Usage: ./deploy.sh [environment]"
        echo ""
        echo "Environments:"
        echo "  base          - Deploy base configuration (default)"
        echo "  dev           - Deploy to development"
        echo "  prod          - Deploy to production"
        echo "  delete        - Delete deployment"
        echo "  status        - Show deployment status"
        echo "  build         - Build Docker image"
        exit 1
        ;;
esac

echo ""
print_status "Done!"
