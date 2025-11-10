#!/bin/bash
# Test script showing EXACT values the Autonomous Agent sees
# Format: VARIABLE | VALUE | TIMESTAMP

echo "================================================================================"
echo "🤖 AUTONOMOUS AGENT - Valores em Tempo Real"
echo "================================================================================"
echo ""
echo "Este teste mostra os VALORES EXATOS que o Autonomous Agent está lendo:"
echo "  • VARIÁVEL (tag name)"
echo "  • VALOR ATUAL (no momento da consulta)"
echo "  • TIMESTAMP (quando o valor foi gerado)"
echo ""
echo "================================================================================"
echo ""

# Lista de tags do simulador
TAGS=(
    "TEST_COUNTER_PV"
    "SYSTEM_RUNNING_PV"
    "WAREHOUSE_LEVEL_PCT_PV"
    "TOTAL_MASS_T_PV"
    "TOTAL_KWH_PV"
    "ARZ_GATES_GATE01_POSICAO_PV"
    "ARZ_GATES_GATE01_VAZAO_TPH_PV"
    "ARZ_GATES_GATE02_POSICAO_PV"
    "ARZ_GATES_GATE02_VAZAO_TPH_PV"
    "ARZ_GATES_GATE03_POSICAO_PV"
    "ARZ_GATES_GATE03_VAZAO_TPH_PV"
    "ARZ_GATES_GATE04_POSICAO_PV"
    "ARZ_GATES_GATE04_VAZAO_TPH_PV"
)

echo "📡 Consultando InfluxDB (fonte de dados do Agent)..."
echo ""
printf "%-45s | %-15s | %-30s | %s\n" "VARIÁVEL" "VALOR" "TIMESTAMP" "QUALIDADE"
echo "--------------------------------------------------------------------------------"

SUCCESS=0
NO_DATA=0

# Captura o tempo de início do teste
TEST_START=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

for TAG_NAME in "${TAGS[@]}"; do
    # Consulta a API (mesmo método que o agent usa internamente)
    RESPONSE=$(timeout 5 curl -s "http://localhost:8000/api/v1/tags/realtime/$TAG_NAME" 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        # Parse JSON response
        VALUE=$(echo "$RESPONSE" | grep -o '"value":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' ')
        TIMESTAMP=$(echo "$RESPONSE" | grep -o '"timestamp":"[^"]*"' | head -1 | cut -d'"' -f4)
        QUALITY=$(echo "$RESPONSE" | grep -o '"quality":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [ -n "$VALUE" ]; then
            SUCCESS=$((SUCCESS + 1))

            # Formata timestamp (remove microsegundos para facilitar leitura)
            TIMESTAMP_FORMATTED=$(echo "$TIMESTAMP" | cut -d'.' -f1 | sed 's/T/ /' | sed 's/Z/ UTC/')

            # Formata valor com 2 casas decimais
            VALUE_FORMATTED=$(printf "%.2f" "$VALUE" 2>/dev/null || echo "$VALUE")

            printf "%-45s | %15s | %-30s | %s\n" "$TAG_NAME" "$VALUE_FORMATTED" "$TIMESTAMP_FORMATTED" "$QUALITY"
        else
            NO_DATA=$((NO_DATA + 1))
            printf "%-45s | %15s | %-30s | %s\n" "$TAG_NAME" "NO DATA" "-" "-"
        fi
    else
        NO_DATA=$((NO_DATA + 1))
        printf "%-45s | %15s | %-30s | %s\n" "$TAG_NAME" "TIMEOUT/ERROR" "-" "-"
    fi
done

echo "--------------------------------------------------------------------------------"
echo ""
echo "📊 RESUMO DA COLETA"
echo "--------------------------------------------------------------------------------"
echo "Tempo do teste:          $TEST_START"
echo "Total de variáveis:      ${#TAGS[@]}"
echo "✅ Valores lidos:        $SUCCESS"
echo "⚠️  Sem dados:           $NO_DATA"
echo ""

if [ $SUCCESS -gt 0 ]; then
    echo "================================================================================"
    echo "🤖 O QUE O AGENT FAZ COM ESSES VALORES"
    echo "================================================================================"
    echo ""
    echo "O Autonomous Agent usa esses valores EXATOS (variável + valor + timestamp) para:"
    echo ""
    echo "  1. 🔍 Detectar Anomalias"
    echo "     Exemplo: Se TEST_COUNTER_PV = 15 (esperado: 0-10)"
    echo "     → Gera insight: 'Anomalia detectada em TEST_COUNTER_PV'"
    echo ""
    echo "  2. 📊 Analisar Performance"
    echo "     Exemplo: Se TOTAL_MASS_T_PV aumentou 1000t em 1 hora"
    echo "     → Calcula: Taxa de carregamento = 1000 t/h"
    echo ""
    echo "  3. ⚠️  Verificar Alarmes"
    echo "     Exemplo: Se WAREHOUSE_LEVEL_PCT_PV > 90%"
    echo "     → Gera alarme: 'Nível crítico do armazém'"
    echo ""
    echo "  4. 💚 Monitorar Saúde de Ativos"
    echo "     Exemplo: Se GATE01_VAZAO_TPH_PV está declinando"
    echo "     → Insight: 'Possível obstrução na comporta 1'"
    echo ""
    echo "  5. ⚡ Identificar Otimizações"
    echo "     Exemplo: Se GATE01_POSICAO=30% e GATE02_POSICAO=80%"
    echo "     → Sugestão: 'Balancear abertura das comportas'"
    echo ""
    echo "  6. 🔮 Prever Estados Futuros"
    echo "     Exemplo: Baseado na tendência de WAREHOUSE_LEVEL_PCT_PV"
    echo "     → Previsão: 'Armazém cheio em 2 horas'"
    echo ""
    echo "================================================================================"
    echo ""

    # Mostra os últimos insights gerados pelo agent
    echo "📈 ÚLTIMOS INSIGHTS GERADOS PELO AGENT"
    echo "--------------------------------------------------------------------------------"
    INSIGHTS=$(docker logs optiflow-backend 2>&1 | grep "Monitoring cycle complete" | tail -3)
    if [ -n "$INSIGHTS" ]; then
        echo "$INSIGHTS"
    else
        echo "Aguardando próximo ciclo de monitoramento (60s)..."
    fi
    echo ""
fi

echo "================================================================================"
echo "✅ TESTE COMPLETO"
echo "================================================================================"
echo ""
echo "Estes são os VALORES REAIS que o Autonomous Agent vê e usa para análise!"
echo ""
