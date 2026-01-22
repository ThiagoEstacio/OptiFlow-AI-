#!/bin/bash

# Script para configurar nvidia-container-toolkit com o novo Docker Root
# Executar com: sudo bash setup-nvidia-docker.sh

set -e

echo "============================================"
echo "  Configurando NVIDIA Container Toolkit"
echo "============================================"

# Verificar se nvidia-smi funciona
echo "[1/4] Verificando driver NVIDIA..."
if ! nvidia-smi &>/dev/null; then
    echo "ERRO: nvidia-smi não encontrado. Instale os drivers NVIDIA primeiro."
    exit 1
fi
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

# Verificar se nvidia-container-toolkit está instalado
echo "[2/4] Verificando nvidia-container-toolkit..."
if ! command -v nvidia-ctk &>/dev/null; then
    echo "nvidia-container-toolkit não encontrado. Instalando..."

    # Adicionar repositório NVIDIA
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
fi

# Configurar Docker para usar nvidia runtime
echo "[3/4] Configurando Docker daemon..."
sudo nvidia-ctk runtime configure --runtime=docker

# Atualizar daemon.json para manter data-root em /home
echo "[4/4] Preservando configuração de data-root..."
cat /etc/docker/daemon.json

# Reiniciar Docker
echo ""
echo "Reiniciando Docker..."
sudo systemctl restart docker

echo ""
echo "============================================"
echo "  Verificando configuração"
echo "============================================"
docker info | grep -E "Runtimes|Default Runtime"

echo ""
echo "Testando GPU no Docker..."
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi || echo "Teste falhou - verifique a instalação"

echo ""
echo "Concluído!"
