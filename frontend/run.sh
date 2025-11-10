#!/bin/bash
# OptiFlow AI Frontend - Script de Inicialização Otimizado
# Uso: ./run.sh

set -e

echo "============================================================"
echo "🎨 OptiFlow AI Frontend - Iniciando..."
echo "============================================================"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Navegar para o diretório frontend
cd "$(dirname "$0")"

# Verificar Node version
echo -e "${BLUE}🔍 Verificando Node.js...${NC}"
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ Node: $NODE_VERSION${NC}"
echo -e "${GREEN}✅ npm: $NPM_VERSION${NC}"
echo ""

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules não encontrado${NC}"
    echo -e "${BLUE}📦 Instalando dependências...${NC}"
    npm install
    echo ""
fi

# Limpar cache do Vite
echo -e "${BLUE}🧹 Limpando cache do Vite...${NC}"
rm -rf node_modules/.vite
echo -e "${GREEN}✅ Cache limpo${NC}"
echo ""

echo "============================================================"
echo -e "${GREEN}✅ Iniciando Vite Dev Server...${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}📍 URLs de Acesso:${NC}"
echo "   Local:   http://localhost:3000"
echo "   Network: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo -e "${BLUE}💡 Recursos Ativados:${NC}"
echo "   ✅ Hot Module Replacement (HMR)"
echo "   ✅ Memória otimizada (4GB)"
echo "   ✅ Watch otimizado"
echo "   ✅ Proxy para backend (API e WebSocket)"
echo ""
echo "============================================================"
echo ""

# Iniciar servidor com memória aumentada
exec NODE_OPTIONS='--max-old-space-size=4096' npm run dev
