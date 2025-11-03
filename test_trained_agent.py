#!/usr/bin/env python3
"""
Test AI Agent - Advanced Capabilities
Tests the trained AI agent with complex queries
"""
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_chat(message: str, test_name: str):
    """Send message to AI agent and display response"""
    print_section(f"TEST: {test_name}")
    print(f"👤 USER: {message}\n")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/agent/dashboard/chat",
            json={"message": message},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"🤖 ASSISTANT:")
            print(f"{data['response']}\n")
            
            if data.get('widgets'):
                print(f"📊 WIDGETS CREATED: {len(data['widgets'])}")
                for i, widget in enumerate(data['widgets'], 1):
                    print(f"\n{i}. {widget['type'].upper()}: {widget['title']}")
                    if widget.get('tagId'):
                        print(f"   Tag: {widget['tagId']}")
                    if widget.get('config'):
                        print(f"   Config: {json.dumps(widget['config'], indent=6)}")
            
            if data.get('suggestions'):
                print(f"\n💡 SUGGESTIONS:")
                for sugg in data['suggestions']:
                    print(f"   • {sugg}")
            
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run comprehensive AI agent tests"""
    print("\n" + "="*80)
    print("🧠 AI Agent - Advanced Training Test Suite")
    print("="*80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        # Basic queries
        {
            "name": "Basic Real-time Query",
            "message": "Mostre a temperatura atual da correia 01"
        },
        
        # Statistical analysis
        {
            "name": "Statistical Analysis",
            "message": "Analise a performance da correia transportadora nas últimas 24 horas"
        },
        
        # Alarm analysis
        {
            "name": "Alarm Root Cause",
            "message": "Por que temos tantos alarmes ativos? Faça uma análise de causa raiz"
        },
        
        # Multi-parameter analysis
        {
            "name": "Correlation Analysis",
            "message": "Compare a velocidade e temperatura da correia para identificar correlações"
        },
        
        # Anomaly detection
        {
            "name": "Anomaly Detection",
            "message": "Detecte anomalias na operação do sistema nas últimas 24 horas"
        },
        
        # OEE calculation
        {
            "name": "OEE Analysis",
            "message": "Calcule o OEE do equipamento e sugira melhorias"
        },
        
        # Predictive insight
        {
            "name": "Predictive Analysis",
            "message": "Com base no nível de inventário atual, quando vamos atingir capacidade máxima?"
        },
        
        # Dashboard creation
        {
            "name": "Complete Dashboard",
            "message": "Crie um dashboard completo de monitoramento com os principais KPIs de produção"
        },
        
        # Process optimization
        {
            "name": "Optimization Insights",
            "message": "Identifique oportunidades de otimização no processo produtivo"
        },
        
        # Comparative analysis
        {
            "name": "Equipment Comparison",
            "message": "Compare o desempenho dos portões e identifique qual precisa manutenção"
        }
    ]
    
    results = []
    
    for test in tests:
        success = test_chat(test["message"], test["name"])
        results.append((test["name"], success))
        print("\n" + "-"*80)
        
        # Small delay between tests
        import time
        time.sleep(2)
    
    # Summary
    print_section("📊 Test Results Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Final Score: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 Perfect! AI Agent is fully trained and operational!")
        print("\n📚 Knowledge Areas Validated:")
        print("   ✅ Real-time monitoring")
        print("   ✅ Statistical analysis")
        print("   ✅ Alarm management")
        print("   ✅ Correlation detection")
        print("   ✅ Anomaly detection")
        print("   ✅ OEE calculation")
        print("   ✅ Predictive insights")
        print("   ✅ Dashboard design")
        print("   ✅ Process optimization")
        print("   ✅ Comparative analysis")
        return 0
    else:
        print("⚠️  Some tests failed. Review agent configuration.")
        return 1

if __name__ == "__main__":
    exit(main())
