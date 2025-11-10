#!/bin/bash
# Simple test to show agent fetching real-time tag values by name

echo "================================================================================"
echo "🤖 AUTONOMOUS AGENT - Real-Time Value Retrieval Test"
echo "================================================================================"
echo ""
echo "This test simulates exactly what the Autonomous Agent does:"
echo "  1. Auto-discover tags from InfluxDB"
echo "  2. For each tag, fetch the current value by NAME"
echo "  3. Use those values for analysis"
echo ""
echo "================================================================================"
echo ""

# Get current values using batch endpoint (this is what agent uses)
echo "📊 Fetching current values for all simulator tags..."
echo ""

curl -s -X POST "http://localhost:8000/api/v1/tags/realtime/batch" \
  -H "Content-Type: application/json" \
  -d '["TEST_COUNTER_PV", "WAREHOUSE_LEVEL_PCT_PV", "TOTAL_MASS_T_PV", "TOTAL_KWH_PV", "SYSTEM_RUNNING_PV", "ARZ_GATES_GATE01_POSICAO_PV", "ARZ_GATES_GATE01_VAZAO_TPH_PV", "ARZ_GATES_GATE02_POSICAO_PV", "ARZ_GATES_GATE02_VAZAO_TPH_PV"]' \
  | python3 -m json.tool 2>/dev/null || echo "Error fetching values"

echo ""
echo "================================================================================"
echo ""
echo "✅ This is the EXACT data the Autonomous Agent uses for:"
echo ""
echo "  🔍 Anomaly Detection   - Identifies outliers and unusual patterns"
echo "  📊 Performance Analysis - Calculates efficiency and throughput"
echo "  ⚠️  Alarm Checking      - Validates if values exceed thresholds"
echo "  💚 Asset Health        - Monitors degradation and maintenance needs"
echo "  ⚡ Optimization        - Finds opportunities to improve operations"
echo "  🔮 Prediction          - Forecasts future states based on trends"
echo ""
echo "================================================================================"
echo ""
echo "Current Agent Status (from logs):"
docker logs optiflow-backend 2>&1 | grep "Monitoring cycle complete" | tail -1
echo ""
echo "================================================================================"
