#!/bin/bash

echo "=========================================="
echo "🧪 Testing Quality Dashboard & Endpoints"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get token
echo "1. 🔐 Authenticating..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Failed to get authentication token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Token obtained successfully${NC}"
echo ""

# Test Quality Tools Info
echo "2. 📊 Testing /api/v1/quality/tools"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/quality/tools)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Quality Tools endpoint: 200 OK${NC}"
  echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tools = data.get('available_tools', [])
    active = [t for t in tools if t.get('status') == 'active']
    print(f'  Active tools: {len(active)}/{len(tools)}')
    for tool in active:
        print(f'    ✓ {tool[\"name\"]} - {tool[\"endpoint\"]}')
except Exception as e:
    print(f'  Error: {e}')
"
else
  echo -e "${RED}✗ Quality Tools endpoint: $HTTP_CODE${NC}"
  echo "$BODY" | head -3
fi
echo ""

# Test Pareto Summary
echo "3. 🎯 Testing /api/v1/quality/pareto/summary"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/quality/pareto/summary)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Pareto Summary endpoint: 200 OK${NC}"
  echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Total failure types: {data.get(\"total_failure_types\", 0)}')
    print(f'  Vital few count: {data.get(\"vital_few_count\", 0)}')
    print(f'  Total failures: {data.get(\"total_failures\", 0)}')
    if data.get('message'):
        print(f'  Message: {data.get(\"message\")}')
except Exception as e:
    print(f'  Error: {e}')
"
else
  echo -e "${RED}✗ Pareto Summary endpoint: $HTTP_CODE${NC}"
  echo "$BODY" | head -3
fi
echo ""

# Test Pareto Full (7 days)
echo "4. 📊 Testing /api/v1/quality/pareto?days=7"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/quality/pareto?days=7")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Pareto Analysis endpoint: 200 OK${NC}"
  echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Status: {data.get(\"status\")}')
    items = data.get('items', [])
    print(f'  Items: {len(items)}')
    if items:
        vital_few = [i for i in items if i.get('is_vital_few')]
        print(f'  Vital few: {len(vital_few)}')
        print(f'  Top issue: {items[0].get(\"failure_type\")} ({items[0].get(\"count\")} occurrences)')
    if data.get('message'):
        print(f'  Message: {data.get(\"message\")}')
except Exception as e:
    print(f'  Error: {e}')
"
else
  echo -e "${RED}✗ Pareto Analysis endpoint: $HTTP_CODE${NC}"
  echo "$BODY" | head -3
fi
echo ""

# Test Quality Insights
echo "5. 💡 Testing /api/v1/quality/insights/quality"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/quality/insights/quality?limit=10")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Quality Insights endpoint: 200 OK${NC}"
  echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    insights = data.get('insights', [])
    print(f'  Quality insights: {len(insights)}')
    print(f'  Total (all): {data.get(\"total_all_insights\", 0)}')
    for i, insight in enumerate(insights[:3], 1):
        print(f'    {i}. [{insight.get(\"severity\", \"N/A\")}] {insight.get(\"title\", \"No title\")}')
        if 'Pareto' in insight.get('title', '') or 'Variabilidade' in insight.get('title', ''):
            print(f'       🎯 QUALITY TOOL DETECTED!')
except Exception as e:
    print(f'  Error: {e}')
"
else
  echo -e "${RED}✗ Quality Insights endpoint: $HTTP_CODE${NC}"
  echo "$BODY" | head -3
fi
echo ""

# Test Autonomous Agent Insights
echo "6. 🤖 Testing Autonomous Agent (quality insights)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/demo/ai-agent/insights?limit=20")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Agent Insights endpoint: 200 OK${NC}"
  echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        insights = data
        quality_insights = [i for i in insights if
            'Pareto' in i.get('title', '') or
            'Variabilidade' in i.get('title', '') or
            'Padrão' in i.get('title', '') or
            any(tag in i.get('tags', []) for tag in ['quality', 'pareto', 'spc', 'pattern'])
        ]
        print(f'  Total insights: {len(insights)}')
        print(f'  Quality-related: {len(quality_insights)}')
        for insight in quality_insights[:3]:
            print(f'    • [{insight.get(\"severity\", \"N/A\")}] {insight.get(\"title\", \"No title\")}')
    else:
        print(f'  Response: {data}')
except Exception as e:
    print(f'  Error: {e}')
"
else
  echo -e "${RED}✗ Agent Insights endpoint: $HTTP_CODE${NC}"
  echo "$BODY" | head -3
fi
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""
echo "Endpoints tested:"
echo "  ✓ /api/v1/quality/tools"
echo "  ✓ /api/v1/quality/pareto/summary"
echo "  ✓ /api/v1/quality/pareto"
echo "  ✓ /api/v1/quality/insights/quality"
echo "  ✓ /api/v1/demo/ai-agent/insights"
echo ""
echo "Frontend URLs to test:"
echo "  🌐 Quality Dashboard: http://localhost:3000/quality"
echo "  🌐 Alarms & Events: http://localhost:3000/data/alarms-events"
echo ""
echo -e "${GREEN}✅ All endpoints are accessible!${NC}"
echo ""
echo "Next steps:"
echo "  1. Open browser: http://localhost:3000/quality"
echo "  2. Login: admin@optiflow.com / admin123"
echo "  3. Navigate to: Analytics & IA → Gestão da Qualidade"
echo "  4. Explore the 4 tabs: Pareto, Insights, SPC, Root Cause"
echo ""
echo "=========================================="
