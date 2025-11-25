#!/bin/bash
# ============================================================================
# Setup Complete Monitoring Stack
# ============================================================================
#
# Deploys full observability stack:
# - Prometheus (metrics collection)
# - Grafana (dashboards)
# - Loki (log aggregation)
# - Promtail (log collection)
# - AlertManager (alerting)
#
# Prerequisites:
#   - Kubernetes cluster (Minikube, K3s, or cloud)
#   - kubectl configured
#   - ~95Gi storage available
# ============================================================================

set -e

echo "📊 Setting up OptiFlow Monitoring Stack..."
echo ""

# === CONFIGURATION ===
NAMESPACE="monitoring"
MONITORING_DIR="../../infrastructure/kubernetes/monitoring"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# === FUNCTIONS ===
print_step() {
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

wait_for_pods() {
    local namespace=$1
    local app=$2
    local timeout=${3:-300}

    echo "⏳ Waiting for $app pods to be ready..."
    if kubectl wait --for=condition=ready pod \
        -l app=$app \
        -n $namespace \
        --timeout=${timeout}s 2>/dev/null; then
        print_success "$app is ready"
    else
        print_warning "$app is taking longer than expected, but continuing..."
    fi
}

# === 0. PRE-FLIGHT CHECKS ===
print_step "0️⃣  Pre-flight checks"

# Check kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install kubectl first."
    exit 1
fi
print_success "kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    exit 1
fi
print_success "Connected to Kubernetes cluster"

# Get cluster info
CLUSTER_NAME=$(kubectl config current-context)
echo "📍 Cluster: $CLUSTER_NAME"
echo ""

# Check if monitoring directory exists
if [ ! -d "$MONITORING_DIR" ]; then
    print_error "Monitoring manifests not found at $MONITORING_DIR"
    exit 1
fi
print_success "Monitoring manifests found"

echo ""

# === 1. CREATE NAMESPACE ===
print_step "1️⃣  Creating namespace"

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
print_success "Namespace '$NAMESPACE' ready"

echo ""

# === 2. DEPLOY PROMETHEUS ===
print_step "2️⃣  Deploying Prometheus (metrics collection)"

echo "📦 Applying Prometheus manifests..."
kubectl apply -f $MONITORING_DIR/prometheus/prometheus.yaml

echo "📋 Applying alert rules..."
kubectl apply -f $MONITORING_DIR/prometheus/rules/optiflow-alerts.yaml

wait_for_pods $NAMESPACE prometheus 180

echo ""

# === 3. DEPLOY LOKI ===
print_step "3️⃣  Deploying Loki (log aggregation)"

echo "📦 Applying Loki manifests..."
kubectl apply -f $MONITORING_DIR/loki/loki.yaml

wait_for_pods $NAMESPACE loki 180

echo "📦 Deploying Promtail (log collector)..."
kubectl rollout status daemonset/promtail -n $NAMESPACE --timeout=120s || print_warning "Promtail still deploying..."

print_success "Loki stack deployed"

echo ""

# === 4. DEPLOY GRAFANA ===
print_step "4️⃣  Deploying Grafana (dashboards)"

echo "📦 Applying Grafana manifests..."
kubectl apply -f $MONITORING_DIR/grafana/grafana.yaml

echo "📊 Loading pre-configured dashboards..."
kubectl apply -f $MONITORING_DIR/grafana/grafana-dashboards.yaml

wait_for_pods $NAMESPACE grafana 180

echo ""

# === 5. DEPLOY ALERTMANAGER ===
print_step "5️⃣  Deploying AlertManager (alerting)"

echo "📦 Applying AlertManager manifests..."
kubectl apply -f $MONITORING_DIR/alertmanager/alertmanager.yaml

wait_for_pods $NAMESPACE alertmanager 120

echo ""

# === 6. VERIFY DEPLOYMENT ===
print_step "6️⃣  Verifying deployment"

echo "📊 Monitoring Stack Status:"
kubectl get pods -n $NAMESPACE

echo ""
echo "💾 Persistent Volume Claims:"
kubectl get pvc -n $NAMESPACE

echo ""
echo "🌐 Services:"
kubectl get svc -n $NAMESPACE

echo ""

# Check if all pods are running
PODS_READY=$(kubectl get pods -n $NAMESPACE --no-headers | grep -c "Running" || echo 0)
PODS_TOTAL=$(kubectl get pods -n $NAMESPACE --no-headers | wc -l)

if [ "$PODS_READY" -eq "$PODS_TOTAL" ]; then
    print_success "All pods are running ($PODS_READY/$PODS_TOTAL)"
else
    print_warning "Some pods are not ready yet ($PODS_READY/$PODS_TOTAL)"
    echo ""
    echo "Check status with: kubectl get pods -n $NAMESPACE"
fi

echo ""

# === 7. CONFIGURATION REMINDERS ===
print_step "7️⃣  Configuration reminders"

print_warning "DEFAULT CREDENTIALS IN USE!"
echo ""
echo "🔐 Please change these default passwords in production:"
echo ""
echo "  Grafana:"
echo "    Username: admin"
echo "    Password: optiflow123"
echo ""
echo "  Change with:"
echo "    kubectl create secret generic grafana-secrets \\"
echo "      --from-literal=admin-password='YOUR_PASSWORD' \\"
echo "      -n monitoring --dry-run=client -o yaml | kubectl apply -f -"
echo "    kubectl rollout restart deployment/grafana -n monitoring"
echo ""

print_warning "CONFIGURE ALERT NOTIFICATIONS!"
echo ""
echo "📧 Edit alertmanager-secrets to configure:"
echo "  - SMTP (email alerts)"
echo "  - Slack webhooks"
echo "  - PagerDuty keys"
echo ""
echo "  Edit: infrastructure/kubernetes/monitoring/alertmanager/alertmanager.yaml"
echo "  Then: kubectl apply -f infrastructure/kubernetes/monitoring/alertmanager/alertmanager.yaml"
echo ""

# === 8. ACCESS INSTRUCTIONS ===
print_step "8️⃣  Access services"

echo "You can access the monitoring services using:"
echo ""

echo "${GREEN}Option A: Port-forward (Quick access)${NC}"
echo ""
echo "  # Grafana (main dashboard UI)"
echo "  kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
echo "  ${BLUE}→ http://localhost:3000${NC} (admin / optiflow123)"
echo ""
echo "  # Prometheus (metrics explorer)"
echo "  kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
echo "  ${BLUE}→ http://localhost:9090${NC}"
echo ""
echo "  # AlertManager (alert management)"
echo "  kubectl port-forward -n $NAMESPACE svc/alertmanager 9093:9093"
echo "  ${BLUE}→ http://localhost:9093${NC}"
echo ""

echo "${GREEN}Option B: Ingress (Production)${NC}"
echo ""

# Check if Ingress controller is installed
if kubectl get ingressclass nginx &> /dev/null; then
    print_success "NGINX Ingress controller detected"
    echo ""
    echo "  Add to /etc/hosts:"
    echo "    127.0.0.1 grafana.optiflow.local"
    echo "    127.0.0.1 prometheus.optiflow.local"
    echo "    127.0.0.1 alertmanager.optiflow.local"
    echo ""
    echo "  Access via:"
    echo "    ${BLUE}http://grafana.optiflow.local${NC}"
    echo "    ${BLUE}http://prometheus.optiflow.local${NC}"
    echo "    ${BLUE}http://alertmanager.optiflow.local${NC}"
else
    print_warning "NGINX Ingress controller not found"
    echo ""
    echo "  Install with:"
    echo "    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.4/deploy/static/provider/cloud/deploy.yaml"
fi

echo ""

# === 9. NEXT STEPS ===
print_step "9️⃣  Next steps"

echo "1. Access Grafana and explore pre-configured dashboards:"
echo "   - Platform Overview"
echo "   - Gateway Metrics"
echo "   - Backend Metrics"
echo "   - Kubernetes Cluster"
echo ""

echo "2. Deploy OptiFlow services with Prometheus annotations:"
echo "   metadata:"
echo "     annotations:"
echo "       prometheus.io/scrape: \"true\""
echo "       prometheus.io/port: \"8000\""
echo "       prometheus.io/path: \"/metrics\""
echo ""

echo "3. Configure alert notifications in AlertManager"
echo "   (Slack, PagerDuty, email)"
echo ""

echo "4. Review monitoring documentation:"
echo "   ${BLUE}infrastructure/kubernetes/monitoring/README.md${NC}"
echo ""

# === 10. QUICK HEALTH CHECK ===
print_step "🏥 Quick health check"

echo "Running health checks..."
echo ""

# Check Prometheus
if kubectl get pods -n $NAMESPACE -l app=prometheus --no-headers 2>/dev/null | grep -q "Running"; then
    print_success "Prometheus: Running"
else
    print_error "Prometheus: Not running"
fi

# Check Grafana
if kubectl get pods -n $NAMESPACE -l app=grafana --no-headers 2>/dev/null | grep -q "Running"; then
    print_success "Grafana: Running"
else
    print_error "Grafana: Not running"
fi

# Check Loki
if kubectl get pods -n $NAMESPACE -l app=loki --no-headers 2>/dev/null | grep -q "Running"; then
    print_success "Loki: Running"
else
    print_error "Loki: Not running"
fi

# Check AlertManager
if kubectl get pods -n $NAMESPACE -l app=alertmanager --no-headers 2>/dev/null | grep -q "Running"; then
    print_success "AlertManager: Running"
else
    print_error "AlertManager: Not running"
fi

# Check Promtail (DaemonSet)
PROMTAIL_DESIRED=$(kubectl get daemonset promtail -n $NAMESPACE -o jsonpath='{.status.desiredNumberScheduled}' 2>/dev/null || echo 0)
PROMTAIL_READY=$(kubectl get daemonset promtail -n $NAMESPACE -o jsonpath='{.status.numberReady}' 2>/dev/null || echo 0)

if [ "$PROMTAIL_DESIRED" -eq "$PROMTAIL_READY" ] && [ "$PROMTAIL_READY" -gt 0 ]; then
    print_success "Promtail: $PROMTAIL_READY/$PROMTAIL_DESIRED nodes"
else
    print_warning "Promtail: $PROMTAIL_READY/$PROMTAIL_DESIRED nodes (may still be starting)"
fi

echo ""

# === COMPLETION ===
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Monitoring stack deployment complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "🚀 Quick start:"
echo ""
echo "  # Access Grafana"
echo "  kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
echo "  # Open http://localhost:3000 (admin / optiflow123)"
echo ""

echo "📚 Documentation:"
echo "  $MONITORING_DIR/README.md"
echo ""

echo "🔧 Useful commands:"
echo "  kubectl get pods -n $NAMESPACE              # List all monitoring pods"
echo "  kubectl logs -n $NAMESPACE -l app=prometheus # View Prometheus logs"
echo "  kubectl get pvc -n $NAMESPACE                # Check storage usage"
echo ""

echo "🗑️  Uninstall:"
echo "  kubectl delete namespace $NAMESPACE"
echo ""
