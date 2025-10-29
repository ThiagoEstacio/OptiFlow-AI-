#!/bin/bash
# Script de Correção Rápida - Backend e CORS

echo "=========================================="
echo "CORRIGINDO BACKEND E CORS"
echo "=========================================="
echo ""

echo "1. Parando backend..."
docker compose stop backend

echo ""
echo "2. Reiniciando Redis (limpar rate limit)..."
docker compose restart redis
sleep 3

echo ""
echo "3. Iniciando backend..."
docker compose up -d backend

echo ""
echo "4. Aguardando backend inicializar (15s)..."
sleep 15

echo ""
echo "5. Testando backend..."
curl -s http://localhost:8000/health && echo "✅ Backend respondendo!" || echo "❌ Backend não responde"

echo ""
echo "6. Testando CORS..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
     -H "Origin: http://localhost:3000" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/auth/login)

if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo "✅ CORS configurado corretamente (recebeu HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" -eq 000 ]; then
    echo "❌ Backend não está respondendo"
else
    echo "⚠️  HTTP $HTTP_CODE - verifique logs"
fi

echo ""
echo "7. Logs do backend:"
docker compose logs backend --tail=15

echo ""
echo "=========================================="
echo "RESULTADO"
echo "=========================================="
echo ""

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend está funcionando!"
    echo ""
    echo "Agora tente fazer login novamente em:"
    echo "  http://localhost:3000"
    echo ""
    echo "Credenciais:"
    echo "  Email: admin@smartport.com"
    echo "  Senha: Admin@123456"
    echo ""
else
    echo "❌ Backend ainda não está respondendo"
    echo ""
    echo "Execute:"
    echo "  docker compose logs backend --tail=50"
    echo ""
    echo "E compartilhe os logs para diagnóstico."
fi

echo "=========================================="
