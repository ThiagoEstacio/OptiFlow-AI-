#!/usr/bin/env python3
"""
Script para testar o AI Agent do OptiFlow através da API HTTP

Testa queries que acionam as ferramentas analíticas do agent.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_agent_query(query: str, description: str):
    """Envia uma query para o agent e exibe o resultado"""
    print("\n" + "="*80)
    print(f"  {description}")
    print("="*80)
    print(f"📝 Query: \"{query}\"\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agent/dashboard/chat",
            json={"message": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resposta recebida ({len(data.get('response', ''))} caracteres):")
            print(f"\n{data.get('response', 'Sem resposta')}\n")
            
            if "tool_calls" in data:
                print(f"🔧 Ferramentas chamadas: {len(data['tool_calls'])}")
                for tool_call in data['tool_calls']:
                    print(f"   • {tool_call.get('name', 'unknown')}")
            
            return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - Agent demorou mais de 30s")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    """Executa bateria de testes"""
    print("\n" + "="*80)
    print("  🧪 TESTES DO AI AGENT - OptiFlow")
    print("  Testando queries que acionam ferramentas analíticas")
    print("="*80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verificar se backend está rodando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está online\n")
        else:
            print("❌ Backend não está respondendo corretamente")
            return
    except:
        print("❌ Backend não está acessível em http://localhost:8000")
        print("   Execute: docker-compose up backend\n")
        return
    
    # Testes
    tests = [
        {
            "query": "Qual foi a temperatura média do ELEV01 nas últimas 24 horas?",
            "description": "TESTE 1: calculate_statistics (temperatura)"
        },
        {
            "query": "Detecte anomalias na corrente do ELEV01 nas últimas 12 horas",
            "description": "TESTE 2: detect_anomalies (corrente)"
        },
        {
            "query": "Compare a temperatura do ELEV01 com o ELEV02 nas últimas 6 horas",
            "description": "TESTE 3: compare_tags (comparação)"
        },
        {
            "query": "Mostre os dados históricos de vibração do ELEV01 nas últimas 3 horas",
            "description": "TESTE 4: get_historical_data (vibração)"
        },
        {
            "query": "Analise o comportamento da velocidade da correia ARZ_CORR01 hoje",
            "description": "TESTE 5: Análise de tendência"
        }
    ]
    
    results = []
    for test in tests:
        success = test_agent_query(test["query"], test["description"])
        results.append((test["description"], success))
    
    # Summary
    print("\n" + "="*80)
    print("  📋 RESUMO DOS TESTES")
    print("="*80 + "\n")
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for description, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"   {status}: {description}")
    
    print(f"\n   📊 Total: {len(results)} testes")
    print(f"   ✅ Passaram: {passed}")
    print(f"   ❌ Falharam: {failed}")
    
    if failed == 0:
        print("\n   🎉 SUCESSO! Todas as ferramentas do Agent estão funcionais!")
        print("   O Qwen 2.5:7B está executando análises matemáticas e estatísticas.")
    else:
        print(f"\n   ⚠️  {failed} teste(s) falharam.")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
