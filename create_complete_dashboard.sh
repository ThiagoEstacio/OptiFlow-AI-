#!/bin/bash
# Script para criar dashboard completo widget por widget

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🤖 CRIANDO DASHBOARD INDUSTRIAL COM AI AGENT (Passo a Passo) ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

WIDGETS_CREATED="[]"

# Widget 1: Gauge de Temperatura
echo "1️⃣ Criando Gauge de Temperatura..."
W1=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crie um gauge de temperatura com range de 0 a 100 graus",
    "available_tags": [{"id": "temp_sala_01", "name": "Temperatura Sala", "description": "Sensor de temperatura"}],
    "current_widgets": []
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('widgets', [])))")
echo "✅ Gauge criado"
echo ""

# Widget 2: Timeseries de Pressão
echo "2️⃣ Criando Gráfico de Pressão (24h)..."
W2=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Adicione um gráfico de pressão das últimas 24 horas",
    "available_tags": [{"id": "press_linha_01", "name": "Pressão Linha 1", "description": "Sensor de pressão"}],
    "current_widgets": []
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('widgets', [])))")
echo "✅ Gráfico de pressão criado"
echo ""

# Widget 3: KPI de Eficiência
echo "3️⃣ Criando KPI de Eficiência..."
W3=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crie um KPI de eficiência com meta de 85%",
    "available_tags": [{"id": "efficiency_prod", "name": "Eficiência", "description": "Eficiência de produção"}],
    "current_widgets": []
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('widgets', [])))")
echo "✅ KPI criado"
echo ""

# Widget 4: Timeseries de Vibração
echo "4️⃣ Criando Gráfico de Vibração..."
W4=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Adicione um gráfico de vibração das últimas 2 horas",
    "available_tags": [{"id": "vibration_motor", "name": "Vibração Motor", "description": "Nível de vibração"}],
    "current_widgets": []
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('widgets', [])))")
echo "✅ Gráfico de vibração criado"
echo ""

# Widget 5: Status da Máquina
echo "5️⃣ Criando Indicador de Status..."
W5=$(curl -s -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crie um indicador de status da máquina",
    "available_tags": [{"id": "machine_status", "name": "Status Máquina", "description": "Status operacional"}],
    "current_widgets": []
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('widgets', [])))")
echo "✅ Indicador de status criado"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Dashboard Criado com 5 Widgets:"
echo ""

# Consolidar todos os widgets
python3 << PYTHON
import json

w1 = json.loads('$W1')
w2 = json.loads('$W2')
w3 = json.loads('$W3')
w4 = json.loads('$W4')
w5 = json.loads('$W5')

all_widgets = w1 + w2 + w3 + w4 + w5

print(f"Total de widgets: {len(all_widgets)}\n")

for i, widget in enumerate(all_widgets, 1):
    print(f"{i}. 📊 {widget['type'].upper()}: {widget['title']}")
    config = widget.get('config', {})
    details = []
    if 'min' in config and 'max' in config:
        details.append(f"Range: {config['min']}-{config['max']}")
    if 'unit' in config:
        details.append(f"Unit: {config['unit']}")
    if 'timeRange' in config:
        details.append(f"Period: {config['timeRange']}")
    if 'target' in config:
        details.append(f"Target: {config['target']}%")
    
    if details:
        print(f"   {' | '.join(details)}")
    print()

# Salvar configuração do dashboard
dashboard_config = {
    "name": "Dashboard Industrial - Criado com AI",
    "description": "Dashboard de monitoramento de linha de produção criado automaticamente com AI Agent",
    "widgets": all_widgets,
    "created_at": "$(date -Iseconds)",
    "created_by": "AI Agent (Llama 3.1 8B)"
}

with open('/tmp/ai_dashboard_config.json', 'w') as f:
    json.dump(dashboard_config, f, indent=2)

print("💾 Configuração salva em: /tmp/ai_dashboard_config.json")
PYTHON

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 DASHBOARD COMPLETO CRIADO!"
echo ""
echo "Para visualizar no frontend:"
echo "1. Acesse: http://localhost:3000/dashboard-builder"
echo "2. Clique no botão 'AI Assistant' (ícone ✨ gradiente azul/roxo)"
echo "3. Digite comandos como os acima para criar cada widget"
echo "4. Os widgets aparecerão automaticamente no canvas!"
echo ""
echo "📝 Configuração JSON disponível em: /tmp/ai_dashboard_config.json"
echo ""
echo "╚════════════════════════════════════════════════════════════════╝"
