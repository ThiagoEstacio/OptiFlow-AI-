#!/bin/bash

echo "=========================================="
echo "Testing Quality Tools Integration"
echo "=========================================="

# Get token
echo ""
echo "1. Getting authentication token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@optiflow.com&password=admin123" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "✗ Failed to get token"
  exit 1
fi

echo "✓ Token obtained"

# Test agent insights
echo ""
echo "2. Fetching Autonomous Agent insights..."
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/demo/ai-agent/insights?limit=10")

echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'✓ Got {len(data)} insights')
        for i, insight in enumerate(data[:5], 1):
            print(f'  {i}. [{insight.get(\"severity\", \"N/A\")}] {insight.get(\"title\", \"No title\")}')
            if 'Pareto' in insight.get('title', '') or 'Variabilidade' in insight.get('title', '') or 'Padrão' in insight.get('title', ''):
                print(f'     🎯 QUALITY INSIGHT DETECTED!')
                print(f'     Category: {insight.get(\"category\", \"N/A\")}')
                if insight.get('recommendations'):
                    print(f'     Recommendations: {len(insight.get(\"recommendations\", []))} actions')
    else:
        print(f'Response: {data}')
except Exception as e:
    print(f'Error parsing response: {e}')
    print(sys.stdin.read())
" <<< "$RESPONSE"

# Test quality-specific insights
echo ""
echo "3. Searching for Pareto insights..."
PARETO_COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        pareto_insights = [i for i in data if 'Pareto' in i.get('title', '')]
        print(len(pareto_insights))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null)

echo "  Found $PARETO_COUNT Pareto insights"

# Test pattern insights
echo ""
echo "4. Searching for Recurring Pattern insights..."
PATTERN_COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        pattern_insights = [i for i in data if 'Padrão' in i.get('title', '') or 'Recorrente' in i.get('title', '')]
        print(len(pattern_insights))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null)

echo "  Found $PATTERN_COUNT Pattern insights"

# Test SPC insights
echo ""
echo "5. Searching for SPC/Variability insights..."
SPC_COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        spc_insights = [i for i in data if 'Variabilidade' in i.get('title', '') or 'SPC' in str(i)]
        print(len(spc_insights))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null)

echo "  Found $SPC_COUNT SPC/Variability insights"

# Summary
echo ""
echo "=========================================="
echo "Quality Tools Integration Summary"
echo "=========================================="
echo "Total insights: $(echo "$RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)) if isinstance(json.load(sys.stdin), list) else 0)" 2>/dev/null || echo "0")"
echo "Pareto insights: $PARETO_COUNT"
echo "Pattern insights: $PATTERN_COUNT"
echo "SPC insights: $SPC_COUNT"
TOTAL_QUALITY=$((PARETO_COUNT + PATTERN_COUNT + SPC_COUNT))
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total Quality Insights: $TOTAL_QUALITY"
echo ""

if [ $TOTAL_QUALITY -gt 0 ]; then
  echo "✅ Quality tools are working!"
  echo ""
  echo "To view in browser:"
  echo "  http://localhost:3000/data/alarms-events"
else
  echo "⚠️  No quality insights found yet."
  echo ""
  echo "This is expected if:"
  echo "  - Agent just started (wait 1-2 monitoring cycles)"
  echo "  - No failure data in database"
  echo "  - InfluxDB not populated with time series data"
  echo ""
  echo "The agent will generate insights once data is available."
fi

echo "=========================================="
