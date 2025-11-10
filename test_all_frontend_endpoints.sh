#!/bin/bash

echo "=========================================="
echo "🧪 Testando TODOS os Endpoints do Frontend"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0

# Get token
echo "1. 🔐 Autenticação..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Falha ao obter token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Token obtido com sucesso${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
  local name=$1
  local endpoint=$2
  local expected_status=${3:-200}

  echo -n "Testing $name... "

  STATUS=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000$endpoint")

  if [ "$STATUS" = "$expected_status" ]; then
    echo -e "${GREEN}✓ $STATUS${NC}"
    ((PASS++))
  else
    echo -e "${RED}✗ $STATUS (esperado $expected_status)${NC}"
    ((FAIL++))
  fi
}

# Test all endpoints used by frontend
echo "2. 📊 Testando Endpoints de Dados..."
echo ""

# Auth endpoints
test_endpoint "Auth /me" "/api/v1/auth/me" 200

# Tags endpoints
test_endpoint "Tags list" "/api/v1/tags/" 200
test_endpoint "Real-time tags" "/api/v1/demo/tags/realtime?limit=10" 200

# Analytics endpoints
test_endpoint "Analytics query" "/api/v1/analytics/query" 200

# AI Insights
test_endpoint "AI Insights autonomous" "/api/v1/ai/insights/autonomous?limit=20" 200
test_endpoint "AI Dashboard summary" "/api/v1/ai/dashboard/summary" 200

# Demo endpoints
test_endpoint "Agent insights" "/api/v1/demo/ai-agent/insights?limit=20" 200
test_endpoint "Tag history" "/api/v1/demo/tags/history?tag_id=test&hours=24" 200

# Alarms endpoints
test_endpoint "Alarms list" "/api/v1/alarms/" 200
test_endpoint "Alarm events" "/api/v1/alarms/events?limit=50" 200

# Quality endpoints (NEW)
test_endpoint "Quality tools" "/api/v1/quality/tools" 200
test_endpoint "Quality Pareto" "/api/v1/quality/pareto?days=7" 200
test_endpoint "Quality summary" "/api/v1/quality/pareto/summary" 200
test_endpoint "Quality insights" "/api/v1/quality/insights/quality?limit=20" 200

# Executive endpoints
test_endpoint "Executive highlights" "/api/v1/executive/highlights/1" 200
test_endpoint "Executive KPI" "/api/v1/executive/kpi-summary/1" 200

# GBM endpoints
test_endpoint "GBM insights overview" "/api/v1/gbm/insights/1/overview" 200

# Historical endpoints
test_endpoint "Historical quick stats" "/api/v1/historical/quick-stats/1" 200

# Assets endpoints
test_endpoint "Assets list" "/api/v1/assets/?limit=10" 200
test_endpoint "Asset tree" "/api/v1/assets/tree" 200

# Operations endpoints
test_endpoint "Truck entries" "/api/v1/operations/trucks?limit=10" 200
test_endpoint "Ship loadings" "/api/v1/operations/ships?limit=10" 200

# Monitoring endpoints
test_endpoint "System health" "/api/v1/monitoring/health" 200
test_endpoint "Monitoring summary" "/api/v1/monitoring/summary" 200

# ML endpoints
test_endpoint "ML insights all" "/api/v1/ml/insights/all?limit=10" 200
test_endpoint "ML models list" "/api/v1/ml/models/list" 200

echo ""
echo "=========================================="
echo "📊 Resumo dos Testes"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Passou: $PASS${NC}"
echo -e "${RED}✗ Falhou: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}🎉 Todos os endpoints estão funcionando!${NC}"
  exit 0
else
  echo -e "${RED}⚠️  Alguns endpoints falharam${NC}"
  exit 1
fi
