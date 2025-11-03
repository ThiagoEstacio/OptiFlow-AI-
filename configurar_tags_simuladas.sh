#!/bin/bash
# Configurar Tags Simuladas no OptiFlow AI
# Este script cria automaticamente todas as tags industriais no banco de dados

set -e

echo "=============================================================================="
echo "🏭 OptiFlow AI - Configuração Automática de Tags Simuladas"
echo "=============================================================================="
echo ""

# Verificar se o container backend está rodando
if ! docker ps | grep -q optiflow-ai--backend; then
    echo "❌ ERRO: Container 'backend' não está rodando"
    echo ""
    echo "Por favor, inicie o backend primeiro:"
    echo "  docker compose up -d backend"
    exit 1
fi

echo "✓ Container backend detectado"
echo ""
echo "📥 Copiando script de configuração para o container..."

# Copiar script para o container
docker cp simulators/setup_simulated_tags.py optiflow-ai--backend:/app/setup_simulated_tags.py

echo "✓ Script copiado com sucesso"
echo ""
echo "🔧 Executando configuração de tags..."
echo ""

# Executar script dentro do container
docker exec -it optiflow-ai--backend python /app/setup_simulated_tags.py

echo ""
echo "=============================================================================="
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "=============================================================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1️⃣  Iniciar o simulador de tags (em outro terminal):"
echo "    cd simulators"
echo "    pip install -r requirements.txt"
echo "    python industrial_tags_simulator.py"
echo ""
echo "2️⃣  Acessar o frontend OptiFlow:"
echo "    http://localhost:3000"
echo ""
echo "3️⃣  Visualizar as tags criadas:"
echo "    http://localhost:3000/tags"
echo ""
echo "4️⃣  Criar dashboards e análises:"
echo "    http://localhost:3000/analytics"
echo ""
echo "=============================================================================="
