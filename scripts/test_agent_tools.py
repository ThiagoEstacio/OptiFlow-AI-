#!/usr/bin/env python3
"""
Script para testar as ferramentas do AI Agent com dados reais do InfluxDB

Testa as principais funções:
1. calculate_statistics - Estatísticas sobre um período
2. detect_anomalies - Detecção de anomalias
3. compare_tags - Comparação entre tags
4. get_historical_data - Dados históricos
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.data_service import DataService
from backend.app.core.config import settings
from backend.app.db.session import AsyncSessionLocal


async def test_calculate_statistics():
    """Teste 1: Calcular estatísticas de temperatura do ELEV01"""
    print("\n" + "="*80)
    print("  TESTE 1: calculate_statistics")
    print("="*80)
    print("📊 Calculando estatísticas de temperatura do ELEV01 (últimas 24h)...\n")
    
    async with AsyncSessionLocal() as db:
        data_service = DataService(db=db)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = await data_service.calculate_statistics(
            tag_id="ELEV01_TEMP_C_PV",
            start_time=start_time,
            end_time=end_time
        )
    
    if result and "error" not in result:
        print(f"✅ Sucesso!")
        print(f"   📈 Média: {result['mean']:.2f}°C")
        print(f"   🔺 Máximo: {result['max']:.2f}°C")
        print(f"   🔻 Mínimo: {result['min']:.2f}°C")
        print(f"   📊 Desvio Padrão: {result['stddev']:.2f}°C")
        print(f"   🔢 Total de Amostras: {result['count']}")
    else:
        print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
    
    return result


async def test_detect_anomalies():
    """Teste 2: Detectar anomalias na corrente do ELEV01"""
    print("\n" + "="*80)
    print("  TESTE 2: detect_anomalies")
    print("="*80)
    print("🔍 Detectando anomalias na corrente do ELEV01 (últimas 24h)...\n")
    
    async with AsyncSessionLocal() as db:
        data_service = DataService(db=db)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = await data_service.detect_anomalies(
            tag_id="ELEV01_CURRENT_A_PV",
            start_time=start_time,
            end_time=end_time,
            threshold=2.0  # Z-score threshold
        )
    
    if result and "error" not in result:
        print(f"✅ Sucesso!")
        print(f"   🎯 Total de Amostras: {result['total_points']}")
        print(f"   ⚠️  Anomalias Detectadas: {result['anomaly_count']}")
        print(f"   📊 Percentual: {result['anomaly_percentage']:.2f}%")
        
        if result['anomalies']:
            print(f"\n   🔴 Primeiras 5 anomalias:")
            for anomaly in result['anomalies'][:5]:
                print(f"      • {anomaly['timestamp']}: {anomaly['value']:.2f}A (Z-score: {anomaly['z_score']:.2f})")
    else:
        print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
    
    return result


async def test_compare_tags():
    """Teste 3: Comparar ELEV01 com ELEV02"""
    print("\n" + "="*80)
    print("  TESTE 3: compare_tags")
    print("="*80)
    print("⚖️  Comparando ELEV01 vs ELEV02 - Temperatura (últimas 12h)...\n")
    
    async with AsyncSessionLocal() as db:
        data_service = DataService(db=db)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=12)
        
        result = await data_service.compare_tags(
            tag_ids=["ELEV01_TEMP_C_PV", "ELEV02_TEMP_C_PV"],
            start_time=start_time,
            end_time=end_time
        )
    
    if result and "error" not in result:
        print(f"✅ Sucesso!")
        print(f"   📊 Tags comparadas: {len(result['statistics'])}")
        
        for tag_id, stats in result['statistics'].items():
            print(f"\n   🏷️  {tag_id}:")
            print(f"      • Média: {stats['mean']:.2f}°C")
            print(f"      • Máximo: {stats['max']:.2f}°C")
            print(f"      • Mínimo: {stats['min']:.2f}°C")
            print(f"      • Desvio: {stats['stddev']:.2f}°C")
        
        if "correlation" in result:
            print(f"\n   🔗 Correlação: {result['correlation']:.3f}")
    else:
        print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
    
    return result


async def test_historical_data():
    """Teste 4: Obter dados históricos da vibração"""
    print("\n" + "="*80)
    print("  TESTE 4: get_historical_data")
    print("="*80)
    print("📈 Obtendo dados históricos de vibração do ELEV01 (últimas 6h)...\n")
    
    async with AsyncSessionLocal() as db:
        data_service = DataService(db=db)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=6)
        
        result = await data_service.get_historical_data(
            tag_id="ELEV01_VIBRATION_MM_S",
            start_time=start_time,
            end_time=end_time
        )
    
    if result and "error" not in result:
        print(f"✅ Sucesso!")
        print(f"   🔢 Total de pontos: {len(result['data'])}")
        
        if result['data']:
            print(f"\n   📊 Primeiros 5 pontos:")
            for point in result['data'][:5]:
                print(f"      • {point['timestamp']}: {point['value']:.2f} mm/s")
            
            print(f"\n   📊 Últimos 3 pontos:")
            for point in result['data'][-3:]:
                print(f"      • {point['timestamp']}: {point['value']:.2f} mm/s")
    else:
        print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
    
    return result


async def main():
    """Executar todos os testes"""
    print("\n" + "="*80)
    print("  🧪 TESTE DAS FERRAMENTAS DO AI AGENT")
    print("  Testando com dados reais do InfluxDB")
    print("="*80)
    
    # Execute tests
    test1 = await test_calculate_statistics()
    test2 = await test_detect_anomalies()
    test3 = await test_compare_tags()
    test4 = await test_historical_data()
    
    # Summary
    print("\n" + "="*80)
    print("  📋 RESUMO DOS TESTES")
    print("="*80)
    
    tests = [
        ("calculate_statistics", test1),
        ("detect_anomalies", test2),
        ("compare_tags", test3),
        ("get_historical_data", test4)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result and "error" not in result:
            print(f"   ✅ {test_name}: PASSOU")
            passed += 1
        else:
            print(f"   ❌ {test_name}: FALHOU")
            failed += 1
    
    print(f"\n   📊 Total: {passed + failed} testes")
    print(f"   ✅ Passaram: {passed}")
    print(f"   ❌ Falharam: {failed}")
    
    if failed == 0:
        print("\n   🎉 Todos os testes passaram! O Agent está 100% funcional.")
    else:
        print(f"\n   ⚠️  {failed} teste(s) falharam. Verifique as configurações.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
