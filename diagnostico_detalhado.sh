#!/bin/bash
# Diagnóstico Detalhado do Frontend

echo "============================================="
echo "DIAGNÓSTICO DETALHADO - FRONTEND SMARTPORT"
echo "============================================="
echo ""

echo "1. CONTEÚDO RETORNADO POR LOCALHOST:3000:"
echo "---------------------------------------------"
curl -s http://localhost:3000 > /tmp/frontend_output.html
head -50 /tmp/frontend_output.html
echo ""
echo "Linhas totais no HTML: $(wc -l < /tmp/frontend_output.html)"
echo ""

echo "2. VERIFICAR SE VITE ESTÁ SERVINDO CORRETAMENTE:"
echo "---------------------------------------------"
curl -s http://localhost:3000/@vite/client | head -10
echo ""

echo "3. VERIFICAR MAIN.TSX:"
echo "---------------------------------------------"
curl -s http://localhost:3000/src/main.tsx | head -20
echo ""

echo "4. STATUS DO CONTAINER FRONTEND:"
echo "---------------------------------------------"
docker compose ps frontend
echo ""

echo "5. LOGS COMPLETOS DO FRONTEND (últimas 100 linhas):"
echo "---------------------------------------------"
docker compose logs frontend --tail=100
echo ""

echo "6. PROCESSOS NODE NO CONTAINER:"
echo "---------------------------------------------"
docker compose exec frontend ps aux 2>/dev/null | grep -E "node|vite|PID"
echo ""

echo "7. VARIÁVEIS DE AMBIENTE VITE:"
echo "---------------------------------------------"
docker compose exec frontend env 2>/dev/null | grep VITE
echo ""

echo "8. ARQUIVOS NO DIRETÓRIO SRC:"
echo "---------------------------------------------"
docker compose exec frontend ls -la /app/src/ 2>/dev/null | head -20
echo ""

echo "============================================="
echo "TESTE NO NAVEGADOR"
echo "============================================="
echo ""
echo "Por favor, execute MANUALMENTE no navegador:"
echo "1. Abra: http://localhost:3000"
echo "2. Pressione F12 para abrir DevTools"
echo "3. Vá para a aba 'Console'"
echo "4. Copie TODOS os erros em vermelho (se houver)"
echo "5. Vá para a aba 'Network'"
echo "6. Recarregue a página (Ctrl+R)"
echo "7. Veja se há requisições falhando (em vermelho)"
echo ""
echo "Cole aqui os erros do Console e Network!"
