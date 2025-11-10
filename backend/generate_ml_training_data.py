"""
Script para gerar dados históricos para treinamento de modelos ML/Data Science

Este script gera:
1. Alarmes históricos (para análise de padrões)
2. Eventos de manutenção (para cálculo de MTBF/MTTR)
3. Consumo energético histórico (para regressão e LSTM)
4. Falhas de equipamentos (para análise de confiabilidade)
5. Dados operacionais correlacionados (para análise de correlação)
6. Custos de energia (para análise financeira)
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from sqlalchemy import select, text
from uuid import uuid4, UUID

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base


class MLDataGenerator:
    """Gerador de dados históricos para ML/DS"""

    def __init__(self):
        self.start_date = datetime.now() - timedelta(days=365)  # 1 ano de dados
        self.end_date = datetime.now()

        # Equipamentos do terminal portuário
        self.equipment = {
            "gates": [
                {"id": f"gate_{i}", "name": f"Gate {i}", "type": "gate", "capacity": 100}
                for i in range(1, 13)
            ],
            "motors": [
                {"id": f"motor_{i}", "name": f"Motor {i}", "type": "motor", "power_kw": 45}
                for i in range(1, 7)
            ],
            "conveyors": [
                {"id": f"conv_{i}", "name": f"Conveyor {i}", "type": "conveyor", "length_m": 50}
                for i in range(1, 4)
            ],
            "loaders": [
                {"id": f"loader_{i}", "name": f"Ship Loader {i}", "type": "loader", "capacity_ton_h": 1000}
                for i in range(1, 3)
            ]
        }

        # Tarifas de energia (R$/kWh)
        self.tariffs = {
            "peak": 0.85,       # Horário de ponta (18h-21h)
            "intermediate": 0.65,  # Horário intermediário (17h-18h, 21h-22h)
            "off_peak": 0.45,   # Horário fora de ponta (demais horários)
        }

    def get_tariff_period(self, hour: int) -> str:
        """Retorna o período tarifário baseado na hora"""
        if 18 <= hour < 21:
            return "peak"
        elif 17 <= hour < 18 or 21 <= hour < 22:
            return "intermediate"
        else:
            return "off_peak"

    def generate_alarms(self, num_days: int = 365) -> List[Dict[str, Any]]:
        """
        Gera alarmes históricos com padrões realistas

        Padrões incluídos:
        - Mais alarmes em horário de pico de operação (8h-18h)
        - Correlação entre equipamentos (falha em cascata)
        - Sazonalidade (mais problemas no verão - sobrecarga térmica)
        - Degradação progressiva (mais alarmes próximo a manutenção)
        """
        alarms = []
        current_date = self.start_date

        # Histórico de manutenção (última manutenção de cada equipamento)
        last_maintenance = {eq["id"]: current_date for category in self.equipment.values() for eq in category}

        for day in range(num_days):
            current_date = self.start_date + timedelta(days=day)

            # Mais alarmes no verão (dezembro-fevereiro)
            season_factor = 1.5 if current_date.month in [12, 1, 2] else 1.0

            # Gerar alarmes ao longo do dia
            num_alarms = int(np.random.poisson(3) * season_factor)

            for _ in range(num_alarms):
                # Horário de operação (mais alarmes entre 8h-18h)
                if random.random() < 0.7:  # 70% dos alarmes em horário comercial
                    hour = random.randint(8, 18)
                else:
                    hour = random.randint(0, 23)

                alarm_time = current_date.replace(hour=hour, minute=random.randint(0, 59))

                # Selecionar equipamento
                category = random.choice(list(self.equipment.keys()))
                equipment = random.choice(self.equipment[category])

                # Dias desde última manutenção
                days_since_maintenance = (alarm_time - last_maintenance[equipment["id"]]).days

                # Probabilidade de alarme aumenta com tempo desde manutenção
                degradation_factor = min(days_since_maintenance / 90, 2.0)  # Máximo 2x após 90 dias

                # Tipos de alarme por categoria de equipamento
                alarm_types = {
                    "gates": [
                        ("high_temperature", 0.3 * degradation_factor),
                        ("position_error", 0.2),
                        ("motor_overload", 0.15 * degradation_factor),
                        ("communication_error", 0.1),
                        ("sensor_failure", 0.15),
                        ("vibration_high", 0.1 * degradation_factor),
                    ],
                    "motors": [
                        ("overheating", 0.35 * degradation_factor),
                        ("overcurrent", 0.25 * degradation_factor),
                        ("bearing_failure", 0.2 * degradation_factor),
                        ("phase_imbalance", 0.1),
                        ("insulation_fault", 0.1),
                    ],
                    "conveyors": [
                        ("belt_misalignment", 0.3),
                        ("motor_overload", 0.25 * degradation_factor),
                        ("bearing_noise", 0.2 * degradation_factor),
                        ("speed_deviation", 0.15),
                        ("emergency_stop", 0.1),
                    ],
                    "loaders": [
                        ("hydraulic_pressure_low", 0.3),
                        ("overload", 0.25),
                        ("positioning_error", 0.2),
                        ("mechanical_wear", 0.15 * degradation_factor),
                        ("control_system_fault", 0.1),
                    ],
                }

                alarm_list = alarm_types[category]
                alarm_type = random.choices([a[0] for a in alarm_list], weights=[a[1] for a in alarm_list])[0]

                # Severidade baseada no tipo
                severity_map = {
                    "high_temperature": "high",
                    "overheating": "critical",
                    "overcurrent": "high",
                    "motor_overload": "high",
                    "communication_error": "medium",
                    "sensor_failure": "medium",
                    "emergency_stop": "critical",
                    "bearing_failure": "critical",
                    "belt_misalignment": "medium",
                    "hydraulic_pressure_low": "high",
                    "overload": "high",
                }

                severity = severity_map.get(alarm_type, "low")

                # Duração do alarme (minutos)
                if severity == "critical":
                    duration = random.randint(30, 180)  # 30min - 3h
                elif severity == "high":
                    duration = random.randint(15, 90)   # 15min - 1.5h
                else:
                    duration = random.randint(5, 30)    # 5min - 30min

                alarm = {
                    "id": str(uuid4()),
                    "equipment_id": equipment["id"],
                    "equipment_name": equipment["name"],
                    "equipment_type": equipment["type"],
                    "alarm_type": alarm_type,
                    "severity": severity,
                    "start_time": alarm_time,
                    "end_time": alarm_time + timedelta(minutes=duration),
                    "duration_minutes": duration,
                    "acknowledged": True,
                    "acknowledged_by": "operator" if random.random() > 0.1 else None,
                    "resolved": True,
                    "resolution_notes": f"Resolved after {duration} minutes",
                    "days_since_maintenance": days_since_maintenance,
                }

                alarms.append(alarm)

                # Se alarme crítico, agendar manutenção
                if severity == "critical" and random.random() > 0.3:
                    last_maintenance[equipment["id"]] = alarm_time + timedelta(days=random.randint(1, 3))

        return alarms

    def generate_maintenance_events(self, alarms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gera eventos de manutenção baseado em alarmes

        Calcula:
        - MTBF (Mean Time Between Failures)
        - MTTR (Mean Time To Repair)
        - Tipos de manutenção (preventiva, corretiva, preditiva)
        """
        maintenance_events = []

        # Agrupar alarmes críticos por equipamento
        critical_alarms = {}
        for alarm in alarms:
            if alarm["severity"] == "critical":
                eq_id = alarm["equipment_id"]
                if eq_id not in critical_alarms:
                    critical_alarms[eq_id] = []
                critical_alarms[eq_id].append(alarm)

        # Gerar eventos de manutenção
        for eq_id, eq_alarms in critical_alarms.items():
            # Ordenar por data
            eq_alarms.sort(key=lambda x: x["start_time"])

            for i, alarm in enumerate(eq_alarms):
                # Tempo desde última falha (MTBF)
                if i > 0:
                    time_since_last = (alarm["start_time"] - eq_alarms[i-1]["start_time"]).total_seconds() / 3600
                else:
                    time_since_last = None

                # Tempo de reparo (MTTR) - baseado na duração do alarme + tempo de manutenção
                mttr_hours = alarm["duration_minutes"] / 60 + random.uniform(0.5, 4.0)

                # Tipo de manutenção
                maintenance_type = random.choices(
                    ["corrective", "preventive", "predictive"],
                    weights=[0.6, 0.3, 0.1]
                )[0]

                # Custo estimado (R$)
                cost_base = {
                    "gate": 1500,
                    "motor": 3000,
                    "conveyor": 2500,
                    "loader": 5000,
                }

                equipment_type = alarm["equipment_type"]
                cost = cost_base.get(equipment_type, 2000) * random.uniform(0.7, 1.5)

                maintenance = {
                    "id": str(uuid4()),
                    "equipment_id": eq_id,
                    "equipment_name": alarm["equipment_name"],
                    "equipment_type": equipment_type,
                    "alarm_id": alarm["id"],
                    "maintenance_type": maintenance_type,
                    "start_time": alarm["end_time"],
                    "end_time": alarm["end_time"] + timedelta(hours=mttr_hours),
                    "mttr_hours": round(mttr_hours, 2),
                    "mtbf_hours": round(time_since_last, 2) if time_since_last else None,
                    "cost_brl": round(cost, 2),
                    "technician": f"Tech-{random.randint(1, 10)}",
                    "parts_replaced": random.choice([
                        "bearing",
                        "motor",
                        "sensor",
                        "control_board",
                        "hydraulic_pump",
                        "belt",
                        "none"
                    ]),
                    "notes": f"{maintenance_type.title()} maintenance performed",
                }

                maintenance_events.append(maintenance)

        return maintenance_events

    def generate_energy_consumption(self, num_days: int = 365) -> List[Dict[str, Any]]:
        """
        Gera dados de consumo energético com padrões realistas para treinar LSTM

        Padrões incluídos:
        - Ciclo diário (mais consumo durante operação 6h-20h)
        - Ciclo semanal (menos consumo fim de semana)
        - Sazonalidade anual (mais consumo no verão devido a refrigeração)
        - Correlação com produção
        - Tendência de eficiência (melhoria ao longo do tempo)
        - Eventos de manutenção (picos/quedas)
        """
        energy_data = []
        current_date = self.start_date

        # Baseline de consumo por equipamento (kW)
        baseline_power = {
            "gates": 5,      # kW por gate
            "motors": 45,    # kW por motor
            "conveyors": 30, # kW por conveyor
            "loaders": 150,  # kW por loader
        }

        for day in range(num_days):
            current_date = self.start_date + timedelta(days=day)

            # Fator sazonal (verão = mais consumo de refrigeração)
            month = current_date.month
            seasonal_factor = 1.0
            if month in [12, 1, 2]:  # Verão
                seasonal_factor = 1.25
            elif month in [6, 7, 8]:  # Inverno
                seasonal_factor = 0.85

            # Fator semanal (menos operação fim de semana)
            weekday = current_date.weekday()
            weekly_factor = 0.4 if weekday >= 5 else 1.0  # Sábado/Domingo

            # Tendência de eficiência (melhoria de 0.5% ao mês)
            efficiency_trend = 1.0 - (day / 365) * 0.06  # 6% de melhoria ao ano

            # Gerar dados hora a hora
            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)

                # Fator de operação por hora
                if 6 <= hour <= 20:
                    operation_factor = 0.8 + random.uniform(-0.1, 0.2)  # 80-100% operação
                elif 20 < hour <= 22:
                    operation_factor = 0.5 + random.uniform(-0.1, 0.1)  # 40-60% operação
                else:
                    operation_factor = 0.2 + random.uniform(-0.05, 0.05)  # 15-25% operação

                # Calcular consumo total
                total_consumption = 0
                equipment_consumption = {}

                for category, equipment_list in self.equipment.items():
                    category_power = baseline_power.get(category, 10)
                    num_equipment = len(equipment_list)

                    # Consumo com todos os fatores
                    consumption = (
                        category_power *
                        num_equipment *
                        operation_factor *
                        weekly_factor *
                        seasonal_factor *
                        efficiency_trend *
                        (1 + random.uniform(-0.05, 0.05))  # Ruído ±5%
                    )

                    equipment_consumption[category] = round(consumption, 2)
                    total_consumption += consumption

                # Calcular produção (toneladas/hora) correlacionada com consumo
                production = total_consumption * random.uniform(1.5, 2.5) * operation_factor

                # Período tarifário e custo
                tariff_period = self.get_tariff_period(hour)
                tariff_rate = self.tariffs[tariff_period]
                cost = total_consumption * tariff_rate

                # Eficiência energética (kWh por tonelada)
                efficiency = total_consumption / production if production > 0 else 0

                energy_record = {
                    "timestamp": timestamp,
                    "hour": hour,
                    "day_of_week": weekday,
                    "day_of_year": day,
                    "month": month,

                    # Consumo
                    "total_consumption_kwh": round(total_consumption, 2),
                    "gates_consumption_kwh": equipment_consumption["gates"],
                    "motors_consumption_kwh": equipment_consumption["motors"],
                    "conveyors_consumption_kwh": equipment_consumption["conveyors"],
                    "loaders_consumption_kwh": equipment_consumption["loaders"],

                    # Produção
                    "production_tons": round(production, 2),

                    # Eficiência
                    "efficiency_kwh_per_ton": round(efficiency, 4),

                    # Custo
                    "tariff_period": tariff_period,
                    "tariff_rate_brl": tariff_rate,
                    "cost_brl": round(cost, 2),

                    # Fatores
                    "operation_factor": round(operation_factor, 2),
                    "seasonal_factor": round(seasonal_factor, 2),
                    "weekly_factor": round(weekly_factor, 2),
                    "efficiency_trend": round(efficiency_trend, 4),
                }

                energy_data.append(energy_record)

        return energy_data

    def generate_operational_events(self, num_days: int = 365) -> List[Dict[str, Any]]:
        """
        Gera eventos operacionais para análise de correlação

        - Chegada de navios
        - Operações de carga/descarga
        - Paradas programadas
        - Condições climáticas
        """
        events = []
        current_date = self.start_date

        for day in range(num_days):
            current_date = self.start_date + timedelta(days=day)

            # Chegada de navios (1-3 por dia útil)
            if current_date.weekday() < 5:  # Segunda a sexta
                num_ships = random.randint(1, 3)

                for ship in range(num_ships):
                    arrival_hour = random.randint(6, 18)
                    arrival_time = current_date.replace(hour=arrival_hour, minute=random.randint(0, 59))

                    # Duração da operação (6-24 horas)
                    duration_hours = random.uniform(6, 24)
                    departure_time = arrival_time + timedelta(hours=duration_hours)

                    # Tonelagem
                    tonnage = random.randint(20000, 80000)

                    event = {
                        "id": str(uuid4()),
                        "event_type": "ship_operation",
                        "ship_name": f"MV-{random.randint(1000, 9999)}",
                        "arrival_time": arrival_time,
                        "departure_time": departure_time,
                        "duration_hours": round(duration_hours, 2),
                        "tonnage": tonnage,
                        "cargo_type": random.choice(["grain", "soy", "corn", "fertilizer"]),
                        "operation_type": random.choice(["loading", "unloading"]),
                    }

                    events.append(event)

            # Condições climáticas
            weather = {
                "id": str(uuid4()),
                "event_type": "weather",
                "date": current_date,
                "temperature_c": random.uniform(15, 35),
                "humidity_percent": random.uniform(40, 90),
                "wind_speed_kmh": random.uniform(0, 40),
                "rainfall_mm": max(0, random.gauss(2, 5)),
                "conditions": random.choice(["clear", "cloudy", "rainy", "windy"]),
            }

            events.append(weather)

        return events

    async def save_to_influxdb(self, energy_data: List[Dict[str, Any]]):
        """Salva dados de energia no InfluxDB"""
        try:
            from influxdb_client import InfluxDBClient, Point
            from influxdb_client.client.write_api import SYNCHRONOUS

            # Configuração do InfluxDB
            url = "http://localhost:8086"
            token = "optiflow_token"
            org = "optiflow"
            bucket = "optiflow_data"

            client = InfluxDBClient(url=url, token=token, org=org)
            write_api = client.write_api(write_options=SYNCHRONOUS)

            points = []
            for record in energy_data:
                point = Point("energy_consumption") \
                    .time(record["timestamp"]) \
                    .field("total_consumption_kwh", record["total_consumption_kwh"]) \
                    .field("production_tons", record["production_tons"]) \
                    .field("efficiency_kwh_per_ton", record["efficiency_kwh_per_ton"]) \
                    .field("cost_brl", record["cost_brl"]) \
                    .tag("tariff_period", record["tariff_period"])

                points.append(point)

            # Escrever em lotes de 1000
            batch_size = 1000
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                write_api.write(bucket=bucket, record=batch)
                print(f"Written {min(i+batch_size, len(points))}/{len(points)} energy records to InfluxDB")

            client.close()
            print(f"✅ Successfully saved {len(energy_data)} energy records to InfluxDB")

        except Exception as e:
            print(f"⚠️ Error saving to InfluxDB: {e}")
            print("Continuing with PostgreSQL only...")

    async def save_to_postgresql(
        self,
        alarms: List[Dict[str, Any]],
        maintenance: List[Dict[str, Any]],
        events: List[Dict[str, Any]]
    ):
        """Salva dados no PostgreSQL"""
        async with AsyncSessionLocal() as session:
            try:
                # Criar tabelas temporárias para dados históricos
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS historical_alarms (
                        id UUID PRIMARY KEY,
                        equipment_id VARCHAR(100),
                        equipment_name VARCHAR(200),
                        equipment_type VARCHAR(50),
                        alarm_type VARCHAR(100),
                        severity VARCHAR(20),
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_minutes INTEGER,
                        acknowledged BOOLEAN,
                        acknowledged_by VARCHAR(100),
                        resolved BOOLEAN,
                        resolution_notes TEXT,
                        days_since_maintenance INTEGER
                    )
                """))

                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS historical_maintenance (
                        id UUID PRIMARY KEY,
                        equipment_id VARCHAR(100),
                        equipment_name VARCHAR(200),
                        equipment_type VARCHAR(50),
                        alarm_id UUID,
                        maintenance_type VARCHAR(50),
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        mttr_hours FLOAT,
                        mtbf_hours FLOAT,
                        cost_brl FLOAT,
                        technician VARCHAR(100),
                        parts_replaced VARCHAR(200),
                        notes TEXT
                    )
                """))

                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS historical_operational_events (
                        id UUID PRIMARY KEY,
                        event_type VARCHAR(50),
                        event_data JSONB,
                        timestamp TIMESTAMP
                    )
                """))

                await session.commit()

                # Inserir alarmes
                for alarm in alarms:
                    await session.execute(
                        text("""
                            INSERT INTO historical_alarms VALUES (
                                :id, :equipment_id, :equipment_name, :equipment_type,
                                :alarm_type, :severity, :start_time, :end_time,
                                :duration_minutes, :acknowledged, :acknowledged_by,
                                :resolved, :resolution_notes, :days_since_maintenance
                            ) ON CONFLICT (id) DO NOTHING
                        """),
                        alarm
                    )

                # Inserir manutenções
                for maint in maintenance:
                    await session.execute(
                        text("""
                            INSERT INTO historical_maintenance VALUES (
                                :id, :equipment_id, :equipment_name, :equipment_type,
                                :alarm_id, :maintenance_type, :start_time, :end_time,
                                :mttr_hours, :mtbf_hours, :cost_brl, :technician,
                                :parts_replaced, :notes
                            ) ON CONFLICT (id) DO NOTHING
                        """),
                        maint
                    )

                # Inserir eventos
                for event in events:
                    event_type = event.pop("event_type")
                    timestamp = event.get("date") or event.get("arrival_time") or datetime.now()

                    await session.execute(
                        text("""
                            INSERT INTO historical_operational_events (id, event_type, event_data, timestamp)
                            VALUES (:id, :event_type, :event_data::jsonb, :timestamp)
                            ON CONFLICT (id) DO NOTHING
                        """),
                        {
                            "id": event["id"],
                            "event_type": event_type,
                            "event_data": str(event),
                            "timestamp": timestamp
                        }
                    )

                await session.commit()

                print(f"✅ Saved {len(alarms)} alarms to PostgreSQL")
                print(f"✅ Saved {len(maintenance)} maintenance events to PostgreSQL")
                print(f"✅ Saved {len(events)} operational events to PostgreSQL")

            except Exception as e:
                print(f"❌ Error saving to PostgreSQL: {e}")
                await session.rollback()
                raise

    async def generate_and_save_all(self):
        """Gera e salva todos os dados"""
        print("🚀 Iniciando geração de dados históricos para ML/Data Science...\n")

        # Gerar dados
        print("📊 Gerando alarmes históricos...")
        alarms = self.generate_alarms(num_days=365)
        print(f"✅ Gerados {len(alarms)} alarmes\n")

        print("🔧 Gerando eventos de manutenção...")
        maintenance = self.generate_maintenance_events(alarms)
        print(f"✅ Gerados {len(maintenance)} eventos de manutenção\n")

        print("⚡ Gerando dados de consumo energético...")
        energy_data = self.generate_energy_consumption(num_days=365)
        print(f"✅ Gerados {len(energy_data)} registros de energia (8760 horas)\n")

        print("📋 Gerando eventos operacionais...")
        events = self.generate_operational_events(num_days=365)
        print(f"✅ Gerados {len(events)} eventos operacionais\n")

        # Salvar dados
        print("💾 Salvando dados no banco...")
        await self.save_to_postgresql(alarms, maintenance, events)
        await self.save_to_influxdb(energy_data)

        print("\n" + "="*80)
        print("✅ DADOS GERADOS COM SUCESSO!")
        print("="*80)
        print(f"\n📊 Resumo:")
        print(f"  • Alarmes: {len(alarms)}")
        print(f"  • Manutenções: {len(maintenance)}")
        print(f"  • Dados de energia: {len(energy_data)} (1 ano, hora a hora)")
        print(f"  • Eventos operacionais: {len(events)}")

        # Calcular métricas
        print(f"\n📈 Métricas calculáveis:")

        # MTBF/MTTR
        mtbf_values = [m["mtbf_hours"] for m in maintenance if m["mtbf_hours"]]
        mttr_values = [m["mttr_hours"] for m in maintenance]

        if mtbf_values:
            print(f"  • MTBF médio: {np.mean(mtbf_values):.1f} horas")
        if mttr_values:
            print(f"  • MTTR médio: {np.mean(mttr_values):.1f} horas")

        # Custos
        total_maintenance_cost = sum(m["cost_brl"] for m in maintenance)
        total_energy_cost = sum(e["cost_brl"] for e in energy_data)

        print(f"  • Custo total de manutenção: R$ {total_maintenance_cost:,.2f}")
        print(f"  • Custo total de energia: R$ {total_energy_cost:,.2f}")
        print(f"  • Custo total: R$ {(total_maintenance_cost + total_energy_cost):,.2f}")

        # Eficiência energética
        avg_efficiency = np.mean([e["efficiency_kwh_per_ton"] for e in energy_data])
        print(f"  • Eficiência média: {avg_efficiency:.4f} kWh/ton")

        print(f"\n🤖 Pronto para treinar modelos ML:")
        print(f"  ✓ Regressão linear (consumo energético)")
        print(f"  ✓ LSTM (previsão de séries temporais)")
        print(f"  ✓ Análise de correlação (variáveis operacionais)")
        print(f"  ✓ Análise de confiabilidade (MTBF/MTTR)")
        print(f"  ✓ Detecção de anomalias (alarmes)")
        print(f"  ✓ Otimização de custos (tarifas de energia)")


async def main():
    """Função principal"""
    generator = MLDataGenerator()
    await generator.generate_and_save_all()


if __name__ == "__main__":
    asyncio.run(main())
