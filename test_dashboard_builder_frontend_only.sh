#!/bin/bash
# Script de Teste - Dashboard Builder (Frontend Only)
# Testa o Dashboard Builder com dados simulados

echo "=============================================================================="
echo "🎨 Dashboard Builder - Teste Frontend"
echo "=============================================================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📋 Este teste irá:"
echo "   1. Iniciar o servidor de desenvolvimento do frontend"
echo "   2. Abrir o Dashboard Builder"
echo "   3. Usar dados simulados para demonstração"
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Diretório frontend não encontrado${NC}"
    echo "   Execute este script na raiz do projeto OptiFlow-AI-"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Instalando dependências...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo -e "${GREEN}✅ Dependências instaladas${NC}"
echo ""

echo "=============================================================================="
echo "🚀 Iniciando servidor de desenvolvimento..."
echo "=============================================================================="
echo ""

cd frontend

echo -e "${BLUE}Servidor iniciando em http://localhost:3000${NC}"
echo ""
echo "=============================================================================="
echo "🎨 COMO TESTAR O DASHBOARD BUILDER"
echo "=============================================================================="
echo ""
echo -e "${YELLOW}PASSO 1: Acesse o Dashboard Builder${NC}"
echo "   URL: http://localhost:3000/dashboard-builder"
echo ""
echo -e "${YELLOW}PASSO 2: Adicione um Widget${NC}"
echo "   • Clique no botão: 🎯 Gauge"
echo "   • Um widget aparecerá no canvas"
echo ""
echo -e "${YELLOW}PASSO 3: Teste os Tags Simulados${NC}"
echo "   • No painel esquerdo, veja a lista de tags"
echo "   • Clique e ARRASTE um tag (ex: CONV1_MOTOR_CURRENT)"
echo "   • SOLTE sobre o widget Gauge"
echo "   • ${GREEN}✨ Dados simulados aparecerão!${NC}"
echo ""
echo -e "${YELLOW}PASSO 4: Adicione Mais Widgets${NC}"
echo "   • 🎯 Gauge - Para medidores tipo velocímetro"
echo "   • 🔢 Value - Para valores numéricos grandes"
echo "   • 📈 Time Series - Para gráficos históricos"
echo "   • 📊 Chart - Para gráficos diversos"
echo ""
echo -e "${YELLOW}PASSO 5: Personalize${NC}"
echo "   • ARRASTE o cabeçalho do widget para mover"
echo "   • ARRASTE os cantos para redimensionar"
echo "   • DUPLO-CLIQUE no título para editar"
echo "   • Clique no X para deletar"
echo ""
echo -e "${YELLOW}PASSO 6: Salve${NC}"
echo "   • Clique em 💾 Save no toolbar"
echo "   • Dashboard salvo no localStorage"
echo ""
echo "=============================================================================="
echo "📊 Tags Disponíveis (Dados Simulados)"
echo "=============================================================================="
echo ""
echo -e "${BLUE}Motor Tags:${NC}"
echo "   • CONV1_MOTOR_CURRENT (0-300A)"
echo "   • CONV1_MOTOR_TEMP (20-120°C)"
echo "   • CONV1_VIBRATION (0-15 mm/s)"
echo "   • ELEV1_MOTOR_CURRENT (0-400A)"
echo "   • SHIP_MOTOR_CURRENT (0-500A)"
echo ""
echo -e "${BLUE}Production Tags:${NC}"
echo "   • SHIP_FLOW_RATE (0-3000 t/h)"
echo "   • VESSEL_PROGRESS (0-100%)"
echo "   • LOADING_RATE_TOTAL (toneladas)"
echo ""
echo -e "${BLUE}Quality Tags:${NC}"
echo "   • PRODUCT_MOISTURE (% umidade)"
echo "   • PRODUCT_TEMP (temperatura)"
echo ""
echo "=============================================================================="
echo "ℹ️  NOTA IMPORTANTE"
echo "=============================================================================="
echo ""
echo "Este teste usa DADOS SIMULADOS gerados pelo navegador."
echo ""
echo "Para testar com dados REAIS do backend:"
echo "   1. Inicie Docker Compose: docker compose up -d"
echo "   2. Execute: ./setup_smartport.sh"
echo "   3. Inicie o simulador: python3 simulators/smartport_bulk_terminal_simulator.py"
echo "   4. Os widgets se conectarão via WebSocket automaticamente"
echo ""
echo "=============================================================================="
echo ""
echo -e "${GREEN}Pressione Ctrl+C para parar o servidor${NC}"
echo ""

# Start dev server
npm run dev
