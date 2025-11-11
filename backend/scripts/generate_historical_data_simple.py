#!/usr/bin/env python3
"""
🔥 Gerador de Dados Históricos Realistas - OptiFlow AI (Versão Simplificada)
===========================================================================

Gera 30 dias de dados industriais diretamente no InfluxDB.
Sem dependências de models problemáticos.

Uso:
    python scripts/generate_historical_data_simple.py
"""

import sys
from datetime import datetime, timedelta
import random
import math
import numpy as np
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

# Configurações InfluxDB
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")

# Período de geração
DAYS_TO_GENERATE = 30
INTERVAL_SECONDS = 60  # 1 ponto por minuto
POINTS_PER_DAY = (24 * 60 * 60) // INTERVAL_SECONDS  # 1440 pontos/dia
TOTAL_POINTS = DAYS_TO_GENERATE * POINTS_PER_DAY  # ~43,200 pontos

# Data final = agora, data inicial = 30 dias atrás
END_TIME = datetime.utcnow()
START_TIME = END_TIME - timedelta(days=DAYS_TO_GENERATE)

print(f"""
{'='*60}
🔥 GERADOR DE DADOS HISTÓRICOS REALISTAS
{'='*60}
📅 Período: {START_TIME.strftime('%Y-%m-%d %H:%M')} → {END_TIME.strftime('%Y-%m-%d %H:%M')}
⏱️  Intervalo: {INTERVAL_SECONDS}s ({POINTS_PER_DAY} pontos/dia)
📊 Total: {TOTAL_POINTS:,} pontos por tag
{'='*60}
""")

# Definições de tags
TAG_DEFINITIONS = {
    "MOTOR_01_CURRENT": {
        "name": "Motor 01 - Corrente",
        "unit": "A",
        "base_value": 35.0,
        "variation": 5.0,
        "min_value": 0.0,
        "max_value": 50.0,
        "alarm_high": 45.0,
        "alarm_critical": 48.0,
        "alarm_low": 10.0,
        "daily_pattern": True,
        "anomaly_probability": 0.02,
    },
    "MOTOR_01_SPEED": {
        "name": "Motor 01 - Velocidade",
        "unit": "RPM",
        "base_value": 1750.0,
        "variation": 50.0,
        "min_value": 0.0,
        "max_value": 2000.0,
        "alarm_high": 1900.0,
        "alarm_low": 1600.0,
        "daily_pattern": True,
        "anomaly_probability": 0.01,
    },
    "MOTOR_01_VIBRATION": {
        "name": "Motor 01 - Vibração",
        "unit": "mm/s",
        "base_value": 2.5,
        "variation": 0.5,
        "min_value": 0.0,
        "max_value": 10.0,
        "alarm_high": 4.5,
        "alarm_critical": 7.0,
        "daily_pattern": False,
        "anomaly_probability": 0.015,
    },
    "TEMP_SENSOR_01": {
        "name": "Temperatura - Área Produção",
        "unit": "°C",
        "base_value": 45.0,
        "variation": 5.0,
        "min_value": 20.0,
        "max_value": 90.0,
        "alarm_high": 70.0,
        "alarm_critical": 80.0,
        "alarm_low": 30.0,
        "daily_pattern": True,
        "anomaly_probability": 0.025,
    },
    "TEMP_SENSOR_02": {
        "name": "Temperatura - Caldeira",
        "unit": "°C",
        "base_value": 85.0,
        "variation": 3.0,
        "min_value": 50.0,
        "max_value": 120.0,
        "alarm_high": 95.0,
        "alarm_critical": 105.0,
        "alarm_low": 70.0,
        "daily_pattern": True,
        "anomaly_probability": 0.01,
    },
    "PRESSURE_01": {
        "name": "Pressão - Linha Principal",
        "unit": "bar",
        "base_value": 6.5,
        "variation": 0.5,
        "min_value": 0.0,
        "max_value": 10.0,
        "alarm_high": 8.5,
        "alarm_critical": 9.5,
        "alarm_low": 4.0,
        "daily_pattern": True,
        "anomaly_probability": 0.02,
    },
    "PRESSURE_02": {
        "name": "Pressão - Caldeira",
        "unit": "bar",
        "base_value": 8.0,
        "variation": 0.3,
        "min_value": 0.0,
        "max_value": 12.0,
        "alarm_high": 10.0,
        "alarm_critical": 11.0,
        "alarm_low": 6.0,
        "daily_pattern": True,
        "anomaly_probability": 0.015,
    },
    "LEVEL_TANK_01": {
        "name": "Nível - Tanque Água",
        "unit": "%",
        "base_value": 70.0,
        "variation": 10.0,
        "min_value": 0.0,
        "max_value": 100.0,
        "alarm_high": 90.0,
        "alarm_low": 20.0,
        "daily_pattern": False,
        "anomaly_probability": 0.01,
    },
    "POWER_CONSUMPTION": {
        "name": "Consumo Energético Total",
        "unit": "kW",
        "base_value": 250.0,
        "variation": 50.0,
        "min_value": 100.0,
        "max_value": 500.0,
        "alarm_high": 450.0,
        "alarm_critical": 480.0,
        "daily_pattern": True,
        "anomaly_probability": 0.01,
    },
    "PRODUCTION_RATE": {
        "name": "Taxa de Produção",
        "unit": "units/h",
        "base_value": 500.0,
        "variation": 50.0,
        "min_value": 0.0,
        "max_value": 800.0,
        "alarm_low": 200.0,
        "daily_pattern": True,
        "anomaly_probability": 0.02,
    },
}


def get_daily_pattern_factor(timestamp: datetime) -> float:
    """Retorna fator baseado na hora do dia (0.7 - 1.3)"""
    hour = timestamp.hour
    if 0 <= hour < 6:  # Noite
        return 0.7 + 0.1 * math.sin(math.pi * hour / 6)
    elif 6 <= hour < 12:  # Manhã
        return 0.9 + 0.3 * ((hour - 6) / 6)
    elif 12 <= hour < 18:  # Tarde
        return 1.2 + 0.1 * math.sin(math.pi * (hour - 12) / 6)
    else:  # Noite
        return 1.0 - 0.2 * ((hour - 18) / 6)


def get_weekly_pattern_factor(timestamp: datetime) -> float:
    """Retorna fator baseado no dia da semana (0.6 - 1.0)"""
    weekday = timestamp.weekday()
    if weekday < 5:  # Segunda-Sexta
        return 0.95 + 0.05 * random.random()
    elif weekday == 5:  # Sábado
        return 0.7 + 0.1 * random.random()
    else:  # Domingo
        return 0.6 + 0.05 * random.random()


def generate_value(tag_def: dict, timestamp: datetime) -> tuple:
    """Gera valor com padrões e anomalias"""
    base = tag_def["base_value"]
    variation = tag_def["variation"]
    
    # Ruído gaussiano
    noise = np.random.normal(0, variation / 3)
    value = base + noise
    
    # Padrões temporais
    if tag_def.get("daily_pattern"):
        daily_factor = get_daily_pattern_factor(timestamp)
        value = base * daily_factor + noise
    
    weekly_factor = get_weekly_pattern_factor(timestamp)
    value *= weekly_factor
    
    # Injetar anomalia?
    is_anomaly = False
    if random.random() < tag_def.get("anomaly_probability", 0):
        multiplier = random.uniform(1.5, 2.5)
        value *= multiplier
        is_anomaly = True
    
    # Limitar aos valores min/max
    value = max(tag_def["min_value"], min(tag_def["max_value"], value))
    
    # Verificar alarmes
    alarms = []
    if "alarm_critical" in tag_def and value >= tag_def["alarm_critical"]:
        alarms.append("CRITICAL")
    elif "alarm_high" in tag_def and value >= tag_def["alarm_high"]:
        alarms.append("HIGH")
    if "alarm_low" in tag_def and value <= tag_def["alarm_low"]:
        alarms.append("LOW")
    
    return value, is_anomaly, alarms


def generate_timestamps(start: datetime, end: datetime, interval_seconds: int):
    """Gera série de timestamps"""
    current = start
    while current <= end:
        yield current
        current += timedelta(seconds=interval_seconds)


def main():
    """Função principal"""
    print("🔄 Conectando ao InfluxDB...")
    
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        print("  ✅ Conectado ao InfluxDB\n")
    except Exception as e:
        print(f"  ❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    total_tags = len(TAG_DEFINITIONS)
    total_anomalies = 0
    total_alarms = 0
    
    print(f"📊 Gerando dados para {total_tags} tags...")
    print(f"   Isso pode levar 5-10 minutos...\n")
    
    for idx, (tag_key, tag_def) in enumerate(TAG_DEFINITIONS.items(), 1):
        tag_name = tag_def["name"]
        print(f"  [{idx}/{total_tags}] {tag_name}...", end=" ", flush=True)
        
        points_written = 0
        anomalies = 0
        alarms_count = 0
        batch = []
        
        for ts in generate_timestamps(START_TIME, END_TIME, INTERVAL_SECONDS):
            value, is_anomaly, alarms = generate_value(tag_def, ts)
            
            if is_anomaly:
                anomalies += 1
                total_anomalies += 1
            
            if alarms:
                alarms_count += 1
                total_alarms += 1
            
            # Criar ponto
            point = Point("tag_values") \
                .tag("tag_key", tag_key) \
                .tag("tag_name", tag_name) \
                .tag("unit", tag_def.get("unit", "")) \
                .field("value", float(value)) \
                .time(ts)
            
            if is_anomaly:
                point.tag("is_anomaly", "true")
            if alarms:
                point.tag("alarms", ",".join(alarms))
            
            batch.append(point)
            points_written += 1
            
            # Escrever em batch de 1000 pontos
            if len(batch) >= 1000:
                try:
                    write_api.write(bucket=INFLUXDB_BUCKET, record=batch)
                    batch = []
                except Exception as e:
                    print(f"\n    ⚠️  Erro ao escrever batch: {e}")
        
        # Escrever batch restante
        if batch:
            try:
                write_api.write(bucket=INFLUXDB_BUCKET, record=batch)
            except Exception as e:
                print(f"\n    ⚠️  Erro ao escrever batch final: {e}")
        
        print(f"✅ {points_written:,} pontos, {anomalies} anomalias, {alarms_count} alarmes")
    
    client.close()
    
    print(f"""
{'='*60}
✅ GERAÇÃO CONCLUÍDA!
{'='*60}
📊 Total de pontos: {total_tags * TOTAL_POINTS:,}
🔴 Anomalias injetadas: {total_anomalies}
🚨 Condições de alarme: {total_alarms}
💾 Dados gravados no InfluxDB: {INFLUXDB_BUCKET}
{'='*60}

🎯 Próximos passos:
   1. Verificar dados no Grafana: http://localhost:3001
   2. Consultar via API: http://localhost:8000/api/v1/tags/TAG_ID/data
   3. Treinar modelos de ML com os dados históricos
   4. Testar Agent com contexto histórico

Para consultar dados no InfluxDB:
   from(bucket: "{INFLUXDB_BUCKET}")
     |> range(start: -30d)
     |> filter(fn: (r) => r["_measurement"] == "tag_values")
     |> filter(fn: (r) => r["tag_name"] == "Motor 01 - Corrente")

""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Geração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
