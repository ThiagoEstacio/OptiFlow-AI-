#!/bin/bash
# Script de Correção Completa - Frontend + Backend

echo "=========================================="
echo "CORREÇÃO COMPLETA - SMARTPORT"
echo "=========================================="
echo ""

echo "🔄 PASSO 1: Parando todos os serviços..."
docker compose down

echo ""
echo "🔄 PASSO 2: Limpando cache do Docker..."
docker compose rm -f frontend backend

echo ""
echo "🔄 PASSO 3: Reconstruindo frontend com correções..."
docker compose build frontend --no-cache

echo ""
echo "🔄 PASSO 4: Reconstruindo backend..."
docker compose build backend --no-cache

echo ""
echo "🔄 PASSO 5: Iniciando todos os serviços..."
docker compose up -d

echo ""
echo "⏳ PASSO 6: Aguardando inicialização (30 segundos)..."
sleep 30

echo ""
echo "🧪 PASSO 7: Testando serviços..."
echo ""

echo "Frontend (porta 3000):"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3000

echo "Backend (porta 8000):"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:8000/health

echo "Grafana (porta 3001):"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3001

echo ""
echo "=========================================="
echo "✅ CORREÇÃO CONCLUÍDA"
echo "=========================================="
echo ""
echo "IMPORTANTE:"
echo ""
echo "1. Limpe o cache do navegador:"
echo "   - Pressione Ctrl+Shift+Del"
echo "   - Ou abra em modo anônimo (Ctrl+Shift+N)"
echo ""
echo "2. Acesse: http://localhost:3000"
echo ""
echo "3. Credenciais:"
echo "   Email: admin@smartport.com"
echo "   Senha: Admin@123456"
echo ""
echo "4. Se o usuário não existe, execute:"
echo "   ./criar_admin_automatico.sh"
echo ""
echo "=========================================="
echo ""

docker compose ps
