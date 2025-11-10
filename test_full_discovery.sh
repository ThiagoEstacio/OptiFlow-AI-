#!/bin/bash
# =============================================================================
# Teste Completo: Servidor OPC-UA + Auto-Discovery
# =============================================================================

echo "=========================================================================="
echo "  OPTIFLOW - TESTE COMPLETO DE AUTO-DISCOVERY"
echo "=========================================================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# ETAPA 1: Iniciar Servidor OPC-UA
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ETAPA 1: Iniciar Servidor OPC-UA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar se servidor já está rodando
if lsof -i:4840 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Servidor OPC-UA já está rodando na porta 4840${NC}"
    echo "  Continuando com servidor existente..."
else
    echo "🚀 Iniciando servidor OPC-UA em background..."
    cd /home/thiestacio/OptiFlow-AI-
    /home/thiestacio/anaconda3/envs/optiflow/bin/python backend/scripts/run_opcua_server.py > opcua_server.log 2>&1 &
    OPCUA_PID=$!
    echo "  PID do servidor: $OPCUA_PID"

    # Aguardar servidor iniciar
    echo "  Aguardando servidor inicializar..."
    sleep 5

    # Verificar se iniciou
    if lsof -i:4840 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Servidor OPC-UA iniciado com sucesso!${NC}"
    else
        echo -e "${RED}✗ FALHA: Servidor não iniciou${NC}"
        echo "  Verificar logs em: opcua_server.log"
        exit 1
    fi
fi

echo ""

# =============================================================================
# ETAPA 2: Auto-Discovery (sem banco)
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ETAPA 2: Auto-Discovery (Discovery apenas)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd /home/thiestacio/OptiFlow-AI-/gateway

echo "🔍 Executando discovery..."
/home/thiestacio/anaconda3/envs/optiflow/bin/python test_opcua_discovery.py opc.tcp://localhost:4840/optiflow/terminal

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Discovery concluído com sucesso!${NC}"

    # Mostrar resumo do JSON
    if [ -f discovery_results.json ]; then
        echo ""
        echo "📊 Resumo dos resultados:"
        /home/thiestacio/anaconda3/envs/optiflow/bin/python3 -c "
import json
with open('discovery_results.json', 'r') as f:
    data = json.load(f)
    print(f'  Total de tags descobertos: {data[\"total_tags\"]}')
    if 'statistics' in data:
        stats = data['statistics']
        print(f'  Classificados: {stats.get(\"classified\", 0)}')
        print(f'  Não classificados: {stats.get(\"unclassified\", 0)}')
        if 'by_type' in stats:
            print('\n  Por tipo de equipamento:')
            for eq_type, count in stats['by_type'].items():
                print(f'    - {eq_type}: {count}')
"
    fi
else
    echo -e "${RED}✗ FALHA no discovery${NC}"
    exit 1
fi

echo ""

# =============================================================================
# ETAPA 3: Auto-Discovery + PostgreSQL
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ETAPA 3: Auto-Discovery + PostgreSQL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "💾 Executando discovery com persistência..."

export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=optiflow
export POSTGRES_USER=optiflow
export POSTGRES_PASSWORD=optiflow_password

/home/thiestacio/anaconda3/envs/optiflow/bin/python test_discovery_to_db.py \
    opc.tcp://localhost:4840/optiflow/terminal \
    "Simulador Terminal TEAG"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Discovery + persistência concluído!${NC}"
else
    echo -e "${RED}✗ FALHA no discovery com persistência${NC}"
fi

echo ""

# =============================================================================
# ETAPA 4: Verificar no Banco
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ETAPA 4: Verificar Dados no PostgreSQL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "🗄️  Consultando PostgreSQL..."

docker exec optiflow-postgres psql -U optiflow -d optiflow << 'EOF'
-- Devices
SELECT 'Total de Devices:' as label, COUNT(*) as count
FROM devices;

-- Tags totais
SELECT 'Total de Tags:' as label, COUNT(*) as count
FROM tags
WHERE is_active = true;

-- Por tipo de equipamento
SELECT
    'Tags por Tipo' as label,
    settings->>'equipment_type' as equipment_type,
    COUNT(*) as count
FROM tags
WHERE is_active = true
  AND settings->>'equipment_type' IS NOT NULL
GROUP BY settings->>'equipment_type'
ORDER BY count DESC;

-- Por rota
SELECT
    'Tags por Rota' as label,
    settings->>'route' as route,
    COUNT(*) as count
FROM tags
WHERE is_active = true
  AND settings->>'route' IS NOT NULL
GROUP BY settings->>'route'
ORDER BY count DESC;

-- Exemplos de tags
SELECT
    name,
    category,
    unit,
    settings->>'equipment_type' as equipment_type,
    settings->>'equipment_id' as equipment_id
FROM tags
WHERE is_active = true
ORDER BY name
LIMIT 10;
EOF

echo ""

# =============================================================================
# RESUMO FINAL
# =============================================================================

echo ""
echo "=========================================================================="
echo -e "${GREEN}  ✅ TESTE COMPLETO FINALIZADO${NC}"
echo "=========================================================================="
echo ""
echo "Arquivos gerados:"
echo "  - gateway/discovery_results.json (resultados da descoberta)"
echo "  - opcua_server.log (log do servidor OPC-UA)"
echo ""
echo "Próximos passos:"
echo "  1. Testar API REST: POST /api/v1/opcua-discovery/discover"
echo "  2. Criar frontend para visualizar tags"
echo "  3. Conectar agente IA aos tags descobertos"
echo ""
echo "=========================================================================="
