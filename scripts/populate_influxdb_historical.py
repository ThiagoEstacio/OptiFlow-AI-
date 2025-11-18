#!/usr/bin/env python3
"""
Script para popular InfluxDB com dados históricos simulados

Popula últimos 30 dias com dados para permitir:
- calculate_statistics
- get_historical_data
- detect_anomalies
- compare_tags
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import random
import math

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# Configuração InfluxDB (from docker-compose.yml)
INFLUX_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")


# Definição de equipamentos e tags do sistema
EQUIPMENT_TAGS = {
    "ELEV01": {
        "TEMP_C_PV": {"min": 60, "max": 85, "unit": "°C", "anomaly_chance": 0.02},
        "CURRENT_A_PV": {"min": 35, "max": 55, "unit": "A", "anomaly_chance": 0.01},
        "SPEED_RPM": {"min": 1400, "max": 1500, "unit": "RPM", "anomaly_chance": 0.01},
        "VIBRATION_MM_S": {"min": 1.5, "max": 4.5, "unit": "mm/s", "anomaly_chance": 0.03},
    },
    "ELEV02": {
        "TEMP_C_PV": {"min": 58, "max": 82, "unit": "°C", "anomaly_chance": 0.02},
        "CURRENT_A_PV": {"min": 33, "max": 53, "unit": "A", "anomaly_chance": 0.01},
        "SPEED_RPM": {"min": 1380, "max": 1480, "unit": "RPM", "anomaly_chance": 0.01},
        "VIBRATION_MM_S": {"min": 1.2, "max": 4.0, "unit": "mm/s", "anomaly_chance": 0.03},
    },
    "SILO01": {
        "LEVEL_PCT": {"min": 40, "max": 95, "unit": "%", "anomaly_chance": 0.05},
        "TEMP_C_PV": {"min": 20, "max": 35, "unit": "°C", "anomaly_chance": 0.01},
        "PRESSURE_BAR": {"min": 0.8, "max": 1.2, "unit": "bar", "anomaly_chance": 0.01},
    },
    "SILO02": {
        "LEVEL_PCT": {"min": 35, "max": 98, "unit": "%", "anomaly_chance": 0.05},
        "TEMP_C_PV": {"min": 18, "max": 32, "unit": "°C", "anomaly_chance": 0.01},
        "PRESSURE_BAR": {"min": 0.75, "max": 1.15, "unit": "bar", "anomaly_chance": 0.01},
    },
    "ARZ_CORR01": {
        "VELOCIDADE_PV": {"min": 45, "max": 65, "unit": "m/min", "anomaly_chance": 0.02},
        "TEMPERATURA_PV": {"min": 30, "max": 50, "unit": "°C", "anomaly_chance": 0.01},
        "CORRENTE_PV": {"min": 8, "max": 15, "unit": "A", "anomaly_chance": 0.01},
    },
    "ARZ_CORR02": {
        "VELOCIDADE_PV": {"min": 42, "max": 62, "unit": "m/min", "anomaly_chance": 0.02},
        "TEMPERATURA_PV": {"min": 28, "max": 48, "unit": "°C", "anomaly_chance": 0.01},
        "CORRENTE_PV": {"min": 7, "max": 14, "unit": "A", "anomaly_chance": 0.01},
    },
    "ENERGY": {
        "DEMAND_KW": {"min": 180, "max": 280, "unit": "kW", "anomaly_chance": 0.03},
        "CONSUMPTION_KWH": {"min": 4000, "max": 6500, "unit": "kWh", "anomaly_chance": 0.02},
        "POWER_FACTOR": {"min": 0.85, "max": 0.98, "unit": "", "anomaly_chance": 0.01},
    }
}


def generate_realistic_value(config: Dict, timestamp: datetime, base_seed: int = 0) -> float:
    """
    Gera valor realista com:
    - Variação diurna (mais atividade durante dia)
    - Ruído aleatório
    - Anomalias ocasionais
    - Tendências de longo prazo
    """
    min_val = config["min"]
    max_val = config["max"]
    anomaly_chance = config.get("anomaly_chance", 0.01)
    
    # Base: média entre min e max
    base_value = (min_val + max_val) / 2
    amplitude = (max_val - min_val) / 2
    
    # 1. Variação diurna (ciclo de 24h)
    hour_of_day = timestamp.hour + timestamp.minute / 60
    diurnal_factor = 0.3 * math.sin((hour_of_day - 6) * math.pi / 12)  # Pico às 18h
    
    # 2. Variação semanal (fim de semana mais baixo)
    weekday = timestamp.weekday()
    weekly_factor = 0.1 if weekday >= 5 else 0  # Reduz 10% no fim de semana
    
    # 3. Ruído aleatório
    random.seed(int(timestamp.timestamp()) + base_seed)
    noise = random.gauss(0, 0.1)  # Desvio padrão 10%
    
    # 4. Tendência de longo prazo (degrada ao longo do mês)
    days_elapsed = (timestamp - (timestamp - timedelta(days=30))).days
    trend_factor = 0.05 * (days_elapsed / 30)  # Aumenta 5% ao longo do mês
    
    # 5. Anomalias ocasionais
    anomaly_factor = 0
    if random.random() < anomaly_chance:
        anomaly_factor = random.choice([0.3, 0.4, -0.3])  # ±30-40%
    
    # Combinar todos os fatores
    total_factor = diurnal_factor - weekly_factor + noise + trend_factor + anomaly_factor
    
    # Calcular valor final
    value = base_value + (amplitude * total_factor)
    
    # Garantir que está dentro dos limites (com margem para anomalias)
    value = max(min_val * 0.8, min(max_val * 1.2, value))
    
    return round(value, 2)


def populate_influxdb(days: int = 30, interval_minutes: int = 1):
    """
    Popula InfluxDB com dados históricos
    
    Args:
        days: Número de dias para trás
        interval_minutes: Intervalo entre pontos em minutos
    """
    print(f"🚀 Iniciando população do InfluxDB")
    print(f"📅 Período: Últimos {days} dias")
    print(f"⏱️  Intervalo: {interval_minutes} minuto(s)")
    print(f"🔗 URL: {INFLUX_URL}")
    print(f"📊 Bucket: {INFLUX_BUCKET}")
    print()
    
    # Conectar ao InfluxDB
    try:
        client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        print("✅ Conectado ao InfluxDB")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Calcular timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    total_points_per_tag = (days * 24 * 60) // interval_minutes
    
    print(f"📈 Gerando {total_points_per_tag:,} pontos por tag")
    print(f"🏷️  Total de tags: {sum(len(tags) for tags in EQUIPMENT_TAGS.values())}")
    print()
    
    # Gerar e escrever dados
    batch_size = 5000
    points_batch = []
    total_written = 0
    
    current_time = start_time
    point_count = 0
    
    while current_time <= end_time:
        # Para cada equipamento e tag
        for equipment_id, tags in EQUIPMENT_TAGS.items():
            for tag_name, config in tags.items():
                full_tag_name = f"{equipment_id}_{tag_name}"
                
                # Gerar valor realista
                value = generate_realistic_value(
                    config, 
                    current_time, 
                    base_seed=hash(full_tag_name)
                )
                
                # Criar ponto InfluxDB
                point = Point("sensor_data") \
                    .tag("tag_id", full_tag_name) \
                    .tag("equipment", equipment_id) \
                    .tag("parameter", tag_name) \
                    .field("value", value) \
                    .field("quality", "good") \
                    .time(current_time)
                
                points_batch.append(point)
        
        # Escrever batch
        if len(points_batch) >= batch_size:
            try:
                write_api.write(bucket=INFLUX_BUCKET, record=points_batch)
                total_written += len(points_batch)
                progress = (total_written / (total_points_per_tag * len(EQUIPMENT_TAGS) * len(list(EQUIPMENT_TAGS.values())[0]))) * 100
                print(f"📝 Escritos: {total_written:,} pontos ({progress:.1f}%) - {current_time.strftime('%Y-%m-%d %H:%M')}", end='\r')
                points_batch = []
            except Exception as e:
                print(f"\n❌ Erro ao escrever batch: {e}")
        
        # Avançar para próximo timestamp
        current_time += timedelta(minutes=interval_minutes)
        point_count += 1
    
    # Escrever últimos pontos
    if points_batch:
        try:
            write_api.write(bucket=INFLUX_BUCKET, record=points_batch)
            total_written += len(points_batch)
        except Exception as e:
            print(f"\n❌ Erro ao escrever últimos pontos: {e}")
    
    print(f"\n\n✅ População concluída!")
    print(f"📊 Total de pontos escritos: {total_written:,}")
    print(f"🏷️  Tags populadas: {sum(len(tags) for tags in EQUIPMENT_TAGS.values())}")
    print(f"⏱️  Período: {start_time.strftime('%Y-%m-%d %H:%M')} até {end_time.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Verificar dados escritos
    print("🔍 Verificando dados escritos...")
    try:
        query_api = client.query_api()
        
        # Query para contar pontos
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -{days}d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> count()
        '''
        
        result = query_api.query(query=query)
        
        if result:
            for table in result:
                for record in table.records:
                    tag_id = record.values.get("tag_id", "unknown")
                    count = record.get_value()
                    print(f"  ✓ {tag_id}: {count:,} pontos")
        
        print("\n✅ Verificação concluída!")
    except Exception as e:
        print(f"⚠️  Erro na verificação: {e}")
    
    client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Popular InfluxDB com dados históricos")
    parser.add_argument("--days", type=int, default=30, help="Número de dias (padrão: 30)")
    parser.add_argument("--interval", type=int, default=1, help="Intervalo em minutos (padrão: 1)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("  OptiFlow AI - População de Dados Históricos no InfluxDB")
    print("=" * 80)
    print()
    
    populate_influxdb(days=args.days, interval_minutes=args.interval)
    
    print()
    print("=" * 80)
    print("  🎉 Processo concluído! O Agent agora tem dados para análise.")
    print("=" * 80)
