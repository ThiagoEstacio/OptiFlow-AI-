#!/bin/bash

echo "=== Testing Authentication ==="

# Step 1: Get token
echo "1. Getting token..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123")

echo "Response: $RESPONSE"

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

echo "Token: $TOKEN"
echo "Token length: ${#TOKEN}"

# Step 2: Test with token
echo ""
echo "2. Testing quality/tools endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/quality/tools | python3 -m json.tool

echo ""
echo "3. Testing health endpoint (no auth)..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "4. Testing quality/pareto endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/quality/pareto?days=7" | python3 -m json.tool
