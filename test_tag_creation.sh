#!/bin/bash

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@optiflow.com&password=admin123" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

echo "Token: ${TOKEN:0:30}..."

# Test tag creation
echo "Creating test tag..."
curl -v -X POST http://localhost:8000/api/v1/tags/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_tag_001",
    "tag_address": "test_tag_001",
    "description": "Test Tag",
    "unit": "unit",
    "category": "PROCESS",
    "data_type": "FLOAT",
    "is_active": true
  }' 2>&1 | head -100
