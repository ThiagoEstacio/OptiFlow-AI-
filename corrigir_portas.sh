#!/bin/bash
# Script de Correção Automática - Mover Frontend para 3000 e Grafana para 3001

set -e

echo "======================================================================"
echo "CORREÇÃO AUTOMÁTICA DE PORTAS"
echo "======================================================================"
echo ""
echo "Este script vai:"
echo "  - Mover Frontend de porta 5173 para 3000"
echo "  - Mover Grafana de porta 3000 para 3001"
echo "  - Atualizar vite.config.ts"
echo "  - Reiniciar containers"
echo ""
read -p "Continuar? (s/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Cancelado."
    exit 1
fi

cd ~/OptiFlow-AI-

# Backup
echo "📦 Criando backups..."
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
cp frontend/vite.config.ts frontend/vite.config.ts.backup.$(date +%Y%m%d_%H%M%S)

# Verificar estado atual
echo ""
echo "📊 Estado ANTES das mudanças:"
echo "Frontend ports:"
grep -A 15 "# Frontend Web Application" docker-compose.yml | grep "ports:" | head -1
echo "Grafana ports:"
grep -A 10 "# Grafana" docker-compose.yml | grep "ports:" | head -1
echo "Vite port:"
grep "port:" frontend/vite.config.ts | head -1

# Aplicar mudanças
echo ""
echo "🔧 Aplicando mudanças..."

# 1. Frontend: mudar porta de 5173 para 3000
echo "  - Atualizando porta do frontend no docker-compose.yml..."
sed -i 's/"5173:5173"/"3000:3000"/' docker-compose.yml

# 2. Frontend: adicionar --port 3000 no comando
echo "  - Atualizando comando do frontend..."
sed -i 's/npm run dev -- --host$/npm run dev -- --host --port 3000/' docker-compose.yml

# 3. Grafana: mudar porta de 3000:3000 para 3001:3000
echo "  - Atualizando porta do Grafana..."
# Cuidado: agora temos dois "3000:3000", precisamos mudar apenas o do Grafana
# Vamos usar uma abordagem mais específica
sed -i '/# Grafana/,/networks:/ { s/"3000:3000"/"3001:3000"/ }' docker-compose.yml

# 4. Vite config: mudar porta de 5173 para 3000
echo "  - Atualizando vite.config.ts..."
sed -i 's/port: 5173/port: 3000/' frontend/vite.config.ts

# Verificar mudanças
echo ""
echo "📊 Estado DEPOIS das mudanças:"
echo "Frontend ports:"
grep -A 15 "# Frontend Web Application" docker-compose.yml | grep "ports:" | head -1
echo "Grafana ports:"
grep -A 10 "# Grafana" docker-compose.yml | grep "ports:" | head -1
echo "Vite port:"
grep "port:" frontend/vite.config.ts | head -1

# Reiniciar containers
echo ""
echo "🔄 Parando containers..."
docker compose down

echo ""
echo "🏗️  Reconstruindo frontend..."
docker compose build frontend

echo ""
echo "🚀 Iniciando containers..."
docker compose up -d

echo ""
echo "⏳ Aguardando 30 segundos para containers iniciarem..."
sleep 30

echo ""
echo "✅ Verificando status..."
docker compose ps | grep -E "(frontend|grafana)"

echo ""
echo "======================================================================"
echo "CORREÇÃO CONCLUÍDA!"
echo "======================================================================"
echo ""
echo "URLs atualizadas:"
echo "  - SmartPort Frontend: http://localhost:3000"
echo "  - Grafana: http://localhost:3001"
echo "  - Backend API: http://localhost:8000/docs"
echo ""
echo "Teste agora: http://localhost:3000"
echo ""
echo "Se ainda ver Grafana, execute:"
echo "  docker compose logs frontend"
echo "  E me envie a saída para diagnóstico."
echo ""
