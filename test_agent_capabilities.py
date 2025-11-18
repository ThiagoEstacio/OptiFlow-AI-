#!/usr/bin/env python3
"""
Test script to demonstrate AI Agent capabilities for:
- Current values retrieval
- Statistical calculations (mean, max, min)
- Logical operations
- Mathematical analysis
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1/agent/dashboard/chat"

def test_chat(message: str, description: str):
    """Test chat endpoint with a message"""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {description}")
    print(f"{'='*80}")
    print(f"📤 USER: {message}")
    print(f"{'-'*80}")
    
    try:
        response = requests.post(
            BASE_URL,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ STATUS: Success")
            print(f"🤖 ASSISTANT:\n{data.get('response', 'No response')}\n")
            
            # Show widgets if present
            if data.get('widgets'):
                print(f"📊 WIDGETS: {json.dumps(data['widgets'], indent=2)}")
                
            # Show suggestions if present
            if data.get('suggestions'):
                print(f"💡 SUGGESTIONS: {data['suggestions']}")
                
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")


def main():
    """Run all capability tests"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     OPTIFLOW AI AGENT - CAPABILITY TEST                      ║
║                                                                              ║
║  Testing agent's ability to:                                                 ║
║  • Retrieve current/real-time values                                         ║
║  • Calculate statistics (mean, max, min, stddev)                             ║
║  • Perform logical operations                                                ║
║  • Execute mathematical analysis                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Test 1: Current values
    test_chat(
        "Qual o valor atual da temperatura do ELEV01?",
        "Current Value Retrieval"
    )
    
    # Test 2: Multiple current values
    test_chat(
        "Me mostre os valores atuais de temperatura de todos os elevadores",
        "Multiple Real-time Values"
    )
    
    # Test 3: Statistical calculation - Average
    test_chat(
        "Qual foi a temperatura média do ELEV01 nas últimas 24 horas?",
        "Statistical Calculation - Mean"
    )
    
    # Test 4: Statistical calculation - Max/Min
    test_chat(
        "Qual foi a temperatura máxima e mínima do ELEV02 nas últimas 6 horas?",
        "Statistical Calculation - Max/Min"
    )
    
    # Test 5: Comparison and logical operations
    test_chat(
        "Compare a temperatura do ELEV01 com ELEV02 nas últimas 12 horas. Qual teve maior variação?",
        "Comparison & Logical Analysis"
    )
    
    # Test 6: Complex mathematical analysis
    test_chat(
        "Calcule a média, desvio padrão e coeficiente de variação da velocidade do correia ARZ_CORR01 no último dia",
        "Complex Statistical Analysis"
    )
    
    # Test 7: Conditional logic
    test_chat(
        "Me avise se algum equipamento teve temperatura acima de 80°C nas últimas 24h",
        "Conditional Logic & Threshold Detection"
    )
    
    # Test 8: Trend analysis
    test_chat(
        "A temperatura do ELEV01 está aumentando, diminuindo ou estável nas últimas 6 horas?",
        "Trend Analysis & Pattern Recognition"
    )
    
    # Test 9: Anomaly detection
    test_chat(
        "Detecte anomalias na temperatura do ELEV02 nas últimas 24 horas",
        "Anomaly Detection (Statistical)"
    )
    
    # Test 10: Multi-variable correlation
    test_chat(
        "Existe correlação entre temperatura e corrente elétrica do ELEV01?",
        "Multi-variable Correlation Analysis"
    )
    
    print(f"\n{'='*80}")
    print("✅ All tests completed!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
