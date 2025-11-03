#!/bin/bash
# Script de Diagnóstico - Frontend não carregando

echo "=========================================="
echo "DIAGNÓSTICO DO FRONTEND SMARTPORT"
echo "=========================================="
echo ""

echo "1. STATUS DOS CONTAINERS:"
echo "-------------------------------------------"
docker compose ps
echo ""

echo "2. CONTAINER FRONTEND ESTÁ RODANDO?"
echo "-------------------------------------------"
docker compose ps frontend
echo ""

echo "3. LOGS DO FRONTEND (últimas 50 linhas):"
echo "-------------------------------------------"
docker compose logs frontend --tail=50
echo ""

echo "4. PORTA 3000 EM USO?"
echo "-------------------------------------------"
sudo lsof -i :3000 || echo "Nenhum processo usando porta 3000"
echo ""

echo "5. CONTEÚDO RETORNADO EM LOCALHOST:3000:"
echo "-------------------------------------------"
curl -s http://localhost:3000 | head -20
echo ""

echo "6. VERIFICAR INDEX.HTML DO BUILD:"
echo "-------------------------------------------"
docker compose exec frontend ls -la /app/dist/ 2>/dev/null || echo "Não foi possível acessar /app/dist/"
echo ""

echo "7. VARIÁVEIS DE AMBIENTE DO FRONTEND:"
echo "-------------------------------------------"
docker compose exec frontend env | grep VITE 2>/dev/null || echo "Não foi possível verificar variáveis"
echo ""

echo "8. PROCESSOS NODE RODANDO NO CONTAINER:"
echo "-------------------------------------------"
docker compose exec frontend ps aux | grep node 2>/dev/null || echo "Container não está acessível"
echo ""

echo "=========================================="
echo "DIAGNÓSTICO COMPLETO"
echo "=========================================="
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Se o container frontend não está rodando:"
echo "   docker compose up -d frontend"
echo ""
echo "2. Se o container está rodando mas com erros:"
echo "   docker compose restart frontend"
echo ""
echo "3. Se precisa reconstruir:"
echo "   docker compose down"
echo "   docker compose build frontend --no-cache"
echo "   docker compose up -d"
echo ""
echo "4. Para ver logs em tempo real:"
echo "   docker compose logs -f frontend"
