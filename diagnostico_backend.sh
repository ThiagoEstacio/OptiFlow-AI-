#!/bin/bash
# Diagnóstico e Criação de Usuário Admin

echo "=========================================="
echo "DIAGNÓSTICO - Backend e Autenticação"
echo "=========================================="
echo ""

echo "1. STATUS DOS CONTAINERS PRINCIPAIS:"
echo "-------------------------------------------"
docker compose ps backend postgres redis
echo ""

echo "2. BACKEND ESTÁ RESPONDENDO?"
echo "-------------------------------------------"
curl -s http://localhost:8000/docs | head -5 || echo "❌ Backend não está respondendo"
echo ""

echo "3. TESTAR ENDPOINT DE SAÚDE DO BACKEND:"
echo "-------------------------------------------"
curl -s http://localhost:8000/health || echo "❌ Endpoint /health não encontrado"
echo ""

echo "4. LOGS DO BACKEND (últimas 30 linhas):"
echo "-------------------------------------------"
docker compose logs backend --tail=30
echo ""

echo "5. VERIFICAR USUÁRIOS NO BANCO DE DADOS:"
echo "-------------------------------------------"
docker compose exec postgres psql -U optiflow -d optiflow -c "SELECT id, email, full_name, role, is_active FROM users;" 2>/dev/null || echo "❌ Não foi possível conectar ao banco"
echo ""

echo "=========================================="
echo "SOLUÇÃO: CRIAR USUÁRIO ADMIN"
echo "=========================================="
echo ""
echo "Se não houver usuários no banco, execute:"
echo ""
echo "  ./criar_usuario_admin.sh"
echo ""
