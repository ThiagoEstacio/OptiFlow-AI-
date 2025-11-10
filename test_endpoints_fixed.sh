#!/bin/bash

echo "=========================================="
echo "Testing Fixed Endpoints"
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

echo "✓ Token obtained: ${TOKEN:0:30}..."

# Test realtime endpoint
echo ""
echo "2. Testing /tags/realtime endpoint..."
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/tags/realtime \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Realtime endpoint: 200 OK"
  echo "  Response: $(echo $BODY | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"{len(d)} items")' 2>/dev/null || echo 'parsing...')"
else
  echo "✗ Realtime endpoint: $HTTP_CODE"
  echo "  Error: $BODY" | head -3
fi

# Test history endpoint
echo ""
echo "3. Testing /tags/history endpoint..."
RESPONSE=$(curl -s -w "\n%{http_code}" "http://localhost:8000/api/v1/tags/history" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ History endpoint: 200 OK"
  echo "  Response: $(echo $BODY | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"tag: {d.get(\"tag_name\", \"N/A\")}, points: {len(d.get(\"data\", []))}")' 2>/dev/null || echo 'parsing...')"
else
  echo "✗ History endpoint: $HTTP_CODE"
  echo "  Error: $BODY" | head -3
fi

# Test list endpoint
echo ""
echo "4. Testing /tags/list endpoint..."
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/tags/list \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ List endpoint: 200 OK"
  echo "  Response: $(echo $BODY | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"{len(d)} tags")' 2>/dev/null || echo 'parsing...')"
else
  echo "✗ List endpoint: $HTTP_CODE"
  echo "  Error: $BODY" | head -3
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
