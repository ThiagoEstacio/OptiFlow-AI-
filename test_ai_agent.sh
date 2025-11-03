#!/bin/bash
# Test script for AI Dashboard Assistant

echo "=== Teste do AI Dashboard Assistant ==="
echo ""

echo "1️⃣ Verificando health do agente..."
curl -s http://localhost:8000/api/v1/agent/health | python3 -m json.tool
echo ""
echo ""

echo "2️⃣ Testando criação de widget via comando natural..."
echo "Comando: 'Crie um gauge de temperatura'"
echo ""

curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crie um gauge de temperatura",
    "available_tags": [
      {"id": "temp_01", "name": "Temperature Sensor 1", "description": "Sensor de temperatura principal"},
      {"id": "press_01", "name": "Pressure Sensor 1", "description": "Sensor de pressão da linha 1"}
    ],
    "current_widgets": []
  }' | python3 -m json.tool

echo ""
echo ""

echo "3️⃣ Testando comando mais complexo..."
echo "Comando: 'Adicione um gráfico mostrando pressão nas últimas 24 horas'"
echo ""

curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Adicione um gráfico mostrando pressão nas últimas 24 horas",
    "available_tags": [
      {"id": "press_01", "name": "Pressure Sensor 1", "description": "Sensor de pressão da linha 1"}
    ],
    "current_widgets": [
      {"type": "gauge", "title": "Temperature"}
    ]
  }' | python3 -m json.tool

echo ""
echo "=== Teste Concluído ==="
