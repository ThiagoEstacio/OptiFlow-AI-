#!/usr/bin/env python3
"""
Teste de ML Insights com dados reais do banco

Este script testa se o ML Insights Service consegue:
1. Buscar dados reais do InfluxDB
2. Buscar dados reais do PostgreSQL
3. Usar fallback para dados sintéticos quando necessário
4. Gerar insights corretamente
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import get_db
from app.services.ml_insights_service import ml_insights_service
from app.services.influxdb import influxdb_service


async def test_influxdb_connection():
    """Testa conexão com InfluxDB e lista tags disponíveis"""
    print("\n" + "=" * 80)
    print("🔍 TESTE 1: Verificando InfluxDB")
    print("=" * 80)

    try:
        # Listar tags disponíveis
        tags = influxdb_service.list_all_measurements()

        if tags:
            print(f"✅ InfluxDB conectado com sucesso")
            print(f"✅ Encontradas {len(tags)} tags")
            print(f"\n📋 Primeiras 10 tags:")
            for tag in tags[:10]:
                print(f"  • {tag}")

            # Tentar buscar dados de uma tag
            if len(tags) > 0:
                test_tag = tags[0]
                print(f"\n🔍 Buscando dados da tag '{test_tag}'...")

                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)

                data = influxdb_service.query_tag_data(
                    tag_id=test_tag,
                    start_time=start_time,
                    end_time=end_time,
                    aggregation='mean',
                    interval='1h'
                )

                if data:
                    print(f"✅ Encontrados {len(data)} pontos de dados")
                    print(f"📊 Amostra:")
                    for point in data[:3]:
                        print(f"  • {point}")
                else:
                    print(f"⚠️  Nenhum dado encontrado para tag '{test_tag}' nos últimos 7 dias")

            return True
        else:
            print("⚠️  Nenhuma tag encontrada no InfluxDB")
            print("   Isso é normal se o sistema está recém-instalado")
            return False

    except Exception as e:
        print(f"❌ Erro ao conectar com InfluxDB: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_postgresql_alarms():
    """Testa busca de alarmes no PostgreSQL"""
    print("\n" + "=" * 80)
    print("🔍 TESTE 2: Verificando PostgreSQL (Alarmes)")
    print("=" * 80)

    try:
        from app.models.alarm import AlarmEvent
        from sqlalchemy import select

        async for db in get_db():
            # Buscar alarmes dos últimos 30 dias
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            query = select(AlarmEvent).where(
                AlarmEvent.timestamp >= start_time,
                AlarmEvent.timestamp <= end_time
            ).limit(10)

            result = await db.execute(query)
            alarms = result.scalars().all()

            if alarms:
                print(f"✅ PostgreSQL conectado com sucesso")
                print(f"✅ Encontrados {len(alarms)} alarmes nos últimos 30 dias")
                print(f"\n📋 Primeiros 3 alarmes:")
                for alarm in alarms[:3]:
                    print(f"  • ID: {alarm.id}, Timestamp: {alarm.timestamp}")
                return True
            else:
                print("⚠️  Nenhum alarme encontrado nos últimos 30 dias")
                print("   Isso é normal se o sistema está recém-instalado")
                return False

            break  # Apenas uma iteração

    except Exception as e:
        print(f"❌ Erro ao buscar alarmes: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ml_insights_with_real_data():
    """Testa geração de insights ML com dados reais"""
    print("\n" + "=" * 80)
    print("🔍 TESTE 3: Gerando Insights ML")
    print("=" * 80)

    try:
        async for db in get_db():
            # Gerar insights para organização de teste
            org_id = "test-org-id"

            print(f"🔄 Gerando insights para organização '{org_id}'...")
            print(f"📅 Período: últimos 7 dias\n")

            insights = await ml_insights_service.generate_all_insights(
                db=db,
                organization_id=org_id,
                time_range='last_7_days'
            )

            # Verificar resultado
            if insights and insights.get('status') == 'success':
                print(f"✅ Insights gerados com sucesso!")
                print(f"\n📊 Sumário:")
                summary = insights.get('summary', {})
                print(f"  • Total de insights: {summary.get('total_insights', 0)}")
                print(f"  • Alertas ativos: {summary.get('total_alerts', 0)}")
                print(f"  • Severidade: {summary.get('severity', 'unknown')}")
                print(f"  • Status: {summary.get('status', 'unknown')}")

                # Verificar cada modelo
                print(f"\n📈 Modelos ML:")
                insights_data = insights.get('insights', {})

                for model_name, model_data in insights_data.items():
                    if model_data and isinstance(model_data, dict):
                        status = model_data.get('status', 'unknown')
                        emoji = "✅" if status == "success" else "❌"
                        print(f"  {emoji} {model_name}: {status}")

                        # Mostrar métricas específicas
                        if model_name == 'energy_prediction' and status == 'success':
                            print(f"      • R²: {model_data.get('r2_score', 0):.4f}")
                            print(f"      • MAPE: {model_data.get('mape', 0):.2f}%")
                        elif model_name == 'efficiency' and status == 'success':
                            print(f"      • R²: {model_data.get('r2_score', 0):.4f}")
                            print(f"      • MAPE: {model_data.get('mape', 0):.2f}%")
                        elif model_name == 'reliability' and status == 'success':
                            print(f"      • MTBF: {model_data.get('mtbf_mean', 0):.1f}h")
                            print(f"      • MTTR: {model_data.get('mttr_mean', 0):.1f}h")
                            print(f"      • Disponibilidade: {model_data.get('availability_percent', 0):.2f}%")

                # Verificar se usou dados reais ou sintéticos
                print(f"\n📋 Origem dos Dados:")
                print(f"  ℹ️  Verifique os logs acima para ver se foram usados dados reais ou sintéticos")

                return True
            else:
                print(f"❌ Falha ao gerar insights")
                print(f"   Status: {insights.get('status')}")
                return False

            break  # Apenas uma iteração

    except Exception as e:
        print(f"❌ Erro ao gerar insights: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Executa todos os testes"""
    print("\n" + "=" * 80)
    print("🚀 TESTE DE ML INSIGHTS COM DADOS REAIS")
    print("=" * 80)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Executar testes
    test_results = {}

    test_results['influxdb'] = await test_influxdb_connection()
    test_results['postgresql'] = await test_postgresql_alarms()
    test_results['ml_insights'] = await test_ml_insights_with_real_data()

    # Sumário final
    print("\n" + "=" * 80)
    print("📊 SUMÁRIO DOS TESTES")
    print("=" * 80)

    for test_name, result in test_results.items():
        emoji = "✅" if result else "⚠️ "
        status = "PASSOU" if result else "AVISO"
        print(f"{emoji} {test_name.upper()}: {status}")

    # Avaliação final
    print("\n" + "=" * 80)
    if all(test_results.values()):
        print("✅ TODOS OS TESTES PASSARAM COM DADOS REAIS")
    elif test_results['ml_insights']:
        print("✅ ML INSIGHTS FUNCIONANDO (com dados sintéticos como fallback)")
        print("ℹ️  Para usar dados reais, popule o InfluxDB com dados de tags")
    else:
        print("❌ ALGUNS TESTES FALHARAM")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
