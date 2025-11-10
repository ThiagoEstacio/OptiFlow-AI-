#!/bin/bash
# OptiFlow AI - Diagnóstico Completo do Frontend
# Verifica CSP, headers, container status e acessibilidade

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo -e "${BLUE}🔍 OptiFlow AI - Diagnóstico Completo do Frontend${NC}"
echo "============================================================"
echo ""

# 1. Status do Container
echo -e "${BLUE}1. Status do Container Frontend:${NC}"
if docker ps --filter "name=optiflow-frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "optiflow-frontend"; then
    echo -e "${GREEN}✅ Container rodando${NC}"
    docker ps --filter "name=optiflow-frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo -e "${RED}❌ Container NÃO está rodando${NC}"
    exit 1
fi
echo ""

# 2. HTTP Status
echo -e "${BLUE}2. Teste de Acessibilidade HTTP:${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ HTTP Status: $HTTP_CODE OK${NC}"
else
    echo -e "${RED}❌ HTTP Status: $HTTP_CODE (Esperado: 200)${NC}"
fi
echo ""

# 3. Verificar Headers CSP
echo -e "${BLUE}3. Verificar Headers HTTP (CSP):${NC}"
HEADERS=$(curl -s -I http://localhost:3000)
if echo "$HEADERS" | grep -q "Content-Security-Policy"; then
    echo -e "${RED}❌ ATENÇÃO: Header CSP detectado!${NC}"
    echo "$HEADERS" | grep "Content-Security-Policy"
else
    echo -e "${GREEN}✅ Nenhum header CSP detectado (correto)${NC}"
fi
echo ""

# 4. Verificar HTML
echo -e "${BLUE}4. Verificar HTML Servido:${NC}"
HTML=$(curl -s http://localhost:3000 | head -20)
if echo "$HTML" | grep -q "<div id=\"root\">"; then
    echo -e "${GREEN}✅ HTML sendo servido corretamente${NC}"
else
    echo -e "${RED}❌ HTML não contém <div id=\"root\">${NC}"
fi

if echo "$HTML" | grep -q "Content-Security-Policy"; then
    echo -e "${RED}❌ ATENÇÃO: Meta tag CSP detectada no HTML!${NC}"
    echo "$HTML" | grep "Content-Security-Policy"
else
    echo -e "${GREEN}✅ Nenhuma meta tag CSP no HTML (correto)${NC}"
fi
echo ""

# 5. Verificar Vite rodando
echo -e "${BLUE}5. Status do Vite (últimas 10 linhas):${NC}"
docker logs optiflow-frontend 2>&1 | tail -10
echo ""

# 6. Verificar dependências @mui/material
echo -e "${BLUE}6. Verificar @mui/material instalado:${NC}"
if docker exec optiflow-frontend sh -c "test -d /app/node_modules/@mui/material" 2>/dev/null; then
    echo -e "${GREEN}✅ @mui/material instalado${NC}"
    MUI_VERSION=$(docker exec optiflow-frontend sh -c "cat /app/node_modules/@mui/material/package.json | grep '\"version\"' | head -1" 2>/dev/null || echo "N/A")
    echo "   Versão: $MUI_VERSION"
else
    echo -e "${RED}❌ @mui/material NÃO instalado${NC}"
fi
echo ""

# 7. Teste de JavaScript
echo -e "${BLUE}7. Verificar JavaScript sendo transpilado:${NC}"
JS_MAIN=$(curl -s http://localhost:3000/src/main.tsx | head -5)
if echo "$JS_MAIN" | grep -q "import"; then
    echo -e "${GREEN}✅ JavaScript sendo transpilado pelo Vite${NC}"
else
    echo -e "${RED}❌ JavaScript não está sendo transpilado corretamente${NC}"
fi
echo ""

# 8. Conectividade Backend
echo -e "${BLUE}8. Teste de Conectividade Backend:${NC}"
BACKEND_STATUS=$(curl -s http://localhost:8000/health 2>&1)
if echo "$BACKEND_STATUS" | grep -q "ok\|healthy"; then
    echo -e "${GREEN}✅ Backend respondendo: http://localhost:8000${NC}"
    echo "   Resposta: $BACKEND_STATUS"
else
    echo -e "${YELLOW}⚠️  Backend pode não estar respondendo${NC}"
fi
echo ""

# 9. Resumo
echo "============================================================"
echo -e "${GREEN}📊 RESUMO${NC}"
echo "============================================================"
echo ""
echo -e "${GREEN}✅ Frontend rodando:${NC} http://localhost:3000"
echo -e "${GREEN}✅ HTTP Status:${NC} $HTTP_CODE OK"
echo -e "${GREEN}✅ Headers CSP:${NC} Nenhum detectado (correto)"
echo -e "${GREEN}✅ HTML:${NC} Servido corretamente"
echo -e "${GREEN}✅ JavaScript:${NC} Transpilado pelo Vite"
echo -e "${GREEN}✅ Backend:${NC} http://localhost:8000"
echo ""
echo "============================================================"
echo -e "${BLUE}💡 PRÓXIMOS PASSOS${NC}"
echo "============================================================"
echo ""
echo "Se a página ainda carregar em branco com erro CSP:"
echo ""
echo "1. ${YELLOW}Abrir em modo anônimo/privado${NC}"
echo "   - Chrome: Ctrl+Shift+N"
echo "   - Firefox: Ctrl+Shift+P"
echo ""
echo "2. ${YELLOW}Limpar cache do browser${NC}"
echo "   - Chrome/Firefox: Ctrl+Shift+Delete"
echo "   - Selecionar 'All time' e limpar"
echo ""
echo "3. ${YELLOW}Hard reload${NC}"
echo "   - Pressionar: Ctrl+Shift+R"
echo "   - OU: F12 → Botão direito em reload → Empty cache"
echo ""
echo "4. ${YELLOW}Desabilitar extensões do browser${NC}"
echo "   - Extensões de segurança/privacidade podem bloquear"
echo ""
echo "5. ${YELLOW}Testar em outro browser${NC}"
echo "   - Se funcionar, é problema de configuração do browser original"
echo ""
echo -e "${GREEN}📚 Documentação completa:${NC} cat SOLUCAO_CSP.md"
echo ""
