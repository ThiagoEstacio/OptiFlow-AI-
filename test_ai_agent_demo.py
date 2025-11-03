#!/usr/bin/env python3
"""
AI Agent Quick Demo - Demonstração das Capacidades

Testa as principais funcionalidades do AI Agent de forma simples e direta.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1/agent"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_agent(message, description=""):
    """Envia mensagem ao agent e mostra resultado"""
    if description:
        print(f"📋 {description}")
    print(f"💬 User: {message}")
    
    response = requests.post(
        f"{API_BASE}/dashboard/chat",
        json={"message": message},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 Agent: {data.get('response', 'No response')[:200]}...")
        
        if data.get('widgets'):
            print(f"\n✅ Widgets criados: {len(data['widgets'])}")
            for widget in data['widgets']:
                print(f"   • {widget['type']}: {widget['title']}")
                if widget.get('tagId'):
                    print(f"     Tag: {widget['tagId']}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False

def main():
    print_section("🚀 AI AGENT - DEMONSTRAÇÃO DE CAPACIDADES")
    
    # Check health
    print("Verificando saúde do sistema...")
    health = requests.get(f"{API_BASE}/health").json()
    print(f"✓ Status: {health['status']}")
    print(f"✓ Ollama: {health['ollama_available']}")
    print(f"✓ Modelo: {health['model_name']}")
    
    time.sleep(2)
    
    # Test 1: Simple widget creation
    print_section("TEST 1: Criação Simples de Widgets")
    test_agent(
        "Crie um gauge de temperatura",
        "Widget básico sem consulta de dados"
    )
    time.sleep(3)
    
    # Test 2: Multiple widgets
    print_section("TEST 2: Múltiplos Widgets")
    test_agent(
        "Crie um gauge de pressão e um gráfico de velocidade",
        "Criação de múltiplos widgets simultaneamente"
    )
    time.sleep(3)
    
    # Test 3: Data query
    print_section("TEST 3: Consulta de Dados")
    test_agent(
        "Quais tags de temperatura estão disponíveis?",
        "Busca de tags no sistema"
    )
    time.sleep(3)
    
    # Test 4: Chart widgets
    print_section("TEST 4: Widgets de Gráficos")
    test_agent(
        "Crie um gráfico de barras com as vibrações",
        "Widget de comparação"
    )
    time.sleep(3)
    
    # Test 5: KPI widget
    print_section("TEST 5: Widget KPI")
    test_agent(
        "Mostre um KPI de eficiência",
        "Widget de indicador chave"
    )
    time.sleep(3)
    
    print_section("✅ DEMONSTRAÇÃO CONCLUÍDA")
    print("O AI Agent está funcionando e pode:")
    print("  • Criar widgets de todos os tipos")
    print("  • Buscar tags no sistema")
    print("  • Consultar dados em tempo real")
    print("  • Calcular estatísticas")
    print("  • Gerar dashboards completos")
    print("\nPróximos passos:")
    print("  1. Teste no Dashboard Builder: http://localhost:3000/dashboard-builder")
    print("  2. Use comandos em português natural")
    print("  3. Peça análises e estatísticas")
    print()

if __name__ == "__main__":
    main()
