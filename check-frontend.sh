#!/bin/bash
# Script de Diagnóstico do Frontend
echo "============================================================"
echo "Diagnóstico do Frontend OptiFlow"
echo "============================================================"
echo ""

echo "1. Status do Container Frontend:"
docker ps --filter "name=optiflow-frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2. Teste de Acessibilidade HTTP:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3000
echo ""

echo "3. Teste de Carregamento do main.tsx:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3000/src/main.tsx
echo ""

echo "4. Últimas 15 linhas do log do Vite:"
docker logs optiflow-frontend 2>&1 | tail -15
echo ""

echo "5. Verificar @mui/material instalado:"
docker exec optiflow-frontend sh -c "ls -la /app/node_modules/@mui/material 2>&1 | head -5"
echo ""

echo "6. Teste de Conectividade Backend:"
curl -s http://localhost:8000/health
echo ""
echo ""

echo "============================================================"
echo "Instruções para Debug no Navegador:"
echo "============================================================"
echo ""
echo "1. Abra http://localhost:3000 no navegador"
echo "2. Pressione F12 para abrir DevTools"
echo "3. Vá na aba 'Console' e verifique erros em VERMELHO"
echo "4. Vá na aba 'Network' e recarregue (F5)"
echo "5. Procure por requisições em VERMELHO (falharam)"
echo ""
echo "Erros comuns:"
echo "- Failed to fetch: Backend não está acessível"
echo "- Cannot find module: Dependência faltando"
echo "- CSP violation: Content Security Policy bloqueando"
echo ""
