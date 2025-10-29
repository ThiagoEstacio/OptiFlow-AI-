#!/bin/bash
# Script para corrigir problemas de CORS e Backend

echo "=========================================="
echo "DIAGNÓSTICO E CORREÇÃO - CORS / BACKEND"
echo "=========================================="
echo ""

echo "1. VERIFICANDO BACKEND..."
echo "-------------------------------------------"
docker compose ps backend

if ! docker compose ps backend | grep -q "Up"; then
    echo "❌ Backend não está rodando!"
    echo ""
    echo "Iniciando backend..."
    docker compose up -d backend
    sleep 15
fi

echo ""
echo "2. TESTANDO CONEXÃO COM BACKEND..."
echo "-------------------------------------------"
curl -s http://localhost:8000/health || echo "❌ Endpoint /health não respondeu"
echo ""

echo "3. TESTANDO CORS..."
echo "-------------------------------------------"
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     -v http://localhost:8000/api/v1/auth/login 2>&1 | grep -i "access-control"

echo ""
echo "4. LOGS DO BACKEND (últimas 30 linhas)..."
echo "-------------------------------------------"
docker compose logs backend --tail=30

echo ""
echo "=========================================="
echo "SOLUÇÃO"
echo "=========================================="
echo ""

echo "Se houver erro de CORS ou backend não responder:"
echo ""
echo "OPÇÃO 1: Reiniciar backend"
echo "  docker compose restart backend"
echo "  sleep 10"
echo "  docker compose logs backend --tail=20"
echo ""

echo "OPÇÃO 2: Reconstruir backend"
echo "  docker compose down"
echo "  docker compose build backend --no-cache"
echo "  docker compose up -d"
echo ""

echo "OPÇÃO 3: Verificar variáveis de ambiente"
echo "  docker compose exec backend env | grep CORS"
echo ""

echo "=========================================="
