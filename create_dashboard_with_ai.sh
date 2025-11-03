#!/bin/bash
# Script para criar dashboard de demonstração usando AI Agent

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🤖 CRIANDO DASHBOARD COM AI AGENT - DEMONSTRAÇÃO          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Tags disponíveis para o dashboard
TAGS='[
  {"id": "temp_sala_01", "name": "Temperatura Sala Principal", "description": "Sensor de temperatura da sala de produção"},
  {"id": "press_linha_01", "name": "Pressão Linha 1", "description": "Sensor de pressão da linha de produção 1"},
  {"id": "efficiency_prod", "name": "Eficiência Produção", "description": "Percentual de eficiência da produção"},
  {"id": "vibration_motor_01", "name": "Vibração Motor 1", "description": "Nível de vibração do motor principal"},
  {"id": "machine_status", "name": "Status Máquina", "description": "Status operacional da máquina"}
]'

echo "1️⃣ Criando Dashboard de Monitoramento Industrial..."
echo ""

# Comando 1: Criar dashboard completo
echo "📊 Solicitando ao AI Agent: 'Crie um dashboard completo para monitorar uma linha de produção industrial com gauge de temperatura, gráfico de pressão das últimas 24 horas, KPI de eficiência com meta de 85%, indicador de vibração e status da máquina'"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Crie um dashboard completo para monitorar uma linha de produção industrial com gauge de temperatura (0 a 100 graus), gráfico de pressão das últimas 24 horas, KPI de eficiência com meta de 85%, gráfico de vibração e indicador de status da máquina\",
    \"available_tags\": $TAGS,
    \"current_widgets\": []
  }")

echo "✅ Resposta do AI Agent:"
echo "$RESPONSE" | python3 -m json.tool
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extrair widgets criados
WIDGETS_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('widgets', [])))")

echo "📦 Widgets criados: $WIDGETS_COUNT"
echo ""

# Mostrar cada widget
echo "$RESPONSE" | python3 << 'PYTHON'
import json
import sys

data = json.load(sys.stdin)
widgets = data.get('widgets', [])

print("📋 Detalhes dos Widgets:\n")
for i, widget in enumerate(widgets, 1):
    print(f"{i}. Tipo: {widget['type'].upper()}")
    print(f"   Título: {widget['title']}")
    print(f"   Tag: {widget.get('tagId', 'N/A')}")
    
    config = widget.get('config', {})
    if 'min' in config and 'max' in config:
        print(f"   Range: {config['min']} - {config['max']}")
    if 'unit' in config:
        print(f"   Unidade: {config['unit']}")
    if 'timeRange' in config:
        print(f"   Período: {config['timeRange']}")
    if 'target' in config:
        print(f"   Meta: {config['target']}")
    print()
PYTHON

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Dashboard criado com sucesso!"
echo ""
echo "Para visualizar no frontend:"
echo "1. Acesse: http://localhost:3000/dashboard-builder"
echo "2. Clique no botão 'AI Assistant' (ícone ✨)"
echo "3. Digite o mesmo comando acima"
echo "4. Os widgets serão adicionados automaticamente ao canvas!"
echo ""
echo "╚════════════════════════════════════════════════════════════════╝"
