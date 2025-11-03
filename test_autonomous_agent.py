#!/usr/bin/env python3
"""
Test Autonomous Agent - Validation Script
Tests if the Autonomous Agent can initialize and run without errors
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_autonomous_agent():
    """Test the autonomous agent initialization and basic functionality"""

    print("=" * 70)
    print("🤖 AUTONOMOUS AGENT - TESTE DE VALIDAÇÃO")
    print("=" * 70)
    print()

    try:
        # Test 1: Import modules
        print("[TEST 1] Importando módulos...")
        from app.services.autonomous_agent import AutonomousAgent, AutonomousInsight, init_autonomous_agent
        from app.services.agent_tools import AgentToolkit
        from app.services.data_service import DataService
        print("✅ Todos os módulos importados com sucesso")
        print()

        # Test 2: Create agent instance
        print("[TEST 2] Criando instância do Autonomous Agent...")
        agent = AutonomousAgent()
        print(f"✅ Agent criado: {agent}")
        print(f"   - Max insights: {agent.max_insights}")
        print(f"   - Monitoring interval: {agent.monitoring_interval}s")
        print(f"   - Is running: {agent.is_running}")
        print()

        # Test 3: Verify agent attributes
        print("[TEST 3] Verificando atributos do agent...")
        assert hasattr(agent, 'insights'), "Agent deve ter atributo 'insights'"
        assert hasattr(agent, 'max_insights'), "Agent deve ter atributo 'max_insights'"
        assert hasattr(agent, 'monitoring_interval'), "Agent deve ter atributo 'monitoring_interval'"
        assert hasattr(agent, 'is_running'), "Agent deve ter atributo 'is_running'"
        assert hasattr(agent, 'start'), "Agent deve ter método 'start'"
        assert hasattr(agent, 'stop'), "Agent deve ter método 'stop'"
        print("✅ Todos os atributos presentes")
        print()

        # Test 4: Verify monitoring methods
        print("[TEST 4] Verificando métodos de monitoramento...")
        assert hasattr(agent, 'detect_anomalies'), "Agent deve ter método 'detect_anomalies'"
        assert hasattr(agent, 'analyze_performance'), "Agent deve ter método 'analyze_performance'"
        assert hasattr(agent, 'check_alarm_conditions'), "Agent deve ter método 'check_alarm_conditions'"
        assert hasattr(agent, 'identify_optimization_opportunities'), "Agent deve ter método 'identify_optimization_opportunities'"
        assert hasattr(agent, 'predict_future_states'), "Agent deve ter método 'predict_future_states'"
        print("✅ Todos os 5 métodos de monitoramento presentes")
        print()

        # Test 5: Test helper methods
        print("[TEST 5] Testando métodos auxiliares...")
        assert hasattr(agent, 'add_insight'), "Agent deve ter método 'add_insight'"
        assert hasattr(agent, 'get_insights'), "Agent deve ter método 'get_insights'"
        assert hasattr(agent, 'get_dashboard_summary'), "Agent deve ter método 'get_dashboard_summary'"
        print("✅ Métodos auxiliares presentes")
        print()

        # Test 6: Test insight creation
        print("[TEST 6] Testando criação de insights...")
        from datetime import datetime
        test_insight = AutonomousInsight(
            insight_id="test_001",
            title="Test Insight",
            description="Testing insight creation",
            category="test",
            severity="info",
            tags=["test_tag"],
            metrics={"test_value": 123},
            recommendations=["Test recommendation"],
            timestamp=datetime.now()
        )
        agent.add_insight(test_insight)
        assert len(agent.insights) == 1, "Deve ter 1 insight após adicionar"
        print("✅ Insight criado e adicionado com sucesso")
        print(f"   - Total insights: {len(agent.insights)}")
        print()

        # Test 7: Test get_insights
        print("[TEST 7] Testando recuperação de insights...")
        insights = agent.get_insights(limit=10)
        assert len(insights) == 1, "Deve retornar 1 insight"
        assert insights[0]['title'] == "Test Insight", "Título deve estar correto"
        print("✅ Insights recuperados corretamente")
        print(f"   - Insight: {insights[0]['title']}")
        print()

        # Test 8: Test dashboard summary
        print("[TEST 8] Testando dashboard summary...")
        summary = agent.get_dashboard_summary()
        assert 'total_insights' in summary, "Summary deve ter total_insights"
        assert 'by_category' in summary, "Summary deve ter by_category"
        assert 'by_severity' in summary, "Summary deve ter by_severity"
        assert 'monitoring_active' in summary, "Summary deve ter monitoring_active"
        assert summary['total_insights'] == 1, "Deve ter 1 insight total"
        print("✅ Dashboard summary funcionando")
        print(f"   - Total insights: {summary['total_insights']}")
        print(f"   - By category: {summary['by_category']}")
        print(f"   - By severity: {summary['by_severity']}")
        print()

        # Test 9: Test stop method
        print("[TEST 9] Testando método stop...")
        agent.is_running = True  # Simulate running
        agent.stop()
        assert agent.is_running == False, "Agent deve parar após chamar stop()"
        print("✅ Método stop funcionando")
        print()

        # Test 10: Check if agent can be initialized (without actually starting the loop)
        print("[TEST 10] Verificando init_autonomous_agent...")
        # We can't actually start it without a database, but we can verify the function exists
        assert callable(init_autonomous_agent), "init_autonomous_agent deve ser callable"
        print("✅ Função init_autonomous_agent disponível")
        print()

        # Test 11: Verify agent methods are async
        print("[TEST 11] Verificando que métodos críticos são async...")
        import inspect
        assert inspect.iscoroutinefunction(agent.start), "start deve ser async"
        assert inspect.iscoroutinefunction(agent.detect_anomalies), "detect_anomalies deve ser async"
        assert inspect.iscoroutinefunction(agent.analyze_performance), "analyze_performance deve ser async"
        print("✅ Métodos assíncronos confirmados")
        print()

        # Test 12: Test AgentToolkit exists
        print("[TEST 12] Verificando AgentToolkit...")
        assert AgentToolkit, "AgentToolkit deve existir"
        print("✅ AgentToolkit disponível")
        print()

        # Test 13: Test DataService exists
        print("[TEST 13] Verificando DataService...")
        assert DataService, "DataService deve existir"
        print("✅ DataService disponível")
        print()

        print("=" * 70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print()
        print("📊 RESULTADO FINAL:")
        print(f"   ✅ 13/13 testes passados (100%)")
        print(f"   ✅ Autonomous Agent estruturalmente correto")
        print(f"   ✅ Todos os métodos presentes")
        print(f"   ✅ Insights funcionando")
        print(f"   ✅ Dashboard summary funcionando")
        print()
        print("⚠️  NOTA: Testes estruturais concluídos com sucesso!")
        print("   Para teste completo end-to-end, o agent precisa de:")
        print("   - Banco de dados PostgreSQL conectado")
        print("   - Tags cadastradas no sistema")
        print("   - InfluxDB com dados históricos")
        print()
        print("🚀 O Autonomous Agent está PRONTO para funcionar quando")
        print("   o sistema estiver rodando com docker compose up -d")
        print()

        return True

    except ImportError as e:
        print(f"❌ ERRO DE IMPORT: {e}")
        print(f"   Verifique se todos os módulos estão presentes")
        return False
    except AssertionError as e:
        print(f"❌ FALHA NO TESTE: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_autonomous_agent())

    # Exit with appropriate code
    sys.exit(0 if result else 1)
