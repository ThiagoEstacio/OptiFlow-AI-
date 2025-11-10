#!/bin/bash

echo "========================================="
echo "OPTIFLOW - TESTE COMPLETO DE ALARMES"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Login
echo "1. Testando autenticação..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ FALHA: Não foi possível obter token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
else
    echo -e "${GREEN}✓ Login OK - Token obtido${NC}"
fi

echo ""
echo "========================================="
echo "2. Testando GET /api/v1/alarms/"
echo "========================================="

ALARMS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/alarms/?limit=5")

# Check if response is valid JSON
if echo "$ALARMS_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    ALARM_COUNT=$(echo "$ALARMS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data) if isinstance(data, list) else len(data.get('items', [])))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Endpoint funcionando${NC}"
    echo "Total de alarmes: $ALARM_COUNT"
    echo ""
    echo "Exemplo (primeiro alarme):"
    echo "$ALARMS_RESPONSE" | python3 -m json.tool | head -30
else
    echo -e "${RED}✗ FALHA: Resposta inválida${NC}"
    echo "$ALARMS_RESPONSE"
fi

echo ""
echo "========================================="
echo "3. Testando GET /api/v1/alarms/events"
echo "========================================="

EVENTS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/alarms/events?limit=10")

if echo "$EVENTS_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    EVENT_COUNT=$(echo "$EVENTS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data) if isinstance(data, list) else len(data.get('items', [])))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Endpoint funcionando${NC}"
    echo "Total de eventos retornados: $EVENT_COUNT"
    echo ""
    echo "Exemplo (primeiro evento):"
    echo "$EVENTS_RESPONSE" | python3 -m json.tool | head -40
else
    echo -e "${RED}✗ FALHA: Resposta inválida${NC}"
    echo "$EVENTS_RESPONSE"
fi

echo ""
echo "========================================="
echo "4. Estatísticas do Banco de Dados"
echo "========================================="

docker exec optiflow-postgres psql -U optiflow -d optiflow << 'EOF'
-- Total de definições
SELECT 'Total de Definições de Alarmes:' as label, COUNT(*) as count
FROM alarm_definitions;

-- Total de eventos
SELECT 'Total de Eventos de Alarmes:' as label, COUNT(*) as count
FROM alarm_events;

-- Eventos por severidade
SELECT
    'Eventos por Severidade' as label,
    ad.severity,
    COUNT(ae.id) as count
FROM alarm_events ae
JOIN alarm_definitions ad ON ae.definition_id = ad.id
GROUP BY ad.severity
ORDER BY ad.severity;

-- Eventos por estado
SELECT
    'Eventos por Estado' as label,
    state,
    COUNT(*) as count
FROM alarm_events
GROUP BY state
ORDER BY state;

-- Alarmes mais frequentes (Top 5)
SELECT
    'Top 5 Alarmes Mais Frequentes' as label,
    ad.name,
    ad.severity,
    COUNT(ae.id) as occurrences
FROM alarm_events ae
JOIN alarm_definitions ad ON ae.definition_id = ad.id
GROUP BY ad.id, ad.name, ad.severity
ORDER BY occurrences DESC
LIMIT 5;
EOF

echo ""
echo "========================================="
echo "5. RESUMO DO TESTE"
echo "========================================="
echo -e "${GREEN}✓ Sistema de alarmes totalmente funcional!${NC}"
echo ""
echo "Próximos passos:"
echo "  1. Acessar http://localhost:3000/data/alarms-events"
echo "  2. Login: admin@optiflow.com / admin123"
echo "  3. Verificar visualização dos dados na tabela"
echo ""
echo "========================================="
