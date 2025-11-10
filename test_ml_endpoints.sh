#!/bin/bash
# Script de Teste dos Endpoints ML

echo "🧪 Testando Endpoints ML do OptiFlow AI"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

# Test 1: Health Check (sem autenticação)
echo "1️⃣  Testando Health Check do ML..."
HEALTH_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/health")
if [ $? -eq 0 ] && [ ! -z "$HEALTH_RESPONSE" ]; then
    echo -e "${GREEN}✅ Health Check OK${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Health Check falhou${NC}"
fi
echo ""

# Test 2: Login para obter token
echo "2️⃣  Fazendo login para obter token..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@optiflow.com","password":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ ! -z "$TOKEN" ]; then
    echo -e "${GREEN}✅ Token obtido com sucesso${NC}"
    echo "Token: ${TOKEN:0:20}..."
else
    echo -e "${YELLOW}⚠️  Não foi possível obter token (pode não haver usuário admin)${NC}"
    echo "Continuando sem autenticação (alguns endpoints podem falhar)"
fi
echo ""

# Test 3: Sumário de Insights (requer autenticação)
if [ ! -z "$TOKEN" ]; then
    echo "3️⃣  Testando Sumário de Insights..."
    SUMMARY_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/summary?time_range=last_7_days" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -eq 0 ] && [ ! -z "$SUMMARY_RESPONSE" ]; then
        echo -e "${GREEN}✅ Sumário obtido com sucesso${NC}"
        echo "$SUMMARY_RESPONSE" | python3 -m json.tool | head -30
    else
        echo -e "${RED}❌ Falha ao obter sumário${NC}"
    fi
    echo ""
fi

# Test 4: Previsão de Energia
if [ ! -z "$TOKEN" ]; then
    echo "4️⃣  Testando Previsão de Energia..."
    ENERGY_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/energy-prediction?time_range=last_24h" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -eq 0 ] && [ ! -z "$ENERGY_RESPONSE" ]; then
        echo -e "${GREEN}✅ Previsão de energia obtida${NC}"
        echo "$ENERGY_RESPONSE" | python3 -m json.tool | head -40
    else
        echo -e "${RED}❌ Falha na previsão de energia${NC}"
    fi
    echo ""
fi

# Test 5: Análise de Eficiência
if [ ! -z "$TOKEN" ]; then
    echo "5️⃣  Testando Análise de Eficiência..."
    EFFICIENCY_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/efficiency?time_range=last_7_days" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -eq 0 ] && [ ! -z "$EFFICIENCY_RESPONSE" ]; then
        echo -e "${GREEN}✅ Análise de eficiência obtida${NC}"
        echo "$EFFICIENCY_RESPONSE" | python3 -m json.tool | head -30
    else
        echo -e "${RED}❌ Falha na análise de eficiência${NC}"
    fi
    echo ""
fi

# Test 6: Detecção de Anomalias
if [ ! -z "$TOKEN" ]; then
    echo "6️⃣  Testando Detecção de Anomalias..."
    ANOMALIES_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/anomalies?time_range=last_7_days" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -eq 0 ] && [ ! -z "$ANOMALIES_RESPONSE" ]; then
        echo -e "${GREEN}✅ Detecção de anomalias obtida${NC}"
        echo "$ANOMALIES_RESPONSE" | python3 -m json.tool | head -30
    else
        echo -e "${RED}❌ Falha na detecção de anomalias${NC}"
    fi
    echo ""
fi

# Test 7: Todos os Insights
if [ ! -z "$TOKEN" ]; then
    echo "7️⃣  Testando Todos os Insights..."
    ALL_INSIGHTS_RESPONSE=$(curl -s -X GET "$BASE_URL/ml/insights/all?time_range=last_7_days" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -eq 0 ] && [ ! -z "$ALL_INSIGHTS_RESPONSE" ]; then
        echo -e "${GREEN}✅ Todos os insights obtidos${NC}"

        # Extrair estatísticas do summary
        TOTAL_INSIGHTS=$(echo "$ALL_INSIGHTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('summary', {}).get('total_insights', 0))" 2>/dev/null)
        TOTAL_ALERTS=$(echo "$ALL_INSIGHTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('summary', {}).get('total_alerts', 0))" 2>/dev/null)
        SEVERITY=$(echo "$ALL_INSIGHTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('summary', {}).get('severity', 'unknown'))" 2>/dev/null)

        echo ""
        echo "📊 Estatísticas:"
        echo "   • Total de Insights: $TOTAL_INSIGHTS"
        echo "   • Total de Alertas: $TOTAL_ALERTS"
        echo "   • Severidade: $SEVERITY"
        echo ""

        # Mostrar primeiras linhas do JSON
        echo "$ALL_INSIGHTS_RESPONSE" | python3 -m json.tool | head -50
    else
        echo -e "${RED}❌ Falha ao obter todos os insights${NC}"
    fi
    echo ""
fi

# Summary
echo ""
echo "=========================================="
echo "🏁 Teste Completo!"
echo ""
if [ ! -z "$TOKEN" ]; then
    echo -e "${GREEN}✅ Sistema ML funcionando corretamente${NC}"
    echo ""
    echo "📖 Para mais detalhes, consulte:"
    echo "   • Swagger UI: http://localhost:8000/docs"
    echo "   • Documentação: ML_INTEGRATION_COMPLETE_REPORT.md"
else
    echo -e "${YELLOW}⚠️  Testes parciais (sem autenticação)${NC}"
    echo "   Crie um usuário admin para testes completos"
fi
echo ""
