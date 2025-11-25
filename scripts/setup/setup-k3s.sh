#!/bin/bash
# ============================================================================
# Setup K3s - Lightweight Kubernetes
# ============================================================================
#
# Instala K3s para Gateway edge ou dev local
#
# Requisitos:
#   - Linux (Ubuntu/Debian/CentOS)
#   - 512MB RAM disponível
#   - systemd
# ============================================================================

set -e

echo "🪶 Setting up K3s for OptiFlow..."

# === 1. INSTALL K3S ===
echo ""
echo "1️⃣  Installing K3s..."

if command -v k3s &> /dev/null; then
    echo "✅ K3s already installed"
else
    # Install K3s (lightweight, no Traefik, use NGINX instead)
    curl -sfL https://get.k3s.io | sh -s - \
        --write-kubeconfig-mode 644 \
        --disable traefik \
        --disable servicelb

    echo "✅ K3s installed"

    # Wait for K3s to be ready
    echo "⏳ Waiting for K3s to be ready..."
    sleep 10
fi

# === 2. CONFIGURE KUBECTL ===
echo ""
echo "2️⃣  Configuring kubectl..."

# Copy kubeconfig
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config

# Test connection
kubectl cluster-info

echo "✅ kubectl configured"

# === 3. INSTALL NGINX INGRESS ===
echo ""
echo "3️⃣  Installing NGINX Ingress Controller..."

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.4/deploy/static/provider/cloud/deploy.yaml

# Wait for NGINX to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo "✅ NGINX Ingress installed"

# === 4. CREATE NAMESPACES ===
echo ""
echo "4️⃣  Creating OptiFlow namespaces..."

kubectl create namespace optiflow-edge --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces created"

# === 5. DEPLOY MONITORING (OPTIONAL) ===
echo ""
echo "5️⃣  Deploying monitoring stack..."

if [ -d "infrastructure/kubernetes/monitoring" ]; then
    kubectl apply -f infrastructure/kubernetes/monitoring/prometheus/ || true
    kubectl apply -f infrastructure/kubernetes/monitoring/grafana/ || true
    echo "✅ Monitoring deployed"
else
    echo "⚠️  Monitoring manifests not found, skipping..."
fi

# === 6. DEPLOY GATEWAY (EDGE) ===
echo ""
echo "6️⃣  Deploying Gateway service..."

if [ -d "services/gateway/k8s" ]; then
    kubectl apply -f services/gateway/k8s/ -n optiflow-edge

    # Wait for Gateway to be ready
    kubectl wait --for=condition=ready pod \
        -l app=gateway \
        -n optiflow-edge \
        --timeout=120s

    echo "✅ Gateway deployed"
else
    echo "⚠️  Gateway manifests not found, skipping..."
fi

# === 7. EXPOSE SERVICES ===
echo ""
echo "7️⃣  Getting service endpoints..."

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get NodePort for Gateway
GATEWAY_PORT=$(kubectl get svc gateway -n optiflow-edge -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ K3s setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access services:"
echo ""
echo "Gateway API:"
if [ "$GATEWAY_PORT" != "N/A" ]; then
    echo "  http://$NODE_IP:$GATEWAY_PORT"
else
    echo "  Port-forward: kubectl port-forward -n optiflow-edge svc/gateway 8080:8080"
fi
echo ""
echo "Monitoring:"
echo "  Grafana:    kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "  Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo ""
echo "🔧 Useful commands:"
echo "  kubectl get pods -A              # List all pods"
echo "  kubectl get nodes                # List nodes"
echo "  kubectl logs -n optiflow-edge <pod>  # View logs"
echo "  sudo systemctl status k3s        # K3s service status"
echo "  sudo k3s kubectl get all -A      # List everything (as root)"
echo ""
echo "🗑️  Uninstall:"
echo "  /usr/local/bin/k3s-uninstall.sh"
echo ""
