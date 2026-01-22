#!/bin/bash

# Script para mover o Docker para /home onde há mais espaço
# Executar com: sudo bash move-docker-to-home.sh

set -e

echo "============================================"
echo "  Movendo Docker para /home/docker-data"
echo "============================================"
echo ""

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, execute como root: sudo bash $0"
  exit 1
fi

# Mostrar espaço atual
echo "Espaço atual:"
df -h / /home
echo ""

# 1. Parar o Docker
echo "[1/6] Parando Docker..."
systemctl stop docker docker.socket containerd 2>/dev/null || true
sleep 2

# 2. Criar diretório destino
echo "[2/6] Criando /home/docker-data..."
mkdir -p /home/docker-data

# 3. Copiar dados (rsync preserva permissões)
echo "[3/6] Copiando dados do Docker (pode demorar alguns minutos)..."
if [ -d "/var/lib/docker" ]; then
  rsync -aP /var/lib/docker/ /home/docker-data/
fi

# 4. Configurar Docker para usar novo diretório
echo "[4/6] Configurando Docker..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "data-root": "/home/docker-data"
}
EOF

# 5. Remover diretório antigo para liberar espaço
echo "[5/6] Removendo dados antigos de /var/lib/docker..."
rm -rf /var/lib/docker

# 6. Reiniciar Docker
echo "[6/6] Reiniciando Docker..."
systemctl start docker

# Verificar
echo ""
echo "============================================"
echo "  Verificando configuração"
echo "============================================"
docker info 2>/dev/null | grep -E "Docker Root Dir|Storage Driver" || echo "Docker iniciando..."
echo ""
echo "Espaço após migração:"
df -h / /home
echo ""
echo "Concluído! Docker agora usa /home/docker-data"
echo ""
