#!/usr/bin/env python3
"""
Script para re-popular o InfluxDB com dados no formato correto para o backend.
O backend espera:
- measurement = "tag_data"
- tag_id = UUID (do PostgreSQL)
- quality = "good"
- field = "value"
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import random
import math

# Configurações
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "my-super-secret-influxdb-token"
INFLUXDB_ORG = "optiflow"
INFLUXDB_BUCKET = "timeseries"

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "optiflow",
    "user": "optiflow",
    "password": "optiflow_password"
}

# Configurações de valores por tipo de tag
VALUE_CONFIGS = {
    "TEMP": {"min": 20, "max": 80, "base": 45},
    "CORRENTE": {"min": 50, "max": 200, "base": 120},
    "VELOCIDADE": {"min": 0.5, "max": 3.0, "base": 2.0},
    "VAZAO": {"min": 500, "max": 1500, "base": 1000},
    "STATUS": {"min": 0, "max": 1, "base": 1},
    "NIVEL": {"min": 20, "max": 95, "base": 60},
    "UMIDADE": {"min": 10, "max": 18, "base": 13},
    "VIBRACAO": {"min": 1, "max": 15, "base": 4},
    "POTENCIA": {"min": 50, "max": 200, "base": 120},
}


def get_tag_type(tag_name: str) -> str:
    """Identifica o tipo de tag pelo nome"""
    for type_key in VALUE_CONFIGS.keys():
        if type_key in tag_name.upper():
            return type_key
    return "TEMP"  # Default


def generate_value(tag_type: str, hour: int, minute: int, add_anomaly: bool = False) -> float:
    """Gera um valor realístico para o tipo de tag"""
    config = VALUE_CONFIGS.get(tag_type, VALUE_CONFIGS["TEMP"])
    base = config["base"]
    range_val = config["max"] - config["min"]

    # Padrão diurno
    diurnal_factor = math.sin((hour - 6) * math.pi / 12) * 0.15

    # Ruído aleatório
    noise = random.gauss(0, range_val * 0.03)

    # Valor com variação
    value = base + (base * diurnal_factor) + noise

    # Anomalia
    if add_anomaly:
        value += range_val * 0.2 * random.choice([1, -1])

    # Status é binário
    if tag_type == "STATUS":
        return float(1.0 if random.random() > 0.02 else 0.0)

    # Garante limites
    value = max(config["min"], min(config["max"], value))
    return float(round(value, 2))


def get_postgres_tags():
    """Busca todas as tags do PostgreSQL que começam com nossos prefixos"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, name, unit
        FROM tags
        WHERE name LIKE 'CORR%'
           OR name LIKE 'ELEV%'
           OR name LIKE 'SILO%'
           OR name LIKE 'MOTOR%'
           OR name LIKE 'SHIPLOADER%'
        ORDER BY name
    """)

    tags = cur.fetchall()
    cur.close()
    conn.close()

    return tags


def populate_influxdb(hours_back: int = 48):
    """Popula o InfluxDB com dados no formato correto"""
    print(f"📊 Populando InfluxDB com {hours_back} horas de dados históricos...")
    print("   Formato: measurement='tag_data', quality='good'")
    print()

    # Busca tags do PostgreSQL
    tags = get_postgres_tags()
    print(f"  ✓ Encontradas {len(tags)} tags no PostgreSQL")

    if not tags:
        print("  ❌ Nenhuma tag encontrada!")
        return

    # Conecta ao InfluxDB
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours_back)

    # Intervalo de 1 minuto entre pontos
    interval_minutes = 1

    points_written = 0
    batch = []
    batch_size = 1000

    current_time = start_time
    while current_time <= now:
        hour = current_time.hour
        minute = current_time.minute

        # Adiciona anomalias em alguns momentos específicos
        add_anomaly = (
            (hour == 14 and 30 <= minute <= 45) or
            (hour == 10 and 0 <= minute <= 15) or
            (hour == 3 and 0 <= minute <= 10)
        )

        for tag in tags:
            tag_id = str(tag["id"])
            tag_name = tag["name"]
            tag_type = get_tag_type(tag_name)

            value = generate_value(tag_type, hour, minute, add_anomaly)

            # Cria ponto no formato esperado pelo backend
            point = Point("tag_data") \
                .tag("tag_id", tag_id) \
                .tag("quality", "good") \
                .field("value", value) \
                .time(current_time, WritePrecision.S)

            batch.append(point)

            if len(batch) >= batch_size:
                write_api.write(bucket=INFLUXDB_BUCKET, record=batch)
                points_written += len(batch)
                print(f"  ✓ {points_written} pontos escritos...")
                batch = []

        current_time += timedelta(minutes=interval_minutes)

    # Escreve batch restante
    if batch:
        write_api.write(bucket=INFLUXDB_BUCKET, record=batch)
        points_written += len(batch)

    client.close()
    print(f"✅ Total: {points_written} pontos escritos no InfluxDB")


def verify_data():
    """Verifica os dados criados"""
    print("\n📊 Verificando dados criados...")

    # InfluxDB
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()

    query = '''
    from(bucket: "timeseries")
    |> range(start: -48h)
    |> filter(fn: (r) => r._measurement == "tag_data")
    |> filter(fn: (r) => r.quality == "good")
    |> group(columns: ["tag_id"])
    |> count()
    '''

    try:
        tables = query_api.query(query)
        tag_count = len(list(tables))
        print(f"  ✓ InfluxDB: {tag_count} tags com dados no formato 'tag_data'")
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar InfluxDB: {e}")

    # Teste de um ponto específico
    query_sample = '''
    from(bucket: "timeseries")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "tag_data")
    |> filter(fn: (r) => r.quality == "good")
    |> limit(n: 1)
    '''

    try:
        tables = query_api.query(query_sample)
        for table in tables:
            for record in table.records:
                print(f"  ✓ Sample: tag_id={record.values.get('tag_id')[:8]}..., value={record.get_value()}, quality={record.values.get('quality')}")
                break
    except Exception as e:
        print(f"  ⚠️  Erro ao obter sample: {e}")

    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OptiFlow AI - Re-população do InfluxDB")
    print("=" * 60)
    print()

    populate_influxdb(hours_back=48)
    print()
    verify_data()
    print()
    print("✅ Re-população concluída!")
