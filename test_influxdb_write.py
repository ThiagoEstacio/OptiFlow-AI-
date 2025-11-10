#!/usr/bin/env python3
"""
Teste de Validação da Escrita no InfluxDB
=========================================

Valida que:
1. Gateway/Backend estão escrevendo dados no InfluxDB
2. Dados do OPC-UA Server estão sendo armazenados corretamente
3. Queries funcionam corretamente

Autor: Claude Code
Data: 2025-11-10
"""

import asyncio
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import sys

# Configuração do InfluxDB
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "my-super-secret-influxdb-token"
INFLUXDB_ORG = "optiflow"
INFLUXDB_BUCKET = "timeseries"

def test_influxdb_connection():
    """Teste 1: Conexão com InfluxDB"""
    print("=" * 60)
    print("🔌 Teste 1: Conexão com InfluxDB")
    print("=" * 60)

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG,
            timeout=10000
        )

        # Verificar health
        health = client.health()
        print(f"✅ InfluxDB Status: {health.status}")
        print(f"   Version: {health.version}")
        print(f"   Message: {health.message}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False


def test_write_sample_data():
    """Teste 2: Escrever dados de teste"""
    print("\n" + "=" * 60)
    print("✍️  Teste 2: Escrevendo Dados de Teste")
    print("=" * 60)

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )

        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Escrever dados de teste simulando tags OPC-UA
        test_points = [
            {
                "measurement": "opcua_test",
                "tags": {
                    "tag_name": "TEST_TEMPERATURE",
                    "equipment": "TEST_SENSOR_01",
                    "source": "validation_script"
                },
                "fields": {
                    "value": 25.5,
                    "quality": "GOOD"
                },
                "time": datetime.utcnow()
            },
            {
                "measurement": "opcua_test",
                "tags": {
                    "tag_name": "TEST_PRESSURE",
                    "equipment": "TEST_SENSOR_02",
                    "source": "validation_script"
                },
                "fields": {
                    "value": 101.3,
                    "quality": "GOOD"
                },
                "time": datetime.utcnow()
            }
        ]

        write_api.write(bucket=INFLUXDB_BUCKET, record=test_points)
        print(f"✅ Escreveu {len(test_points)} pontos de teste no bucket '{INFLUXDB_BUCKET}'")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao escrever dados: {e}")
        return False


def test_read_data():
    """Teste 3: Ler dados escritos"""
    print("\n" + "=" * 60)
    print("📖 Teste 3: Lendo Dados de Teste")
    print("=" * 60)

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )

        query_api = client.query_api()

        # Query para buscar dados de teste
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "opcua_test")
            |> filter(fn: (r) => r.source == "validation_script")
        '''

        result = query_api.query(query)

        if not result:
            print("⚠️  Nenhum dado encontrado")
            return False

        print(f"✅ Dados encontrados:")
        for table in result:
            for record in table.records:
                print(f"   - {record.values.get('tag_name')}: {record.get_value()} {record.get_field()} @ {record.get_time()}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao ler dados: {e}")
        return False


def test_opcua_data():
    """Teste 4: Verificar dados do OPC-UA Server"""
    print("\n" + "=" * 60)
    print("🏭 Teste 4: Verificando Dados do OPC-UA Server")
    print("=" * 60)

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )

        query_api = client.query_api()

        # Query para buscar dados do OPC-UA
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "opcua_tags" or r._measurement == "raw_tag")
            |> limit(n: 20)
        '''

        result = query_api.query(query)

        if not result or len(result) == 0:
            print("⚠️  Nenhum dado do OPC-UA encontrado no InfluxDB")
            print("   Isso indica que o Gateway/Backend ainda não está escrevendo dados")
            return False

        total_records = sum(len(table.records) for table in result)
        print(f"✅ Encontrados {total_records} registros do OPC-UA:")

        # Mostrar amostra dos dados
        count = 0
        for table in result:
            for record in table.records:
                if count < 10:  # Mostrar apenas 10 primeiros
                    tag_name = record.values.get('tag_name', 'N/A')
                    value = record.get_value()
                    time = record.get_time()
                    print(f"   {count+1}. Tag: {tag_name}, Value: {value}, Time: {time}")
                    count += 1

        if total_records > 10:
            print(f"   ... e mais {total_records - 10} registros")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao verificar dados OPC-UA: {e}")
        return False


def test_data_retention():
    """Teste 5: Verificar retenção de dados"""
    print("\n" + "=" * 60)
    print("⏰ Teste 5: Verificando Retenção de Dados")
    print("=" * 60)

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )

        # Verificar buckets e suas políticas de retenção
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets().buckets

        print("📦 Buckets configurados:")
        for bucket in buckets:
            retention_hours = bucket.retention_rules[0].every_seconds // 3600 if bucket.retention_rules else 0
            if retention_hours == 0:
                retention_str = "Infinito"
            else:
                retention_str = f"{retention_hours} horas ({retention_hours // 24} dias)"

            print(f"   - {bucket.name}: Retenção = {retention_str}")

            if bucket.name == INFLUXDB_BUCKET:
                print(f"     ✅ Bucket '{INFLUXDB_BUCKET}' encontrado")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao verificar retenção: {e}")
        return False


def main():
    """Executar todos os testes"""
    print("\n" + "=" * 60)
    print("🧪 VALIDAÇÃO DO INFLUXDB - OptiFlow AI")
    print("=" * 60)
    print()

    tests = [
        ("Conexão", test_influxdb_connection),
        ("Escrita", test_write_sample_data),
        ("Leitura", test_read_data),
        ("Dados OPC-UA", test_opcua_data),
        ("Retenção", test_data_retention)
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Erro crítico no teste '{name}': {e}")
            results[name] = False

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)

    for name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name:20s}: {status}")

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    print("\n" + "=" * 60)
    print(f"Total: {passed}/{total} testes passaram")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
