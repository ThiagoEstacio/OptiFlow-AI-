#!/bin/bash
# Script de Teste - Dashboard Builder SmartPort
# Execute este script para testar o Dashboard Builder completo

echo "=============================================================================="
echo "🎨 Dashboard Builder - Script de Teste"
echo "=============================================================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar serviços
echo "📋 Passo 1: Verificando serviços..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado${NC}"
    echo "   Por favor, instale o Docker primeiro"
    exit 1
fi

# Check se backend está rodando
if docker ps | grep -q optiflow-ai--backend; then
    echo -e "${GREEN}✅ Backend rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Backend não está rodando${NC}"
    echo ""
    echo "Iniciando backend..."
    docker compose up -d backend postgres influxdb redis
    sleep 5
    echo -e "${GREEN}✅ Backend iniciado${NC}"
fi

# Check se postgres está rodando
if docker ps | grep -q postgres; then
    echo -e "${GREEN}✅ PostgreSQL rodando${NC}"
else
    echo -e "${RED}❌ PostgreSQL não está rodando${NC}"
    exit 1
fi

# Check se InfluxDB está rodando
if docker ps | grep -q influxdb; then
    echo -e "${GREEN}✅ InfluxDB rodando${NC}"
else
    echo -e "${YELLOW}⚠️  InfluxDB não está rodando${NC}"
    echo "   Iniciando InfluxDB..."
    docker compose up -d influxdb
    sleep 3
fi

echo ""
echo "=============================================================================="
echo "📊 Passo 2: Configurando Tags SmartPort..."
echo "=============================================================================="
echo ""

if [ -f "./setup_smartport.sh" ]; then
    echo "Executando setup_smartport.sh..."
    ./setup_smartport.sh
    echo -e "${GREEN}✅ Tags configuradas${NC}"
else
    echo -e "${YELLOW}⚠️  setup_smartport.sh não encontrado${NC}"
    echo "   Pulando configuração de tags..."
fi

echo ""
echo "=============================================================================="
echo "🎮 Passo 3: Iniciando Simulador..."
echo "=============================================================================="
echo ""

# Check se simulador já está rodando
if pgrep -f "smartport_bulk_terminal_simulator" > /dev/null; then
    echo -e "${YELLOW}⚠️  Simulador já está rodando${NC}"
    echo "   Parando simulador antigo..."
    pkill -f "smartport_bulk_terminal_simulator"
    sleep 2
fi

# Iniciar simulador em background
echo "Iniciando simulador em background..."
cd simulators

# Check se pymodbus está instalado
if python3 -c "import pymodbus" 2>/dev/null; then
    echo -e "${GREEN}✅ pymodbus instalado${NC}"
else
    echo -e "${YELLOW}⚠️  Instalando pymodbus...${NC}"
    pip install -q pymodbus
fi

# Iniciar simulador
nohup python3 smartport_bulk_terminal_simulator.py > /tmp/simulator.log 2>&1 &
SIMULATOR_PID=$!
echo -e "${GREEN}✅ Simulador iniciado (PID: $SIMULATOR_PID)${NC}"
echo "   Logs: tail -f /tmp/simulator.log"

cd ..

sleep 3

echo ""
echo "=============================================================================="
echo "⏳ Aguardando simulador estabilizar..."
echo "=============================================================================="
echo ""

for i in {5..1}; do
    echo -n "$i... "
    sleep 1
done
echo "Pronto!"

echo ""
echo "=============================================================================="
echo "🎨 Passo 4: Como Testar o Dashboard Builder"
echo "=============================================================================="
echo ""

echo -e "${BLUE}INSTRUÇÕES DE TESTE:${NC}"
echo ""
echo "1️⃣  Abra o navegador e acesse:"
echo -e "   ${GREEN}http://localhost:3000/dashboard-builder${NC}"
echo ""
echo "2️⃣  Login (se necessário):"
echo "   Email: admin@smartport.com"
echo "   Senha: Admin@123456"
echo ""
echo "3️⃣  No Dashboard Builder:"
echo "   a) Clique no botão: ${YELLOW}🎯 Gauge${NC}"
echo "   b) Veja a lista de tags no painel esquerdo"
echo "   c) Arraste a tag ${YELLOW}CONV1_MOTOR_CURRENT${NC}"
echo "   d) Solte no widget Gauge"
echo "   e) ${GREEN}BOOM! Dados ao vivo aparecem!${NC} 🎉"
echo ""
echo "4️⃣  Adicione mais widgets:"
echo "   • ${YELLOW}🎯 Gauge${NC} para CONV1_MOTOR_TEMP"
echo "   • ${YELLOW}🎯 Gauge${NC} para CONV1_VIBRATION"
echo "   • ${YELLOW}🔢 Value${NC} para SHIP_FLOW_RATE"
echo ""
echo "5️⃣  Personalize:"
echo "   • Arraste widgets para reposicionar"
echo "   • Arraste cantos para redimensionar"
echo "   • Duplo-clique no título para editar"
echo ""
echo "6️⃣  Salve seu dashboard:"
echo "   • Clique em ${YELLOW}💾 Save${NC}"
echo ""

echo "=============================================================================="
echo "📊 Tags Disponíveis para Teste:"
echo "=============================================================================="
echo ""
echo -e "${YELLOW}Motores (Corrente, Temperatura, Vibração):${NC}"
echo "   • CONV1_MOTOR_CURRENT (0-300A)"
echo "   • CONV1_MOTOR_TEMP (20-120°C)"
echo "   • CONV1_VIBRATION (0-15 mm/s)"
echo "   • ELEV1_MOTOR_CURRENT (0-400A)"
echo "   • SHIP_MOTOR_CURRENT (0-500A)"
echo ""
echo -e "${YELLOW}Produção:${NC}"
echo "   • SHIP_FLOW_RATE (0-3000 t/h) ⭐ Principal KPI"
echo "   • VESSEL_PROGRESS (0-100%)"
echo "   • LOADING_RATE_TOTAL (toneladas acumuladas)"
echo ""
echo -e "${YELLOW}Qualidade:${NC}"
echo "   • PRODUCT_MOISTURE (% umidade)"
echo "   • PRODUCT_TEMP (temperatura do produto)"
echo ""

echo "=============================================================================="
echo "🔍 Verificar Anomalias Simuladas:"
echo "=============================================================================="
echo ""
echo "Após 5 minutos, você verá:"
echo -e "   ${RED}⚠️  Anomalia 1:${NC} Temperatura rolamento subindo (CONV1_BEARING_TEMP)"
echo -e "   ${RED}⚠️  Anomalia 1:${NC} Vibração aumentando (CONV1_VIBRATION)"
echo ""
echo "Após 10 minutos:"
echo -e "   ${RED}⚠️  Anomalia 2:${NC} Sobrecarga no elevador (ELEV1_MOTOR_CURRENT)"
echo ""

echo "=============================================================================="
echo "📝 Comandos Úteis:"
echo "=============================================================================="
echo ""
echo "Ver logs do simulador:"
echo "   tail -f /tmp/simulator.log"
echo ""
echo "Parar simulador:"
echo "   pkill -f smartport_bulk_terminal_simulator"
echo ""
echo "Reiniciar backend:"
echo "   docker compose restart backend"
echo ""
echo "Ver logs do backend:"
echo "   docker logs -f optiflow-ai--backend"
echo ""

echo "=============================================================================="
echo "✅ TUDO PRONTO! Abra o navegador e teste!"
echo "=============================================================================="
echo ""
echo -e "${GREEN}URL: http://localhost:3000/dashboard-builder${NC}"
echo ""
echo "Pressione Ctrl+C para parar o script (simulador continuará rodando)"
echo ""

# Keep script running
echo "Monitorando simulador..."
echo ""
tail -f /tmp/simulator.log
