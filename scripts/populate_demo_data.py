#!/usr/bin/env python3
"""
Script para popular dados de demonstração no OptiFlow AI

Este script cria:
1. Dados históricos no InfluxDB (últimas 48 horas)
2. Tags de equipamentos no PostgreSQL
3. Eventos de alarme para demonstração
"""

import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

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

BACKEND_URL = "http://localhost:8000"

# Equipamentos para simular
EQUIPMENTS = {
    "conveyors": [
        {"id": "CORR01", "name": "Correia Transportadora 01", "max_temp": 85, "max_current": 180, "max_speed": 3.5},
        {"id": "CORR02", "name": "Correia Transportadora 02", "max_temp": 85, "max_current": 150, "max_speed": 3.0},
        {"id": "CORR03", "name": "Correia Transportadora 03", "max_temp": 80, "max_current": 120, "max_speed": 2.5},
    ],
    "elevators": [
        {"id": "ELEV01", "name": "Elevador de Canecas 01", "max_temp": 75, "max_current": 250, "capacity_tph": 500},
        {"id": "ELEV02", "name": "Elevador de Canecas 02", "max_temp": 75, "max_current": 200, "capacity_tph": 400},
    ],
    "silos": [
        {"id": "SILO01", "name": "Silo de Armazenagem 01", "capacity_t": 50000, "max_temp": 40, "max_humidity": 16},
        {"id": "SILO02", "name": "Silo de Armazenagem 02", "capacity_t": 45000, "max_temp": 40, "max_humidity": 16},
        {"id": "SILO03", "name": "Silo de Armazenagem 03", "capacity_t": 40000, "max_temp": 40, "max_humidity": 16},
    ],
    "motors": [
        {"id": "MOTOR01", "name": "Motor Principal Correia 01", "power_kw": 150, "max_temp": 90, "max_vibration": 10},
        {"id": "MOTOR02", "name": "Motor Principal Elevador 01", "power_kw": 200, "max_temp": 95, "max_vibration": 12},
    ],
    "shiploader": [
        {"id": "SHIPLOADER01", "name": "Carregador de Navio 01", "max_flow_tph": 2500, "max_current": 400},
    ]
}

# Tags a serem criadas
TAGS_CONFIG = [
    # Correias
    {"name": "CORR01_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "CORR01", "type": "temperature"},
    {"name": "CORR01_CORRENTE", "unit": "A", "category": "PROCESS", "equipment": "CORR01", "type": "current"},
    {"name": "CORR01_VELOCIDADE", "unit": "m/s", "category": "PROCESS", "equipment": "CORR01", "type": "speed"},
    {"name": "CORR01_VAZAO", "unit": "t/h", "category": "PROCESS", "equipment": "CORR01", "type": "flow"},
    {"name": "CORR01_STATUS", "unit": "", "category": "STATUS", "equipment": "CORR01", "type": "status"},

    {"name": "CORR02_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "CORR02", "type": "temperature"},
    {"name": "CORR02_CORRENTE", "unit": "A", "category": "PROCESS", "equipment": "CORR02", "type": "current"},
    {"name": "CORR02_VELOCIDADE", "unit": "m/s", "category": "PROCESS", "equipment": "CORR02", "type": "speed"},
    {"name": "CORR02_VAZAO", "unit": "t/h", "category": "PROCESS", "equipment": "CORR02", "type": "flow"},

    # Elevadores
    {"name": "ELEV01_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "ELEV01", "type": "temperature"},
    {"name": "ELEV01_CORRENTE", "unit": "A", "category": "PROCESS", "equipment": "ELEV01", "type": "current"},
    {"name": "ELEV01_VAZAO", "unit": "t/h", "category": "PROCESS", "equipment": "ELEV01", "type": "flow"},
    {"name": "ELEV01_STATUS", "unit": "", "category": "STATUS", "equipment": "ELEV01", "type": "status"},

    # Silos
    {"name": "SILO01_NIVEL", "unit": "%", "category": "PROCESS", "equipment": "SILO01", "type": "level"},
    {"name": "SILO01_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "SILO01", "type": "temperature"},
    {"name": "SILO01_UMIDADE", "unit": "%", "category": "QUALITY", "equipment": "SILO01", "type": "humidity"},

    {"name": "SILO02_NIVEL", "unit": "%", "category": "PROCESS", "equipment": "SILO02", "type": "level"},
    {"name": "SILO02_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "SILO02", "type": "temperature"},
    {"name": "SILO02_UMIDADE", "unit": "%", "category": "QUALITY", "equipment": "SILO02", "type": "humidity"},

    {"name": "SILO03_NIVEL", "unit": "%", "category": "PROCESS", "equipment": "SILO03", "type": "level"},
    {"name": "SILO03_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "SILO03", "type": "temperature"},

    # Motores
    {"name": "MOTOR01_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "MOTOR01", "type": "temperature"},
    {"name": "MOTOR01_VIBRACAO", "unit": "mm/s", "category": "PROCESS", "equipment": "MOTOR01", "type": "vibration"},
    {"name": "MOTOR01_POTENCIA", "unit": "kW", "category": "PROCESS", "equipment": "MOTOR01", "type": "power"},

    {"name": "MOTOR02_TEMP", "unit": "°C", "category": "PROCESS", "equipment": "MOTOR02", "type": "temperature"},
    {"name": "MOTOR02_VIBRACAO", "unit": "mm/s", "category": "PROCESS", "equipment": "MOTOR02", "type": "vibration"},

    # Shiploader
    {"name": "SHIPLOADER01_VAZAO", "unit": "t/h", "category": "PROCESS", "equipment": "SHIPLOADER01", "type": "flow"},
    {"name": "SHIPLOADER01_CORRENTE", "unit": "A", "category": "PROCESS", "equipment": "SHIPLOADER01", "type": "current"},
]


def generate_realistic_value(tag_type: str, base_value: float, hour: int, minute: int, add_anomaly: bool = False) -> float:
    """Gera valores realistas com padrões diurnos e variações"""

    # Padrão diurno (mais atividade durante o dia)
    day_factor = 0.7 + 0.3 * math.sin((hour - 6) * math.pi / 12) if 6 <= hour <= 18 else 0.5

    # Ruído aleatório
    noise = random.gauss(0, base_value * 0.02)

    # Valor base ajustado
    value = base_value * day_factor + noise

    # Adiciona anomalia ocasional
    if add_anomaly and random.random() < 0.01:
        value *= random.uniform(1.1, 1.3)

    # Limites por tipo
    if tag_type == "temperature":
        value = max(20, min(100, value))
    elif tag_type == "current":
        value = max(0, min(500, value))
    elif tag_type == "level":
        value = max(5, min(95, value))
    elif tag_type == "humidity":
        value = max(8, min(18, value))
    elif tag_type == "flow":
        value = max(0, min(3000, value))
    elif tag_type == "speed":
        value = max(0, min(5, value))
    elif tag_type == "vibration":
        value = max(0, min(15, value))
    elif tag_type == "power":
        value = max(0, min(300, value))
    elif tag_type == "status":
        value = 1.0 if random.random() > 0.05 else 0.0  # 95% running

    return float(round(value, 2))


def get_base_value(tag_config: Dict) -> float:
    """Retorna valor base para cada tipo de tag"""
    tag_type = tag_config["type"]
    equipment = tag_config["equipment"]

    base_values = {
        "temperature": {"CORR": 55, "ELEV": 50, "SILO": 28, "MOTOR": 65},
        "current": {"CORR": 100, "ELEV": 150, "SHIPLOADER": 250},
        "speed": {"CORR": 2.5},
        "flow": {"CORR": 800, "ELEV": 400, "SHIPLOADER": 1800},
        "level": {"SILO": 60},
        "humidity": {"SILO": 13},
        "vibration": {"MOTOR": 4},
        "power": {"MOTOR": 120},
        "status": {"default": 1},
    }

    type_values = base_values.get(tag_type, {"default": 50})

    for prefix, value in type_values.items():
        if equipment.startswith(prefix):
            return value

    return type_values.get("default", 50)


def populate_influxdb(hours_back: int = 48):
    """Popula InfluxDB com dados históricos"""
    print(f"📊 Populando InfluxDB com {hours_back} horas de dados históricos...")

    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours_back)

    # Intervalo de 1 minuto entre pontos
    interval_minutes = 1
    total_points = (hours_back * 60) // interval_minutes

    points_written = 0
    batch = []
    batch_size = 1000

    current_time = start_time
    while current_time <= now:
        hour = current_time.hour
        minute = current_time.minute

        for tag_config in TAGS_CONFIG:
            base_value = get_base_value(tag_config)

            # Adiciona anomalias em alguns momentos específicos
            add_anomaly = (
                (hour == 14 and 30 <= minute <= 45) or  # Pico de temperatura às 14:30
                (hour == 10 and 0 <= minute <= 15)       # Oscilação às 10:00
            )

            value = generate_realistic_value(
                tag_config["type"],
                base_value,
                hour,
                minute,
                add_anomaly
            )

            point = Point("process_data") \
                .tag("tag_id", tag_config["name"]) \
                .tag("equipment", tag_config["equipment"]) \
                .tag("category", tag_config["category"]) \
                .tag("unit", tag_config["unit"]) \
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


def create_tags_in_postgres():
    """Cria tags no PostgreSQL"""
    print("🏷️  Criando tags no PostgreSQL...")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Busca device_id existente ou cria um
    cur.execute("SELECT id FROM devices LIMIT 1")
    result = cur.fetchone()

    if result:
        device_id = result["id"]
        print(f"  ✓ Usando device existente: {device_id}")
    else:
        # Cria um device padrão
        device_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO devices (id, name, device_type, protocol, is_active, host, port, settings, created_at, updated_at)
            VALUES (%s, 'Gateway Principal', 'GATEWAY', 'OPCUA', true, 'localhost', 4840, '{}', NOW(), NOW())
            ON CONFLICT DO NOTHING
        """, (device_id,))
        conn.commit()
        print(f"  ✓ Device criado: {device_id}")

    tags_created = 0
    for tag_config in TAGS_CONFIG:
        # Verifica se tag já existe
        cur.execute("SELECT id FROM tags WHERE name = %s", (tag_config["name"],))
        existing = cur.fetchone()

        if existing:
            print(f"  - Tag {tag_config['name']} já existe, pulando...")
            continue

        tag_id = str(uuid.uuid4())
        try:
            # Estrutura correta da tabela tags
            cur.execute("""
                INSERT INTO tags (
                    id, name, device_id, address, data_type, description, unit, category,
                    is_active, scale, "offset", scan_rate_ms, enable_quality_check,
                    data_points_count, settings, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, 'FLOAT', %s, %s, %s, true, 1.0, 0.0, 1000, true, 0, '{}', NOW(), NOW())
            """, (
                tag_id,
                tag_config["name"],
                device_id,
                f"simulator:{tag_config['name'].lower()}",
                f"Tag {tag_config['name']} - {tag_config['equipment']}",
                tag_config["unit"],
                tag_config["category"]
            ))
            conn.commit()
            tags_created += 1
            print(f"  ✓ Tag {tag_config['name']} criada")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️  Erro ao criar tag {tag_config['name']}: {e}")

    cur.close()
    conn.close()

    print(f"✅ {tags_created} tags criadas/atualizadas no PostgreSQL")


def create_alarm_definitions():
    """Cria definições de alarme no PostgreSQL"""
    print("🚨 Criando definições de alarme...")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Busca tags para criar alarmes
    cur.execute("SELECT id, name FROM tags WHERE category = 'PROCESS'")
    tags = cur.fetchall()

    alarm_configs = {
        "TEMP": {"high_limit": 75, "high_high_limit": 85, "low_limit": 15, "low_low_limit": 10},
        "CORRENTE": {"high_limit": 180, "high_high_limit": 220},
        "NIVEL": {"high_limit": 90, "high_high_limit": 95, "low_limit": 15, "low_low_limit": 10},
        "UMIDADE": {"high_limit": 15, "high_high_limit": 16},
        "VIBRACAO": {"high_limit": 8, "high_high_limit": 12},
    }

    alarms_created = 0
    for tag in tags:
        tag_name = tag["name"]
        tag_id = tag["id"]

        for alarm_type, limits in alarm_configs.items():
            if alarm_type in tag_name:
                alarm_id = str(uuid.uuid4())
                alarm_name = f"ALARME_{tag_name}"

                # Determina tipo de alarme e severidade
                alarm_type_db = "HIGH_LIMIT" if "high_limit" in limits else "LOW_LIMIT"
                severity = "HIGH" if "high_high_limit" in limits else "MEDIUM"

                # Verifica se já existe
                cur.execute("SELECT id FROM alarm_definitions WHERE name = %s", (alarm_name,))
                if cur.fetchone():
                    continue

                try:
                    cur.execute("""
                        INSERT INTO alarm_definitions (
                            id, tag_id, name, description, is_active, alarm_type, severity,
                            high_limit, high_high_limit, low_limit, low_low_limit,
                            deadband, delay_seconds, enable_email, enable_sms,
                            notification_recipients, settings, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, true, %s, %s, %s, %s, %s, %s, 0.5, 5, false, false, '[]'::jsonb, '{}'::jsonb, NOW(), NOW())
                    """, (
                        alarm_id,
                        tag_id,
                        alarm_name,
                        f"Alarme automático para {tag_name}",
                        alarm_type_db,
                        severity,
                        limits.get("high_limit"),
                        limits.get("high_high_limit"),
                        limits.get("low_limit"),
                        limits.get("low_low_limit")
                    ))
                    alarms_created += 1
                except Exception as e:
                    print(f"  ❌ Erro ao criar alarme {alarm_name}: {e}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ {alarms_created} definições de alarme criadas")


def create_alarm_events():
    """Cria alguns eventos de alarme históricos"""
    print("📋 Criando eventos de alarme históricos...")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Busca definições de alarme com high_limit para calcular valores
    cur.execute("SELECT id, name, high_limit, high_high_limit FROM alarm_definitions LIMIT 10")
    alarm_defs = cur.fetchall()

    events_created = 0
    now = datetime.utcnow()

    for alarm_def in alarm_defs:
        # Usa high_limit ou high_high_limit como referência
        threshold = alarm_def.get("high_limit") or alarm_def.get("high_high_limit") or 100

        # Cria 2-3 eventos por alarme nas últimas 48h
        for i in range(random.randint(1, 3)):
            event_id = str(uuid.uuid4())
            hours_ago = random.randint(1, 48)
            trigger_time = now - timedelta(hours=hours_ago)
            duration = random.randint(5, 60)  # 5-60 minutos
            clear_time = trigger_time + timedelta(minutes=duration)

            trigger_value = threshold * random.uniform(1.05, 1.2)
            clear_value = threshold * random.uniform(0.85, 0.95)

            # Estado: alguns ativos, maioria limpos
            state = "CLEARED" if random.random() > 0.2 else "ACTIVE"

            try:
                cur.execute("""
                    INSERT INTO alarm_events (
                        id, definition_id, state, trigger_value, trigger_timestamp,
                        cleared_at, clear_value, duration_seconds, event_metadata,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '{}'::jsonb, NOW(), NOW())
                """, (
                    event_id,
                    alarm_def["id"],
                    state,
                    round(trigger_value, 2),
                    trigger_time,
                    clear_time if state == "CLEARED" else None,
                    round(clear_value, 2) if state == "CLEARED" else None,
                    duration * 60 if state == "CLEARED" else None
                ))
                events_created += 1
            except Exception as e:
                print(f"  ❌ Erro ao criar evento: {e}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ {events_created} eventos de alarme criados")


def verify_data():
    """Verifica os dados criados"""
    print("\n📊 Verificando dados criados...")

    # InfluxDB
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()

    query = '''
    from(bucket: "timeseries")
    |> range(start: -48h)
    |> filter(fn: (r) => r._measurement == "process_data")
    |> group(columns: ["tag_id"])
    |> count()
    '''

    try:
        tables = query_api.query(query)
        tag_count = len(list(tables))
        print(f"  ✓ InfluxDB: {tag_count} tags com dados históricos")
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar InfluxDB: {e}")

    client.close()

    # PostgreSQL
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tags")
    tag_count = cur.fetchone()[0]
    print(f"  ✓ PostgreSQL: {tag_count} tags configuradas")

    cur.execute("SELECT COUNT(*) FROM alarm_definitions")
    alarm_count = cur.fetchone()[0]
    print(f"  ✓ PostgreSQL: {alarm_count} definições de alarme")

    cur.execute("SELECT COUNT(*) FROM alarm_events")
    event_count = cur.fetchone()[0]
    print(f"  ✓ PostgreSQL: {event_count} eventos de alarme")

    cur.close()
    conn.close()


def main():
    print("=" * 60)
    print("🚀 OptiFlow AI - Gerador de Dados de Demonstração")
    print("=" * 60)
    print()

    try:
        # 1. Criar tags no PostgreSQL
        create_tags_in_postgres()
        print()

        # 2. Popular InfluxDB com dados históricos
        populate_influxdb(hours_back=48)
        print()

        # 3. Criar definições de alarme
        create_alarm_definitions()
        print()

        # 4. Criar eventos de alarme
        create_alarm_events()
        print()

        # 5. Verificar dados
        verify_data()

        print()
        print("=" * 60)
        print("✅ Dados de demonstração criados com sucesso!")
        print("=" * 60)
        print()
        print("Próximos passos:")
        print("  1. Acesse http://localhost:3000 para ver os dashboards")
        print("  2. Navegue para 'Monitoramento de Processo'")
        print("  3. Explore os painéis de IA (PCM, Preditivo, Qualidade)")
        print()

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
