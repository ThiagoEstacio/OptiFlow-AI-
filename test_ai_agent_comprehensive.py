#!/usr/bin/env python3
"""
AI Agent Test Suite - Comprehensive Widget Testing

Tests all widget types with various scenarios:
- Basic widget creation
- Real-time data integration
- Historical data queries
- Statistical calculations
- Multi-widget dashboards
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuration
API_BASE = "http://localhost:8000/api/v1/agent"
COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "reset": "\033[0m"
}

def print_color(text: str, color: str):
    """Print colored text"""
    print(f"{COLORS.get(color, '')}{text}{COLORS['reset']}")

def print_test_header(test_name: str):
    """Print test header"""
    print("\n" + "=" * 80)
    print_color(f"  TEST: {test_name}", "blue")
    print("=" * 80)

def send_message(message: str, available_tags: List[Dict] = None) -> Dict[str, Any]:
    """Send message to AI agent"""
    payload = {
        "message": message,
        "available_tags": available_tags or []
    }
    
    print_color(f"\n→ User: {message}", "yellow")
    
    try:
        response = requests.post(
            f"{API_BASE}/dashboard/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_color(f"← Agent: {data.get('response', 'No response')}", "green")
            
            if data.get('widgets'):
                print_color(f"   Widgets created: {len(data['widgets'])}", "green")
                for idx, widget in enumerate(data['widgets'], 1):
                    print(f"     {idx}. {widget.get('type')} - {widget.get('title')}")
            
            return data
        else:
            print_color(f"✗ Error: {response.status_code} - {response.text}", "red")
            return {}
            
    except Exception as e:
        print_color(f"✗ Exception: {str(e)}", "red")
        return {}

def check_health() -> bool:
    """Check if AI agent is healthy"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_color("✓ Agent is healthy", "green")
            print(f"  Ollama: {data.get('ollama_available')}")
            print(f"  Model loaded: {data.get('model_loaded')}")
            return data.get('status') == 'healthy'
        return False
    except:
        print_color("✗ Agent is not responding", "red")
        return False

# Sample tags for testing
SAMPLE_TAGS = [
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
    },
    {
        "name": "ARZ_VIBR01_EIXO_X_PV",
        "description": "Vibração no eixo X",
        "unit": "mm/s",
        "min_value": 0,
        "max_value": 20
    },
    {
        "name": "ARZ_VIBR01_EIXO_Y_PV",
        "description": "Vibração no eixo Y",
        "unit": "mm/s",
        "min_value": 0,
        "max_value": 20
    },
    {
        "name": "ARZ_PROD01_EFICIENCIA_PV",
        "description": "Eficiência de produção",
        "unit": "%",
        "min_value": 0,
        "max_value": 100
    },
    {
        "name": "ARZ_PROD01_STATUS_PV",
        "description": "Status da linha de produção",
        "unit": "",
        "min_value": 0,
        "max_value": 3
    }
]

def test_basic_widgets():
    """Test basic widget creation"""
    print_test_header("Basic Widget Creation")
    
    tests = [
        ("Crie um gauge de temperatura de 0 a 100 graus", "gauge"),
        ("Adicione um gráfico de linha mostrando a velocidade", "timeseries"),
        ("Mostre um KPI com a eficiência atual", "value/kpi"),
        ("Crie um indicador de status", "status"),
        ("Adicione uma barra de progresso", "progress"),
    ]
    
    results = []
    for message, expected_type in tests:
        result = send_message(message, SAMPLE_TAGS)
        widgets = result.get('widgets', [])
        success = len(widgets) > 0
        results.append(success)
        time.sleep(1)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def test_chart_widgets():
    """Test chart widget types"""
    print_test_header("Chart Widgets")
    
    tests = [
        "Crie um gráfico de barras comparando as vibrações X e Y",
        "Adicione um gráfico de pizza mostrando distribuição de tempo",
        "Crie um mapa de calor com as temperaturas",
    ]
    
    results = []
    for message in tests:
        result = send_message(message, SAMPLE_TAGS)
        success = len(result.get('widgets', [])) > 0
        results.append(success)
        time.sleep(1)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def test_data_queries():
    """Test data query capabilities"""
    print_test_header("Data Query Capabilities")
    
    tests = [
        "Qual é a temperatura atual do motor?",
        "Mostre a velocidade média nas últimas 24 horas",
        "Qual foi o valor máximo de pressão hoje?",
        "Calcule a média e o desvio padrão da eficiência na última hora",
    ]
    
    results = []
    for message in tests:
        result = send_message(message, SAMPLE_TAGS)
        success = len(result.get('response', '')) > 10  # Has meaningful response
        results.append(success)
        time.sleep(2)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def test_multi_widget():
    """Test creating multiple widgets at once"""
    print_test_header("Multi-Widget Creation")
    
    message = """Crie um dashboard completo com:
- Gauge de temperatura
- Gráfico de velocidade ao longo do tempo
- KPI de eficiência
- Indicador de status
"""
    
    result = send_message(message, SAMPLE_TAGS)
    widgets = result.get('widgets', [])
    success = len(widgets) >= 3
    
    print_color(f"\n✓ Created {len(widgets)} widgets", "green" if success else "yellow")
    return success

def test_contextual_widget():
    """Test creating widgets with context awareness"""
    print_test_header("Contextual Widget Creation")
    
    tests = [
        "Crie um gauge colorido com zonas vermelhas acima de 120",
        "Adicione um gráfico mostrando as últimas 6 horas",
        "Crie uma tabela com todas as vibrações",
    ]
    
    results = []
    for message in tests:
        result = send_message(message, SAMPLE_TAGS)
        widgets = result.get('widgets', [])
        success = len(widgets) > 0
        
        # Check if widget has expected configurations
        if widgets:
            widget = widgets[0]
            if "zona" in message.lower() or "colorid" in message.lower():
                has_thresholds = widget.get('config', {}).get('thresholds') is not None
                success = success and has_thresholds
            elif "últimas 6 horas" in message.lower():
                has_timerange = widget.get('config', {}).get('timeRange') is not None
                success = success and has_timerange
        
        results.append(success)
        time.sleep(1)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def test_tag_search():
    """Test tag search and matching"""
    print_test_header("Tag Search and Matching")
    
    tests = [
        ("Crie um widget para temperatura", "TEMPERATURA"),
        ("Mostre a velocidade", "VELOCIDADE"),
        ("Adicione pressão", "PRES"),
    ]
    
    results = []
    for message, expected_tag_part in tests:
        result = send_message(message, SAMPLE_TAGS)
        widgets = result.get('widgets', [])
        
        if widgets:
            tag_id = widgets[0].get('tagId', '') or ''
            tag_ids = widgets[0].get('tagIds', [])
            all_tags = [tag_id] + tag_ids
            
            found = any(expected_tag_part in tag.upper() for tag in all_tags)
            results.append(found)
        else:
            results.append(False)
        
        time.sleep(1)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def test_calculations():
    """Test calculation capabilities"""
    print_test_header("Statistical Calculations")
    
    tests = [
        "Calcule a média de temperatura nas últimas 24 horas",
        "Qual é o valor máximo e mínimo da pressão hoje?",
        "Mostre estatísticas completas da velocidade na última hora",
    ]
    
    results = []
    for message in tests:
        result = send_message(message, SAMPLE_TAGS)
        response = result.get('response', '').lower()
        
        # Check if response contains statistical terms
        has_stats = any(term in response for term in [
            'média', 'average', 'máximo', 'maximum', 'mínimo', 'minimum',
            'desvio', 'stddev', 'estatística', 'statistics'
        ])
        
        results.append(has_stats or len(result.get('widgets', [])) > 0)
        time.sleep(2)
    
    passed = sum(results)
    print_color(f"\n✓ Passed: {passed}/{len(tests)}", "green" if passed == len(tests) else "yellow")
    return passed == len(tests)

def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("=" * 80)
    print_color("  AI AGENT COMPREHENSIVE TEST SUITE", "blue")
    print("=" * 80)
    
    # Health check
    if not check_health():
        print_color("\n✗ Agent is not healthy. Aborting tests.", "red")
        return False
    
    print("\nStarting tests in 2 seconds...")
    time.sleep(2)
    
    # Run all test suites
    results = {
        "Basic Widgets": test_basic_widgets(),
        "Chart Widgets": test_chart_widgets(),
        "Data Queries": test_data_queries(),
        "Multi-Widget": test_multi_widget(),
        "Contextual Widget": test_contextual_widget(),
        "Tag Search": test_tag_search(),
        "Calculations": test_calculations(),
    }
    
    # Summary
    print("\n")
    print("=" * 80)
    print_color("  TEST SUMMARY", "blue")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "green" if passed else "red"
        print_color(f"{status} - {test_name}", color)
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n")
    print_color(f"Total: {passed}/{total} test suites passed", 
                "green" if passed == total else "yellow")
    
    if passed == total:
        print_color("🎉 All tests passed!", "green")
    else:
        print_color("⚠️  Some tests failed. Check logs above.", "yellow")
    
    print("=" * 80)
    print("\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
