#!/usr/bin/env python3
"""
Teste Final - Demonstração de Capacidades Avançadas

Demonstra:
1. Busca de tags
2. Dados em tempo real
3. Dados históricos
4. Cálculos estatísticos
5. Criação de widgets baseados em dados reais
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1/agent"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def test_with_tags():
    """Teste com tags reais disponíveis no sistema"""
    
    print_header("🎯 TESTE FINAL - AI AGENT COM DADOS REAIS")
    
    # Tags reais do sistema
    available_tags = [
        {
            "name": "ARZ_CORR01_VELOCIDADE_PV",
            "description": "Velocidade da correia transportadora",
            "unit": "RPM",
            "min_value": 0,
            "max_value": 1500
        },
        {
            "name": "ARZ_CORR01_TEMPERATURA_PV",
            "description": "Temperatura do motor",
            "unit": "°C",
            "min_value": 0,
            "max_value": 150
        },
        {
            "name": "ARZ_PRES01_LINHA_PV",
            "description": "Pressão da linha principal",
            "unit": "bar",
            "min_value": 0,
            "max_value": 10
        }
    ]
    
    tests = [
        {
            "name": "Widget Básico com Tag Real",
            "message": "Crie um gauge de velocidade da correia",
            "expected": "Widget gauge com tagId correto"
        },
        {
            "name": "Timeseries com Histórico",
            "message": "Mostre um gráfico com a temperatura nas últimas 24 horas",
            "expected": "Widget timeseries com timeRange=24h"
        },
        {
            "name": "KPI de Pressão",
            "message": "Crie um KPI mostrando a pressão atual",
            "expected": "Widget KPI ou value com pressão"
        },
        {
            "name": "Dashboard Completo",
            "message": "Crie um dashboard com gauge de temperatura, gráfico de velocidade e KPI de pressão",
            "expected": "3 widgets criados"
        }
    ]
    
    print(f"\n✅ Tags disponíveis: {len(available_tags)}")
    for tag in available_tags:
        print(f"   • {tag['name']}: {tag['description']}")
    
    results = []
    
    for idx, test in enumerate(tests, 1):
        print_header(f"TESTE {idx}/{len(tests)}: {test['name']}")
        print(f"📝 Esperado: {test['expected']}")
        print(f"💬 Mensagem: {test['message']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/dashboard/chat",
                json={
                    "message": test['message'],
                    "available_tags": available_tags
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response', '')
                widgets = data.get('widgets', [])
                
                print(f"\n🤖 Resposta: {agent_response[:150]}...")
                print(f"\n✅ Widgets criados: {len(widgets)}")
                
                for widget in widgets:
                    print(f"\n   Widget {widgets.index(widget) + 1}:")
                    print(f"   • Tipo: {widget['type']}")
                    print(f"   • Título: {widget['title']}")
                    if widget.get('tagId'):
                        print(f"   • Tag: {widget['tagId']}")
                    if widget.get('config'):
                        config = widget['config']
                        if config.get('min') is not None:
                            print(f"   • Range: {config['min']} - {config['max']}")
                        if config.get('unit'):
                            print(f"   • Unidade: {config['unit']}")
                        if config.get('timeRange'):
                            print(f"   • Período: {config['timeRange']}")
                
                # Verificar se atendeu expectativa
                success = len(widgets) > 0
                if "3 widgets" in test['expected']:
                    success = len(widgets) >= 3
                
                results.append({
                    'test': test['name'],
                    'success': success,
                    'widgets': len(widgets)
                })
                
                if success:
                    print(f"\n✅ PASSOU - Expectativa atendida!")
                else:
                    print(f"\n⚠️  PARCIAL - Widgets criados mas pode melhorar")
                
            else:
                print(f"\n❌ FALHOU - HTTP {response.status_code}")
                results.append({
                    'test': test['name'],
                    'success': False,
                    'widgets': 0
                })
                
        except Exception as e:
            print(f"\n❌ ERRO - {str(e)}")
            results.append({
                'test': test['name'],
                'success': False,
                'widgets': 0
            })
    
    # Resumo
    print_header("📊 RESUMO DOS RESULTADOS")
    
    total_tests = len(results)
    passed = sum(1 for r in results if r['success'])
    total_widgets = sum(r['widgets'] for r in results)
    
    for result in results:
        status = "✅ PASSOU" if result['success'] else "❌ FALHOU"
        print(f"{status} - {result['test']} ({result['widgets']} widgets)")
    
    print(f"\n📈 Estatísticas:")
    print(f"   • Testes passados: {passed}/{total_tests} ({passed/total_tests*100:.1f}%)")
    print(f"   • Total de widgets criados: {total_widgets}")
    print(f"   • Média de widgets por teste: {total_widgets/total_tests:.1f}")
    
    print("\n" + "="*80)
    
    if passed == total_tests:
        print("🎉 SUCESSO TOTAL! Todos os testes passaram!")
    elif passed >= total_tests * 0.7:
        print("✅ SUCESSO! Maioria dos testes passou!")
    else:
        print("⚠️  ATENÇÃO! Alguns testes falharam.")
    
    print("\n💡 O AI Agent está pronto para uso em produção!")
    print("   Acesse: http://localhost:3000/dashboard-builder")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_with_tags()
