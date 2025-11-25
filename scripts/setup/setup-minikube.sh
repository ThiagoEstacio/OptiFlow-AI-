#!/bin/bash
# ============================================================================
# Setup Minikube - Kubernetes Local
# ============================================================================
#
# Instala e configura Minikube para desenvolvimento local OptiFlow
#
# Requisitos:
#   - 4GB RAM disponível
#   - Docker instalado
#   - 20GB disk space
# ============================================================================

set -e

echo "🎡 Setting up Minikube for OptiFlow..."

# === 1. INSTALL MINIKUBE ===
echo ""
echo "1️⃣  Installing Minikube..."

if ! command -v minikube &> /dev/null; then
    # Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
        sudo install minikube-linux-amd64 /usr/local/bin/minikube
        rm minikube-linux-amd64

    # macOS
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install minikube

    # Windows (WSL)
    else
        echo "❌ Unsupported OS. Install manually: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi

    echo "✅ Minikube installed"
else
    echo "✅ Minikube already installed"
fi

# === 2. START MINIKUBE ===
echo ""
echo "2️⃣  Starting Minikube cluster..."

# Check if already running
if minikube status &> /dev/null; then
    echo "✅ Minikube already running"
else
    # Start with optimal settings for OptiFlow
    minikube start \
        --driver=docker \
        --cpus=4 \
        --memory=8192 \
        --disk-size=40g \
        --kubernetes-version=v1.28.0 \
        --addons=metrics-server,dashboard,ingress

    echo "✅ Minikube cluster started"
fi

# === 3. ENABLE ADDONS ===
echo ""
echo "3️⃣  Enabling useful addons..."

minikube addons enable metrics-server
minikube addons enable dashboard
minikube addons enable ingress
minikube addons enable storage-provisioner

echo "✅ Addons enabled"

# === 4. CONFIGURE KUBECTL ===
echo ""
echo "4️⃣  Configuring kubectl..."

kubectl config use-context minikube
kubectl cluster-info

echo "✅ kubectl configured"

# === 5. CREATE NAMESPACES ===
echo ""
echo "5️⃣  Creating OptiFlow namespaces..."

kubectl create namespace optiflow-dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces created"

# === 6. DEPLOY OPTIFLOW ===
echo ""
echo "6️⃣  Deploying OptiFlow services..."

# Deploy monitoring first
if [ -d "infrastructure/kubernetes/monitoring" ]; then
    kubectl apply -f infrastructure/kubernetes/monitoring/prometheus/
    kubectl apply -f infrastructure/kubernetes/monitoring/grafana/
    echo "✅ Monitoring deployed"
fi

# Deploy services
for service in simulator gateway backend frontend; do
    if [ -d "services/$service/k8s" ]; then
        kubectl apply -f services/$service/k8s/ -n optiflow-dev
        echo "✅ $service deployed"
    fi
done

# === 7. WAIT FOR READY ===
echo ""
echo "7️⃣  Waiting for pods to be ready..."

kubectl wait --for=condition=ready pod \
    --all \
    --timeout=300s \
    -n optiflow-dev

echo "✅ All pods ready"

# === 8. EXPOSE SERVICES ===
echo ""
echo "8️⃣  Exposing services (port-forward)..."

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Minikube setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access services:"
echo ""
echo "Kubernetes Dashboard:"
echo "  minikube dashboard"
echo ""
echo "OptiFlow Services (use port-forward):"
echo "  kubectl port-forward -n optiflow-dev svc/simulator 4850:4850"
echo "  kubectl port-forward -n optiflow-dev svc/gateway 8080:8080"
echo "  kubectl port-forward -n optiflow-dev svc/backend 8000:8000"
echo "  kubectl port-forward -n optiflow-dev svc/frontend 3000:80"
echo ""
echo "Monitoring:"
echo "  kubectl port-forward -n monitoring svc/grafana 3001:3000"
echo "  kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo ""
echo "Minikube IP: $MINIKUBE_IP"
echo ""
echo "🔧 Useful commands:"
echo "  minikube status              # Check cluster status"
echo "  minikube stop                # Stop cluster"
echo "  minikube delete              # Delete cluster"
echo "  kubectl get pods -A          # List all pods"
echo "  kubectl logs -n optiflow-dev <pod-name>  # View logs"
echo ""
