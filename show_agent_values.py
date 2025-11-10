#!/usr/bin/env python3
"""
Script to show EXACT values the Autonomous Agent sees in real-time
Format: VARIABLE | VALUE | TIMESTAMP
"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

# Simular o ambiente do backend
os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://optiflow_user:optiflow_password@db:5432/optiflow_db')
os.environ.setdefault('INFLUXDB_URL', 'http://influxdb:8086')
os.environ.setdefault('INFLUXDB_TOKEN', 'optiflow-dev-token-change-in-production')
os.environ.setdefault('INFLUXDB_ORG', 'optiflow')
os.environ.setdefault('INFLUXDB_BUCKET', 'optiflow')

from app.services.influxdb import influxdb_service
from datetime import datetime

def format_timestamp(ts_str):
    """Format timestamp for display"""
    try:
        # Parse ISO timestamp
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return ts_str[:19].replace('T', ' ')

def main():
    print("=" * 100)
    print("🤖 AUTONOMOUS AGENT - Valores em Tempo Real")
    print("=" * 100)
    print()
    print("Este teste mostra os VALORES EXATOS que o Autonomous Agent está lendo:")
    print("  • VARIÁVEL (tag name)")
    print("  • VALOR ATUAL (no momento da consulta)")
    print("  • TIMESTAMP (quando o valor foi gerado)")
    print()
    print("=" * 100)
    print()

    # Tags do simulador
    tags = [
        "TEST_COUNTER_PV",
        "SYSTEM_RUNNING_PV",
        "WAREHOUSE_LEVEL_PCT_PV",
        "TOTAL_MASS_T_PV",
        "TOTAL_KWH_PV",
        "ARZ_GATES_GATE01_POSICAO_PV",
        "ARZ_GATES_GATE01_VAZAO_TPH_PV",
        "ARZ_GATES_GATE02_POSICAO_PV",
        "ARZ_GATES_GATE02_VAZAO_TPH_PV",
        "ARZ_GATES_GATE03_POSICAO_PV",
        "ARZ_GATES_GATE03_VAZAO_TPH_PV",
        "ARZ_GATES_GATE04_POSICAO_PV",
        "ARZ_GATES_GATE04_VAZAO_TPH_PV",
    ]

    print("📡 Step 1: Auto-discovery (o que o agent faz primeiro)")
    print("-" * 100)
    print()

    # Step 1: Auto-discovery
    try:
        discovered_tags = influxdb_service.list_all_measurements()
        print(f"✅ Descobertas {len(discovered_tags)} tags do InfluxDB")
        print(f"   Primeiras 10: {', '.join(discovered_tags[:10])}")
        if len(discovered_tags) > 10:
            print(f"   ... e mais {len(discovered_tags) - 10} tags")
        print()
    except Exception as e:
        print(f"❌ Erro no auto-discovery: {e}")
        discovered_tags = tags

    print()
    print("📊 Step 2: Busca de valores em tempo real (por nome de tag)")
    print("-" * 100)
    print()
    print(f"{'VARIÁVEL':<45} | {'VALOR':>15} | {'TIMESTAMP':<25} | {'QUALIDADE':<10}")
    print("-" * 100)

    success = 0
    no_data = 0
    values_list = []

    for tag_name in tags:
        try:
            # Este é o MESMO método que o agent usa
            result = influxdb_service.get_latest_value_by_name(tag_name)

            if result:
                success += 1
                value = result['value']
                timestamp = format_timestamp(result['timestamp'])
                quality = result['quality']

                values_list.append({
                    'tag': tag_name,
                    'value': value,
                    'timestamp': timestamp,
                    'quality': quality
                })

                print(f"{tag_name:<45} | {value:>15.2f} | {timestamp:<25} | {quality:<10}")
            else:
                no_data += 1
                print(f"{tag_name:<45} | {'NO DATA':>15} | {'-':<25} | {'-':<10}")

        except Exception as e:
            no_data += 1
            print(f"{tag_name:<45} | {'ERROR':>15} | {'-':<25} | {str(e)[:10]:<10}")

    print("-" * 100)
    print()
    print("📊 RESUMO DA COLETA")
    print("-" * 100)
    print(f"Tempo do teste:          {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total de variáveis:      {len(tags)}")
    print(f"✅ Valores lidos:        {success}")
    print(f"⚠️  Sem dados:           {no_data}")
    print()

    if success > 0:
        print()
        print("=" * 100)
        print("🤖 O QUE O AGENT FAZ COM ESSES VALORES")
        print("=" * 100)
        print()
        print("O Autonomous Agent usa esses valores EXATOS (variável + valor + timestamp) para:")
        print()
        print("  1. 🔍 Detectar Anomalias")
        print("     Exemplo: Se TEST_COUNTER_PV = 15 (esperado: 0-10)")
        print("     → Gera insight: 'Anomalia detectada em TEST_COUNTER_PV'")
        print()
        print("  2. 📊 Analisar Performance")
        print("     Exemplo: Se TOTAL_MASS_T_PV aumentou 1000t em 1 hora")
        print("     → Calcula: Taxa de carregamento = 1000 t/h")
        print()
        print("  3. ⚠️  Verificar Alarmes")
        print("     Exemplo: Se WAREHOUSE_LEVEL_PCT_PV > 90%")
        print("     → Gera alarme: 'Nível crítico do armazém'")
        print()
        print("  4. 💚 Monitorar Saúde de Ativos")
        print("     Exemplo: Se GATE01_VAZAO_TPH_PV está declinando")
        print("     → Insight: 'Possível obstrução na comporta 1'")
        print()
        print("  5. ⚡ Identificar Otimizações")
        print("     Exemplo: Se GATE01_POSICAO=30% e GATE02_POSICAO=80%")
        print("     → Sugestão: 'Balancear abertura das comportas'")
        print()
        print("  6. 🔮 Prever Estados Futuros")
        print("     Exemplo: Baseado na tendência de WAREHOUSE_LEVEL_PCT_PV")
        print("     → Previsão: 'Armazém cheio em 2 horas'")
        print()

        # Mostrar alguns exemplos concretos com os valores reais
        print("=" * 100)
        print("📋 EXEMPLOS CONCRETOS COM OS VALORES ATUAIS")
        print("=" * 100)
        print()

        # Pegar alguns valores interessantes
        for v in values_list[:5]:
            print(f"• {v['tag']}")
            print(f"  Valor atual: {v['value']:.2f}")
            print(f"  Timestamp:   {v['timestamp']}")
            print(f"  Qualidade:   {v['quality']}")
            print()

    print("=" * 100)
    print("✅ TESTE COMPLETO")
    print("=" * 100)
    print()
    print("Estes são os VALORES REAIS que o Autonomous Agent vê e usa para análise!")
    print()


if __name__ == "__main__":
    main()
