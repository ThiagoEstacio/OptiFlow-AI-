#!/usr/bin/env python3
"""
SmartPort - Auto Setup Tags
Configuração automática de tags para Terminal de Grãos/Açúcar

Cria automaticamente:
- Site SmartPort
- Device (Bulk Terminal PLC)
- 35+ tags para anomalia detection
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime
import os
import uuid

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://optiflow:optiflow_password@localhost:5432/optiflow"
)


class SmartPortConfigurator:
    """Configurador de tags SmartPort"""

    def __init__(self):
        self.engine = None
        self.async_session = None

        # Tag definitions (matching smartport_bulk_terminal_simulator.py)
        self.tag_definitions = {
            # ==================== CORREIA 1 ====================
            "CONV1_MOTOR_CURRENT": {
                "address": "40001", "data_type": "float", "unit": "A", "category": "energy",
                "min_value": 0.0, "max_value": 300.0, "scaling_factor": 0.1,
                "description": "Corrente motor correia 1 (anomalia: sobrecarga)", "scan_rate": 1000
            },
            "CONV1_MOTOR_SPEED": {
                "address": "40003", "data_type": "float", "unit": "RPM", "category": "process",
                "min_value": 0.0, "max_value": 2000.0, "scaling_factor": 1.0,
                "description": "Velocidade motor correia 1", "scan_rate": 1000
            },
            "CONV1_MOTOR_TEMP": {
                "address": "40005", "data_type": "float", "unit": "°C", "category": "maintenance",
                "min_value": 20.0, "max_value": 120.0, "scaling_factor": 0.1,
                "description": "Temperatura motor correia 1", "scan_rate": 2000
            },
            "CONV1_BEARING_TEMP": {
                "address": "40007", "data_type": "float", "unit": "°C", "category": "maintenance",
                "min_value": 20.0, "max_value": 120.0, "scaling_factor": 0.1,
                "description": "Temperatura rolamento correia 1 (preditiva)", "scan_rate": 2000
            },
            "CONV1_VIBRATION": {
                "address": "40009", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 15.0, "scaling_factor": 0.01,
                "description": "Vibração correia 1 (anomalia: desbalanceamento)", "scan_rate": 1000
            },
            "CONV1_FLOW_RATE": {
                "address": "40011", "data_type": "float", "unit": "t/h", "category": "production",
                "min_value": 0.0, "max_value": 1500.0, "scaling_factor": 1.0,
                "description": "Fluxo de produto correia 1", "scan_rate": 1000
            },

            # ==================== CORREIA 2 ====================
            "CONV2_MOTOR_CURRENT": {
                "address": "40013", "data_type": "float", "unit": "A", "category": "energy",
                "min_value": 0.0, "max_value": 250.0, "scaling_factor": 0.1,
                "description": "Corrente motor correia 2", "scan_rate": 1000
            },
            "CONV2_MOTOR_SPEED": {
                "address": "40015", "data_type": "float", "unit": "RPM", "category": "process",
                "min_value": 0.0, "max_value": 2000.0, "scaling_factor": 1.0,
                "description": "Velocidade motor correia 2", "scan_rate": 1000
            },
            "CONV2_MOTOR_TEMP": {
                "address": "40017", "data_type": "float", "unit": "°C", "category": "maintenance",
                "min_value": 20.0, "max_value": 120.0, "scaling_factor": 0.1,
                "description": "Temperatura motor correia 2", "scan_rate": 2000
            },
            "CONV2_VIBRATION": {
                "address": "40019", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 15.0, "scaling_factor": 0.01,
                "description": "Vibração correia 2", "scan_rate": 1000
            },

            # ==================== ELEVADOR ====================
            "ELEV1_MOTOR_CURRENT": {
                "address": "40021", "data_type": "float", "unit": "A", "category": "energy",
                "min_value": 0.0, "max_value": 400.0, "scaling_factor": 0.1,
                "description": "Corrente motor elevador (anomalia: bloqueio)", "scan_rate": 1000
            },
            "ELEV1_MOTOR_SPEED": {
                "address": "40023", "data_type": "float", "unit": "RPM", "category": "process",
                "min_value": 0.0, "max_value": 1200.0, "scaling_factor": 1.0,
                "description": "Velocidade motor elevador", "scan_rate": 1000
            },
            "ELEV1_MOTOR_TEMP": {
                "address": "40025", "data_type": "float", "unit": "°C", "category": "maintenance",
                "min_value": 20.0, "max_value": 130.0, "scaling_factor": 0.1,
                "description": "Temperatura motor elevador", "scan_rate": 2000
            },
            "ELEV1_VIBRATION": {
                "address": "40027", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 20.0, "scaling_factor": 0.01,
                "description": "Vibração elevador (anomalia: desalinhamento)", "scan_rate": 1000
            },

            # ==================== SHIPLOADER ====================
            "SHIP_MOTOR_CURRENT": {
                "address": "40029", "data_type": "float", "unit": "A", "category": "energy",
                "min_value": 0.0, "max_value": 500.0, "scaling_factor": 0.1,
                "description": "Corrente motor shiploader", "scan_rate": 1000
            },
            "SHIP_MOTOR_SPEED": {
                "address": "40031", "data_type": "float", "unit": "RPM", "category": "process",
                "min_value": 0.0, "max_value": 1500.0, "scaling_factor": 1.0,
                "description": "Velocidade motor shiploader", "scan_rate": 1000
            },
            "SHIP_FLOW_RATE": {
                "address": "40033", "data_type": "float", "unit": "t/h", "category": "production",
                "min_value": 0.0, "max_value": 3000.0, "scaling_factor": 1.0,
                "description": "Fluxo carregamento navio (KPI principal)", "scan_rate": 1000
            },
            "SHIP_VIBRATION": {
                "address": "40035", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 20.0, "scaling_factor": 0.01,
                "description": "Vibração shiploader", "scan_rate": 1000
            },
            "SHIP_BOOM_ANGLE": {
                "address": "40037", "data_type": "float", "unit": "°", "category": "process",
                "min_value": -10.0, "max_value": 90.0, "scaling_factor": 0.1,
                "description": "Ângulo lança shiploader", "scan_rate": 2000
            },

            # ==================== SILOS ====================
            "SILO1_LEVEL": {
                "address": "40039", "data_type": "float", "unit": "%", "category": "process",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Nível silo 1", "scan_rate": 5000
            },
            "SILO1_TEMP": {
                "address": "40041", "data_type": "float", "unit": "°C", "category": "quality",
                "min_value": 10.0, "max_value": 60.0, "scaling_factor": 0.1,
                "description": "Temperatura produto silo 1", "scan_rate": 10000
            },
            "SILO2_LEVEL": {
                "address": "40043", "data_type": "float", "unit": "%", "category": "process",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Nível silo 2", "scan_rate": 5000
            },

            # ==================== QUALIDADE ====================
            "PRODUCT_MOISTURE": {
                "address": "40045", "data_type": "float", "unit": "%", "category": "quality",
                "min_value": 0.0, "max_value": 25.0, "scaling_factor": 0.01,
                "description": "Umidade do produto (grãos/açúcar)", "scan_rate": 30000
            },
            "PRODUCT_TEMP": {
                "address": "40047", "data_type": "float", "unit": "°C", "category": "quality",
                "min_value": 10.0, "max_value": 50.0, "scaling_factor": 0.1,
                "description": "Temperatura do produto", "scan_rate": 10000
            },

            # ==================== KPIs ====================
            "LOADING_RATE_TOTAL": {
                "address": "40049", "data_type": "float", "unit": "t", "category": "production",
                "min_value": 0.0, "max_value": 100000.0, "scaling_factor": 1.0,
                "description": "Toneladas carregadas acumulado", "scan_rate": 10000
            },
            "VESSEL_PROGRESS": {
                "address": "40051", "data_type": "float", "unit": "%", "category": "production",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Progresso carregamento navio", "scan_rate": 10000
            },
            "ENERGY_TOTAL": {
                "address": "40053", "data_type": "float", "unit": "kWh", "category": "energy",
                "min_value": 0.0, "max_value": 999999.0, "scaling_factor": 1.0,
                "description": "Energia consumida total", "scan_rate": 10000
            },

            # ==================== STATUS ====================
            "CONV1_RUNNING": {
                "address": "00001", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Correia 1 em operação", "scan_rate": 1000
            },
            "CONV2_RUNNING": {
                "address": "00002", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Correia 2 em operação", "scan_rate": 1000
            },
            "ELEV1_RUNNING": {
                "address": "00003", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Elevador em operação", "scan_rate": 1000
            },
            "SHIP_RUNNING": {
                "address": "00004", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Shiploader em operação", "scan_rate": 1000
            },

            # ==================== ALARMES ====================
            "ALARM_HIGH_CURRENT": {
                "address": "00005", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Alarme sobrecorrente", "scan_rate": 1000
            },
            "ALARM_HIGH_VIBRATION": {
                "address": "00006", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Alarme vibração alta", "scan_rate": 1000
            },
            "ALARM_HIGH_TEMP": {
                "address": "00007", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Alarme temperatura alta", "scan_rate": 1000
            },
            "ALARM_LOW_FLOW": {
                "address": "00008", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Alarme fluxo baixo", "scan_rate": 1000
            },
        }

    async def connect(self):
        """Conectar ao banco de dados"""
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def disconnect(self):
        """Desconectar do banco"""
        if self.engine:
            await self.engine.dispose()

    async def get_or_create_site(self, session: AsyncSession) -> str:
        """Criar site SmartPort"""
        result = await session.execute(
            text("SELECT id FROM sites WHERE name = 'Terminal Santos - Grãos e Açúcar' LIMIT 1")
        )
        site = result.fetchone()

        if site:
            print(f"✓ Site encontrado: Terminal Santos (ID: {site[0]})")
            return site[0]

        site_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO sites (id, name, site_type, address, city, state, country,
                                   latitude, longitude, is_active, created_at, updated_at)
                VALUES (:id, :name, :site_type, :address, :city, :state, :country,
                        :latitude, :longitude, :is_active, :created_at, :updated_at)
            """),
            {
                "id": site_id,
                "name": "Terminal Santos - Grãos e Açúcar",
                "site_type": "smartport",
                "address": "Av. Eng. José Monteiro Fernandes, 600",
                "city": "Santos",
                "state": "SP",
                "country": "Brazil",
                "latitude": -23.9618,
                "longitude": -46.3122,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        await session.commit()
        print(f"✓ Site criado: Terminal Santos (ID: {site_id})")
        return site_id

    async def get_or_create_device(self, session: AsyncSession, site_id: str) -> str:
        """Criar device"""
        result = await session.execute(
            text("SELECT id FROM devices WHERE name = 'Bulk Terminal PLC' LIMIT 1")
        )
        device = result.fetchone()

        if device:
            print(f"✓ Device encontrado: Bulk Terminal PLC (ID: {device[0]})")
            return device[0]

        device_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO devices (id, site_id, name, protocol, ip_address, port,
                                     device_type, manufacturer, model, enabled, status,
                                     created_at, updated_at)
                VALUES (:id, :site_id, :name, :protocol, :ip_address, :port,
                        :device_type, :manufacturer, :model, :enabled, :status,
                        :created_at, :updated_at)
            """),
            {
                "id": device_id,
                "site_id": site_id,
                "name": "Bulk Terminal PLC",
                "protocol": "modbus_tcp",
                "ip_address": "localhost",
                "port": 5020,
                "device_type": "PLC",
                "manufacturer": "SmartPort Simulation",
                "model": "BULK-TERMINAL-SIM",
                "enabled": True,
                "status": "connected",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        await session.commit()
        print(f"✓ Device criado: Bulk Terminal PLC (ID: {device_id})")
        return device_id

    async def create_tag(self, session: AsyncSession, device_id: str, tag_name: str, tag_def: dict):
        """Criar tag"""
        tag_id = str(uuid.uuid4())

        await session.execute(
            text("""
                INSERT INTO tags (id, device_id, name, address, data_type, unit, category,
                                  description, min_value, max_value, scaling_factor, scan_rate,
                                  enabled, log_enabled, created_at, updated_at)
                VALUES (:id, :device_id, :name, :address, :data_type, :unit, :category,
                        :description, :min_value, :max_value, :scaling_factor, :scan_rate,
                        :enabled, :log_enabled, :created_at, :updated_at)
                ON CONFLICT (device_id, name) DO UPDATE SET
                    address = EXCLUDED.address,
                    data_type = EXCLUDED.data_type,
                    unit = EXCLUDED.unit,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    min_value = EXCLUDED.min_value,
                    max_value = EXCLUDED.max_value,
                    scaling_factor = EXCLUDED.scaling_factor,
                    scan_rate = EXCLUDED.scan_rate,
                    updated_at = EXCLUDED.updated_at
            """),
            {
                "id": tag_id,
                "device_id": device_id,
                "name": tag_name,
                "address": tag_def["address"],
                "data_type": tag_def["data_type"],
                "unit": tag_def["unit"] or None,
                "category": tag_def["category"],
                "description": tag_def["description"],
                "min_value": tag_def["min_value"],
                "max_value": tag_def["max_value"],
                "scaling_factor": tag_def["scaling_factor"],
                "scan_rate": tag_def["scan_rate"],
                "enabled": True,
                "log_enabled": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    async def setup_all_tags(self):
        """Setup completo"""
        try:
            print("\n" + "=" * 90)
            print("🚢 SmartPort - Configuração de Tags: Terminal de Grãos/Açúcar")
            print("=" * 90 + "\n")

            await self.connect()

            async with self.async_session() as session:
                print("📍 Passo 1: Criando Site SmartPort")
                site_id = await self.get_or_create_site(session)

                print("\n📡 Passo 2: Criando Device (Bulk Terminal PLC)")
                device_id = await self.get_or_create_device(session, site_id)

                print(f"\n🏷️  Passo 3: Criando {len(self.tag_definitions)} Tags")
                print("-" * 90)

                category_counts = {}
                for tag_name, tag_def in sorted(self.tag_definitions.items()):
                    await self.create_tag(session, device_id, tag_name, tag_def)
                    category = tag_def["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1
                    print(f"  ✓ {tag_name:<30} ({tag_def['category']:<12}) | {tag_def['description']}")

                await session.commit()

                print("-" * 90)
                print("\n📊 Tags por Categoria:")
                for category, count in sorted(category_counts.items()):
                    print(f"   • {category:<15}: {count} tags")

                print("\n" + "=" * 90)
                print("✅ SUCESSO! Configuração SmartPort concluída")
                print("=" * 90)
                print("\n📋 Próximos Passos:")
                print("\n   1. Iniciar o simulador:")
                print("      cd simulators")
                print("      python smartport_bulk_terminal_simulator.py")
                print("\n   2. Ver dados no frontend:")
                print("      http://localhost:3000/tags")
                print("\n   3. Criar dashboards de anomalia detection:")
                print("      http://localhost:3000/analytics")
                print("\n   🔍 ANOMALIAS SIMULADAS:")
                print("      • Rolamento degradando (Correia 1) - após 5min")
                print("      • Sobrecarga periódica (Elevador) - a cada 10min")
                print("      • Spikes de vibração (Shiploader) - aleatórios")
                print("\n" + "=" * 90 + "\n")

                return True

        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.disconnect()


async def main():
    configurator = SmartPortConfigurator()
    success = await configurator.setup_all_tags()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
