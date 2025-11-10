#!/bin/bash
# OptiFlow AI - Parar todos os containers via Docker Compose
# Uso: ./stop-all.sh

echo "============================================================"
echo "🛑 Parando OptiFlow AI Platform..."
echo "============================================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ir para diretório raiz do projeto
cd "$(dirname "$0")"

# Verificar se há containers rodando
echo -e "${BLUE}🔍 Verificando containers em execução...${NC}"
RUNNING_CONTAINERS=$(docker compose ps -q 2>/dev/null | wc -l)

if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Nenhum container OptiFlow está rodando${NC}"
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✅ Nada para parar${NC}"
    echo "============================================================"
    exit 0
fi

echo -e "${YELLOW}📦 Encontrados $RUNNING_CONTAINERS containers rodando${NC}"
echo ""

# Parar todos os containers
echo -e "${BLUE}🛑 Parando todos os containers...${NC}"
docker compose down

echo ""
echo -e "${BLUE}🧹 Limpando processos locais (se houver)...${NC}"
# Limpar processos locais que possam estar rodando
pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "${GREEN}✅ Processos uvicorn locais parados${NC}" || true
pkill -f "npm run dev" 2>/dev/null && echo -e "${GREEN}✅ Processos npm/vite locais parados${NC}" || true

# Limpar arquivos PID
rm -f /tmp/optiflow-backend.pid /tmp/optiflow-frontend.pid 2>/dev/null

echo ""
echo "============================================================"
echo -e "${GREEN}✅ OptiFlow AI Platform totalmente parado${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}💡 Para iniciar novamente:${NC}"
echo "  ./start-all.sh"
echo ""
