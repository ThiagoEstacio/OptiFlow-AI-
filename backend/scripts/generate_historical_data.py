#!/usr/bin/env python3
"""
🔥 Gerador de Dados Históricos Realistas - OptiFlow AI
======================================================

Gera 30 dias de dados industriais com:
- Valores realistas com padrões diários e semanais
- Anomalias intencionais para ML detectar
- Alarmes disparados (High/Low/Critical)
- Events (start/stop de equipamentos)
- Dados no InfluxDB (time-series) + PostgreSQL (metadata)

Uso:
    python scripts/generate_historical_data.py
    ou
    docker compose exec backend python scripts/generate_historical_data.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random
import math
from typing import List, Dict, Any, Tuple
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.db.session import AsyncSessionLocal
from app.models.organization import Organization
from app.models.device import Device, DeviceProtocol
from app.models.tag import Tag, TagDataType, TagCategory
from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmSeverity, AlarmType, AlarmState
from app.core.config import settings


# ========================================
# 📊 CONFIGURAÇÕES
# ========================================

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


# ========================================
# 🏭 DEFINIÇÃO DE TAGS REALISTAS
# ========================================

TAG_DEFINITIONS = {
    # Motor Principal - Produção
    "MOTOR_01_CURRENT": {
        "name": "Motor 01 - Corrente",
        "description": "Corrente elétrica do motor principal (A)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
        "unit": "A",
        "base_value": 35.0,  # Valor médio
        "variation": 5.0,    # Variação normal (±5A)
        "min_value": 0.0,
        "max_value": 50.0,
        "alarm_high": 45.0,   # Alarme alto
        "alarm_critical": 48.0,  # Alarme crítico
        "alarm_low": 10.0,
        "daily_pattern": True,  # Segue padrão diário (mais carga durante dia)
        "anomaly_probability": 0.02,  # 2% chance de anomalia
    },
    "MOTOR_01_SPEED": {
        "name": "Motor 01 - Velocidade",
        "description": "Velocidade de rotação (RPM)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
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
        "description": "Nível de vibração (mm/s)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.MAINTENANCE,
        "unit": "mm/s",
        "base_value": 2.5,
        "variation": 0.5,
        "min_value": 0.0,
        "max_value": 10.0,
        "alarm_high": 4.5,
        "alarm_critical": 7.0,
        "daily_pattern": False,
        "anomaly_probability": 0.015,  # Vibração aumenta antes de falha
    },
    
    # Temperatura - Processo
    "TEMP_SENSOR_01": {
        "name": "Temperatura - Área Produção",
        "description": "Temperatura ambiente área de produção (°C)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
        "unit": "°C",
        "base_value": 45.0,
        "variation": 5.0,
        "min_value": 20.0,
        "max_value": 90.0,
        "alarm_high": 70.0,
        "alarm_critical": 80.0,
        "alarm_low": 30.0,
        "daily_pattern": True,  # Mais quente durante o dia
        "anomaly_probability": 0.025,
    },
    "TEMP_SENSOR_02": {
        "name": "Temperatura - Caldeira",
        "description": "Temperatura da caldeira (°C)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
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
    
    # Pressão - Processo
    "PRESSURE_01": {
        "name": "Pressão - Linha Principal",
        "description": "Pressão na linha principal (bar)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
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
        "description": "Pressão interna da caldeira (bar)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
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
    
    # Nível - Processo
    "LEVEL_TANK_01": {
        "name": "Nível - Tanque Água",
        "description": "Nível do tanque de água (%)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
        "unit": "%",
        "base_value": 70.0,
        "variation": 10.0,
        "min_value": 0.0,
        "max_value": 100.0,
        "alarm_high": 90.0,
        "alarm_low": 20.0,
        "daily_pattern": False,  # Ciclo de enchimento/esvaziamento
        "anomaly_probability": 0.01,
    },
    
    # Energia - Consumo
    "POWER_CONSUMPTION": {
        "name": "Consumo Energético Total",
        "description": "Consumo de energia da planta (kW)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.ENERGY,
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
    
    # Produção - Contadores
    "PRODUCTION_COUNT": {
        "name": "Contador de Produção",
        "description": "Unidades produzidas (acumulado)",
        "data_type": TagDataType.INTEGER,
        "category": TagCategory.PRODUCTION,
        "unit": "units",
        "base_value": 0,  # Contador incremental
        "variation": 0,
        "min_value": 0,
        "max_value": 1000000,
        "daily_pattern": True,  # Produz mais durante turno diurno
        "anomaly_probability": 0.0,  # Contador não tem anomalia, apenas para de contar
    },
    "PRODUCTION_RATE": {
        "name": "Taxa de Produção",
        "description": "Taxa de produção instantânea (units/h)",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PRODUCTION,
        "unit": "units/h",
        "base_value": 500.0,
        "variation": 50.0,
        "min_value": 0.0,
        "max_value": 800.0,
        "alarm_low": 200.0,  # Produção baixa
        "daily_pattern": True,
        "anomaly_probability": 0.02,
    },
}


# ========================================
# 🎲 FUNÇÕES DE GERAÇÃO DE DADOS
# ========================================

def generate_timestamp_series(start: datetime, end: datetime, interval_seconds: int) -> List[datetime]:
    """Gera série temporal com timestamps"""
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current)
        current += timedelta(seconds=interval_seconds)
    return timestamps


def get_daily_pattern_factor(timestamp: datetime) -> float:
    """
    Retorna fator multiplicador baseado na hora do dia (0.7 - 1.3)
    - Noite (0-6h): 0.7-0.8 (baixa atividade)
    - Manhã (6-12h): 0.9-1.2 (rampa de subida)
    - Tarde (12-18h): 1.1-1.3 (pico)
    - Noite (18-24h): 0.8-1.0 (rampa de descida)
    """
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
    """
    Retorna fator multiplicador baseado no dia da semana (0.6 - 1.0)
    - Segunda-Sexta: 0.95-1.0 (produção normal)
    - Sábado: 0.7-0.8 (meio período)
    - Domingo: 0.6 (mínimo/manutenção)
    """
    weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
    if weekday < 5:  # Segunda-Sexta
        return 0.95 + 0.05 * random.random()
    elif weekday == 5:  # Sábado
        return 0.7 + 0.1 * random.random()
    else:  # Domingo
        return 0.6 + 0.05 * random.random()


def generate_base_value(tag_def: Dict, timestamp: datetime, previous_value: float = None) -> float:
    """Gera valor base com padrões diários e semanais"""
    base = tag_def["base_value"]
    variation = tag_def["variation"]
    
    # Contador incremental (produção)
    if tag_def["data_type"] == TagDataType.INTEGER and base == 0:
        if previous_value is None:
            return 0
        # Incrementa baseado na taxa de produção
        daily_factor = get_daily_pattern_factor(timestamp) if tag_def.get("daily_pattern") else 1.0
        weekly_factor = get_weekly_pattern_factor(timestamp)
        increment = int(8 * daily_factor * weekly_factor)  # ~500 units/hora em média
        return previous_value + increment
    
    # Valor normal com distribuição gaussiana
    noise = np.random.normal(0, variation / 3)  # 99.7% dentro de ±variation
    value = base + noise
    
    # Aplicar padrões temporais
    if tag_def.get("daily_pattern"):
        daily_factor = get_daily_pattern_factor(timestamp)
        value = base * daily_factor + noise
    
    weekly_factor = get_weekly_pattern_factor(timestamp)
    value *= weekly_factor
    
    # Limitar aos valores min/max
    value = max(tag_def["min_value"], min(tag_def["max_value"], value))
    
    return value


def inject_anomaly(tag_def: Dict, timestamp: datetime, normal_value: float) -> Tuple[float, bool]:
    """
    Injeta anomalia com probabilidade definida
    Tipos de anomalias:
    - Spike: pico súbito
    - Drift: desvio gradual
    - Level shift: mudança de patamar
    """
    if random.random() > tag_def.get("anomaly_probability", 0):
        return normal_value, False
    
    anomaly_type = random.choice(["spike", "drift", "level_shift"])
    
    if anomaly_type == "spike":
        # Pico súbito (2-3x o valor normal)
        multiplier = random.uniform(2.0, 3.0)
        anomaly_value = normal_value * multiplier
    elif anomaly_type == "drift":
        # Desvio gradual (30-50% acima)
        multiplier = random.uniform(1.3, 1.5)
        anomaly_value = normal_value * multiplier
    else:  # level_shift
        # Mudança de patamar (20-40% diferença)
        shift = tag_def["variation"] * random.uniform(2.0, 4.0)
        anomaly_value = normal_value + (shift if random.random() > 0.5 else -shift)
    
    # Limitar aos valores físicos possíveis
    anomaly_value = max(tag_def["min_value"], min(tag_def["max_value"], anomaly_value))
    
    return anomaly_value, True


def check_alarm_conditions(tag_name: str, tag_def: Dict, value: float) -> List[str]:
    """Verifica se valor dispara alarmes"""
    alarms = []
    
    # Alarme crítico (maior prioridade)
    if "alarm_critical" in tag_def and value >= tag_def["alarm_critical"]:
        alarms.append("CRITICAL")
    
    # Alarme alto
    elif "alarm_high" in tag_def and value >= tag_def["alarm_high"]:
        alarms.append("HIGH")
    
    # Alarme baixo
    if "alarm_low" in tag_def and value <= tag_def["alarm_low"]:
        alarms.append("LOW")
    
    return alarms


# ========================================
# 💾 FUNÇÕES DE PERSISTÊNCIA
# ========================================

async def setup_organization_structure(session: AsyncSession) -> Dict[str, Any]:
    """Cria/recupera estrutura organizacional"""
    print("\n📋 Configurando estrutura organizacional...")
    
    # Buscar ou criar organização
    result = await session.execute(
        select(Organization).where(Organization.name == "OptiFlow Demo")
    )
    org = result.scalar_one_or_none()
    
    if not org:
        org = Organization(
            name="OptiFlow Demo",
            slug="optiflow-demo",
            is_active=True
        )
        session.add(org)
        await session.flush()
        print(f"  ✅ Organização criada: {org.name}")
    else:
        print(f"  ℹ️  Organização existente: {org.name}")
    
    await session.commit()
    
    return {
        "organization": org
    }


async def setup_devices_and_tags(session: AsyncSession, org_id: str) -> Dict[str, Any]:
    """Cria devices e tags"""
    print("\n🔧 Configurando devices e tags...")
    
    # Device 1: PLC Modbus
    result = await session.execute(
        select(Device).where(Device.name == "PLC Modbus - Produção")
    )
    device_plc = result.scalar_one_or_none()
    
    if not device_plc:
        device_plc = Device(
            name="PLC Modbus - Produção",
            description="CLP principal - controle de motores e produção",
            protocol=DeviceProtocol.MODBUS_TCP,
            is_active=True,
            connection_config={
                "host": "192.168.1.100",
                "port": 502,
                "unit_id": 1
            }
        )
        session.add(device_plc)
        await session.flush()
        print(f"  ✅ Device criado: {device_plc.name}")
    else:
        print(f"  ℹ️  Device existente: {device_plc.name}")
    
    # Device 2: Gateway OPC UA
    result = await session.execute(
        select(Device).where(Device.name == "Gateway OPC UA - Sensores")
    )
    device_opcua = result.scalar_one_or_none()
    
    if not device_opcua:
        device_opcua = Device(
            name="Gateway OPC UA - Sensores",
            description="Gateway OPC UA - sensores de temperatura, pressão e nível",
            protocol=DeviceProtocol.OPC_UA,
            is_active=True,
            connection_config={
                "endpoint": "opc.tcp://192.168.1.101:4840",
                "security_mode": "None"
            }
        )
        session.add(device_opcua)
        await session.flush()
        print(f"  ✅ Device criado: {device_opcua.name}")
    else:
        print(f"  ℹ️  Device existente: {device_opcua.name}")
    
    await session.commit()
    
    # Criar tags
    tags_created = {}
    tag_count = 0
    
    for tag_key, tag_def in TAG_DEFINITIONS.items():
        # Determinar device baseado no tipo
        if "MOTOR" in tag_key or "PRODUCTION" in tag_key or "POWER" in tag_key:
            device = device_plc
            address = f"40{1000 + tag_count}"  # Holding register
        else:
            device = device_opcua
            address = f"ns=2;s={tag_key}"  # OPC UA node
        
        result = await session.execute(
            select(Tag).where(Tag.name == tag_def["name"])
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            tag = Tag(
                device_id=device.id,
                name=tag_def["name"],
                description=tag_def["description"],
                address=address,
                data_type=tag_def["data_type"],
                category=tag_def["category"],
                is_active=True,
                scaling_enabled=False,
                unit=tag_def.get("unit"),
                metadata_={
                    "tag_key": tag_key,
                    "min_value": tag_def["min_value"],
                    "max_value": tag_def["max_value"]
                }
            )
            session.add(tag)
            tag_count += 1
        
        tags_created[tag_key] = tag
    
    await session.flush()
    await session.commit()
    
    print(f"  ✅ Tags configuradas: {len(tags_created)}")
    
    return {
        "device_plc": device_plc,
        "device_opcua": device_opcua,
        "tags": tags_created
    }


async def setup_alarm_definitions(session: AsyncSession, tags: Dict[str, Tag]) -> Dict[str, AlarmDefinition]:
    """Cria definições de alarmes"""
    print("\n🚨 Configurando alarmes...")
    
    alarms_created = {}
    
    for tag_key, tag_def in TAG_DEFINITIONS.items():
        tag = tags[tag_key]
        
        # Alarme HIGH
        if "alarm_high" in tag_def:
            result = await session.execute(
                select(AlarmDefinition).where(
                    AlarmDefinition.tag_id == tag.id,
                    AlarmDefinition.alarm_type == AlarmType.HIGH_LIMIT
                )
            )
            alarm = result.scalar_one_or_none()
            
            if not alarm:
                alarm = AlarmDefinition(
                    tag_id=tag.id,
                    name=f"{tag_def['name']} - Alto",
                    description=f"Alarme de limite alto para {tag_def['name']}",
                    alarm_type=AlarmType.HIGH_LIMIT,
                    severity=AlarmSeverity.HIGH if "alarm_critical" in tag_def else AlarmSeverity.MEDIUM,
                    threshold_high=tag_def["alarm_high"],
                    is_enabled=True
                )
                session.add(alarm)
                alarms_created[f"{tag_key}_HIGH"] = alarm
        
        # Alarme CRITICAL
        if "alarm_critical" in tag_def:
            result = await session.execute(
                select(AlarmDefinition).where(
                    AlarmDefinition.tag_id == tag.id,
                    AlarmDefinition.alarm_type == AlarmType.HIGH_LIMIT,
                    AlarmDefinition.severity == AlarmSeverity.CRITICAL
                )
            )
            alarm = result.scalar_one_or_none()
            
            if not alarm:
                alarm = AlarmDefinition(
                    tag_id=tag.id,
                    name=f"{tag_def['name']} - CRÍTICO",
                    description=f"Alarme CRÍTICO para {tag_def['name']}",
                    alarm_type=AlarmType.HIGH_LIMIT,
                    severity=AlarmSeverity.CRITICAL,
                    threshold_high=tag_def["alarm_critical"],
                    is_enabled=True
                )
                session.add(alarm)
                alarms_created[f"{tag_key}_CRITICAL"] = alarm
        
        # Alarme LOW
        if "alarm_low" in tag_def:
            result = await session.execute(
                select(AlarmDefinition).where(
                    AlarmDefinition.tag_id == tag.id,
                    AlarmDefinition.alarm_type == AlarmType.LOW_LIMIT
                )
            )
            alarm = result.scalar_one_or_none()
            
            if not alarm:
                alarm = AlarmDefinition(
                    tag_id=tag.id,
                    name=f"{tag_def['name']} - Baixo",
                    description=f"Alarme de limite baixo para {tag_def['name']}",
                    alarm_type=AlarmType.LOW_LIMIT,
                    severity=AlarmSeverity.LOW,
                    threshold_low=tag_def["alarm_low"],
                    is_enabled=True
                )
                session.add(alarm)
                alarms_created[f"{tag_key}_LOW"] = alarm
    
    await session.flush()
    await session.commit()
    
    print(f"  ✅ Alarmes configurados: {len(alarms_created)}")
    
    return alarms_created


def write_to_influxdb(tag_name: str, timestamp: datetime, value: float, 
                      metadata: Dict = None) -> None:
    """Escreve ponto no InfluxDB"""
    try:
        client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        point = Point("tag_values") \
            .tag("tag_name", tag_name) \
            .field("value", float(value)) \
            .time(timestamp)
        
        if metadata:
            for key, val in metadata.items():
                point.tag(key, str(val))
        
        write_api.write(
            bucket=settings.INFLUXDB_BUCKET,
            record=point
        )
        
        client.close()
        
    except Exception as e:
        print(f"    ⚠️  Erro ao escrever no InfluxDB: {e}")


async def create_alarm_event(session: AsyncSession, alarm_def: AlarmDefinition,
                             timestamp: datetime, value: float) -> AlarmEvent:
    """Cria evento de alarme"""
    event = AlarmEvent(
        alarm_definition_id=alarm_def.id,
        state=AlarmState.ACTIVE,
        value=value,
        timestamp=timestamp,
        message=f"Alarme disparado: {alarm_def.name} (valor: {value:.2f})"
    )
    session.add(event)
    return event


# ========================================
# 🚀 GERAÇÃO PRINCIPAL
# ========================================

async def generate_historical_data():
    """Função principal de geração"""
    
    print("🔄 Iniciando geração de dados históricos...")
    
    async with AsyncSessionLocal() as session:
        # 1. Setup estrutura
        structure = await setup_organization_structure(session)
        org = structure["organization"]
        
        # 2. Setup devices e tags
        devices_tags = await setup_devices_and_tags(session, org.id)
        tags = devices_tags["tags"]
        
        # 3. Setup alarmes
        alarms = await setup_alarm_definitions(session, tags)
        
        # 4. Gerar timestamps
        print(f"\n⏱️  Gerando {TOTAL_POINTS:,} pontos por tag...")
        timestamps = generate_timestamp_series(START_TIME, END_TIME, INTERVAL_SECONDS)
        
        # 5. Gerar dados para cada tag
        total_tags = len(TAG_DEFINITIONS)
        total_points_all_tags = total_tags * len(timestamps)
        total_anomalies = 0
        total_alarms = 0
        
        print(f"\n📊 Gerando dados para {total_tags} tags ({total_points_all_tags:,} pontos totais)...")
        print("   Isso pode levar alguns minutos...\n")
        
        previous_values = {}  # Para contadores incrementais
        alarm_active_states = {}  # Track alarmes ativos para evitar duplicatas
        
        for idx, (tag_key, tag_def) in enumerate(TAG_DEFINITIONS.items(), 1):
            tag = tags[tag_key]
            tag_name = tag_def["name"]
            
            print(f"  [{idx}/{total_tags}] {tag_name}...", end=" ", flush=True)
            
            points_written = 0
            anomalies_detected = 0
            alarms_triggered = 0
            
            # Batch de pontos para otimizar gravação
            batch_size = 1000
            batch_points = []
            
            for ts in timestamps:
                # Gerar valor base
                prev_val = previous_values.get(tag_key)
                base_value = generate_base_value(tag_def, ts, prev_val)
                
                # Injetar anomalia?
                value, is_anomaly = inject_anomaly(tag_def, ts, base_value)
                if is_anomaly:
                    anomalies_detected += 1
                    total_anomalies += 1
                
                # Atualizar valor anterior (para contadores)
                previous_values[tag_key] = value
                
                # Verificar alarmes
                alarm_conditions = check_alarm_conditions(tag_key, tag_def, value)
                
                # Escrever no InfluxDB (batch)
                metadata = {
                    "is_anomaly": "true" if is_anomaly else "false",
                    "tag_key": tag_key
                }
                if alarm_conditions:
                    metadata["alarms"] = ",".join(alarm_conditions)
                
                write_to_influxdb(tag_name, ts, value, metadata)
                points_written += 1
                
                # Criar eventos de alarme
                for alarm_condition in alarm_conditions:
                    alarm_key = f"{tag_key}_{alarm_condition}"
                    
                    # Só criar evento se alarme não está ativo
                    if alarm_key not in alarm_active_states:
                        if alarm_key in alarms:
                            await create_alarm_event(session, alarms[alarm_key], ts, value)
                            alarm_active_states[alarm_key] = ts
                            alarms_triggered += 1
                            total_alarms += 1
                
                # Limpar alarmes resolvidos (quando valor volta ao normal)
                if not alarm_conditions:
                    for key in list(alarm_active_states.keys()):
                        if key.startswith(tag_key):
                            del alarm_active_states[key]
            
            # Commit batch de alarmes
            if alarms_triggered > 0:
                await session.commit()
            
            print(f"✅ {points_written:,} pontos, {anomalies_detected} anomalias, {alarms_triggered} alarmes")
        
        print(f"""
{'='*60}
✅ GERAÇÃO CONCLUÍDA!
{'='*60}
📊 Total de pontos: {total_points_all_tags:,}
🔴 Anomalias injetadas: {total_anomalies}
🚨 Alarmes disparados: {total_alarms}
💾 Dados gravados em:
   - PostgreSQL: metadata (tags, devices, alarmes)
   - InfluxDB: time-series ({settings.INFLUXDB_BUCKET})
{'='*60}

🎯 Próximos passos:
   1. Verificar dados no Grafana: http://localhost:3001
   2. Testar endpoints de alarmes: http://localhost:8000/api/v1/alarms
   3. Treinar modelos de ML com os dados históricos
   4. Testar Agent com contexto histórico

""")


# ========================================
# 🎬 MAIN
# ========================================

if __name__ == "__main__":
    try:
        asyncio.run(generate_historical_data())
    except KeyboardInterrupt:
        print("\n\n⚠️  Geração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
