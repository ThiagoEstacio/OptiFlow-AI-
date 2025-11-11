#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo
para demonstração da visualização no frontend
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.device import Device
from app.models.tag import Tag
from app.models.alarm import Alarm
from sqlalchemy import text


async def create_sample_data():
    """Cria dados de exemplo no banco"""
    
    db = SessionLocal()
    
    try:
        print("🚀 Criando dados de exemplo...")
        
        # 1. Criar Organização
        print("\n📊 Criando organização...")
        org = Organization(
            name="OptiFlow Demo",
            slug="optiflow-demo",
            is_active=True
        )
        db.add(org)
        db.flush()
        print(f"✅ Organização criada: {org.name}")
        
        # 2. Criar Sites/Assets (hierarquia)
        print("\n🏭 Criando hierarquia de assets...")
        
        # Site Principal
        site = {
            "id": "site-fabrica-01",
            "name": "Fábrica Principal",
            "asset_type": "site",
            "organization_id": org.id,
            "is_active": True,
            "metadata": {
                "location": "São Paulo, SP",
                "capacity": "10000 units/day"
            }
        }
        
        # Áreas
        areas = [
            {
                "id": "area-producao",
                "name": "Área de Produção",
                "asset_type": "area",
                "parent_id": site["id"],
                "organization_id": org.id
            },
            {
                "id": "area-utilidades",
                "name": "Área de Utilidades",
                "asset_type": "area",
                "parent_id": site["id"],
                "organization_id": org.id
            }
        ]
        
        # Unidades
        units = [
            {
                "id": "unit-linha-01",
                "name": "Linha de Produção 01",
                "asset_type": "unit",
                "parent_id": "area-producao",
                "organization_id": org.id
            },
            {
                "id": "unit-caldeira",
                "name": "Casa de Caldeiras",
                "asset_type": "unit",
                "parent_id": "area-utilidades",
                "organization_id": org.id
            }
        ]
        
        # Equipamentos
        equipments = [
            {
                "id": "eq-motor-01",
                "name": "Motor Principal",
                "asset_type": "equipment",
                "parent_id": "unit-linha-01",
                "organization_id": org.id,
                "metadata": {"model": "WEG 100HP", "year": 2020}
            },
            {
                "id": "eq-sensor-temp-01",
                "name": "Sensor Temperatura",
                "asset_type": "equipment",
                "parent_id": "unit-linha-01",
                "organization_id": org.id
            },
            {
                "id": "eq-caldeira-01",
                "name": "Caldeira 01",
                "asset_type": "equipment",
                "parent_id": "unit-caldeira",
                "organization_id": org.id,
                "metadata": {"capacity": "10 ton/h", "pressure": "10 bar"}
            }
        ]
        
        # Inserir assets via SQL (mais rápido)
        assets = [site] + areas + units + equipments
        
        for asset in assets:
            db.execute(
                text("""
                    INSERT INTO assets (id, name, asset_type, parent_id, organization_id, is_active, metadata, created_at, updated_at)
                    VALUES (:id, :name, :asset_type, :parent_id, :organization_id, :is_active, :metadata::jsonb, now(), now())
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": asset["id"],
                    "name": asset["name"],
                    "asset_type": asset["asset_type"],
                    "parent_id": asset.get("parent_id"),
                    "organization_id": asset["organization_id"],
                    "is_active": asset.get("is_active", True),
                    "metadata": str(asset.get("metadata", {}))
                }
            )
        
        db.commit()
        print(f"✅ Assets criados: {len(assets)} itens")
        
        # 3. Criar Dispositivos
        print("\n🔌 Criando dispositivos...")
        devices = [
            Device(
                name="PLC Linha 01",
                device_type="plc",
                protocol="modbus_tcp",
                connection_string="192.168.1.100:502",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "model": "Siemens S7-1200",
                    "firmware": "V4.5"
                }
            ),
            Device(
                name="Gateway OPC UA",
                device_type="gateway",
                protocol="opcua",
                connection_string="opc.tcp://192.168.1.101:4840",
                organization_id=org.id,
                is_active=True
            )
        ]
        
        for device in devices:
            db.add(device)
        
        db.flush()
        print(f"✅ Dispositivos criados: {len(devices)}")
        
        # 4. Criar Tags
        print("\n🏷️  Criando tags...")
        tags = [
            # Motor - Linha 01
            Tag(
                name="Motor01_Current",
                description="Corrente do Motor Principal",
                tag_type="analog",
                data_type="float",
                unit="A",
                device_id=devices[0].id,
                asset_id="eq-motor-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": 0,
                    "max": 100,
                    "normal_range": [10, 80]
                }
            ),
            Tag(
                name="Motor01_Speed",
                description="Velocidade do Motor",
                tag_type="analog",
                data_type="float",
                unit="RPM",
                device_id=devices[0].id,
                asset_id="eq-motor-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": 0,
                    "max": 3600
                }
            ),
            Tag(
                name="Motor01_Status",
                description="Status do Motor",
                tag_type="digital",
                data_type="boolean",
                device_id=devices[0].id,
                asset_id="eq-motor-01",
                organization_id=org.id,
                is_active=True
            ),
            # Temperatura
            Tag(
                name="Temp01_Value",
                description="Temperatura Ambiente",
                tag_type="analog",
                data_type="float",
                unit="°C",
                device_id=devices[0].id,
                asset_id="eq-sensor-temp-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": -10,
                    "max": 100,
                    "alarm_high": 80,
                    "alarm_low": 10
                }
            ),
            # Caldeira
            Tag(
                name="Boiler01_Pressure",
                description="Pressão da Caldeira",
                tag_type="analog",
                data_type="float",
                unit="bar",
                device_id=devices[1].id,
                asset_id="eq-caldeira-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": 0,
                    "max": 15,
                    "alarm_high": 12
                }
            ),
            Tag(
                name="Boiler01_Temperature",
                description="Temperatura da Caldeira",
                tag_type="analog",
                data_type="float",
                unit="°C",
                device_id=devices[1].id,
                asset_id="eq-caldeira-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": 0,
                    "max": 200,
                    "alarm_high": 180
                }
            ),
            Tag(
                name="Boiler01_Level",
                description="Nível de Água",
                tag_type="analog",
                data_type="float",
                unit="%",
                device_id=devices[1].id,
                asset_id="eq-caldeira-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "min": 0,
                    "max": 100,
                    "alarm_low": 20
                }
            ),
            # Produção
            Tag(
                name="Production_Count",
                description="Contador de Produção",
                tag_type="analog",
                data_type="integer",
                unit="units",
                device_id=devices[0].id,
                asset_id="unit-linha-01",
                organization_id=org.id,
                is_active=True
            ),
            Tag(
                name="Production_Rate",
                description="Taxa de Produção",
                tag_type="analog",
                data_type="float",
                unit="units/min",
                device_id=devices[0].id,
                asset_id="unit-linha-01",
                organization_id=org.id,
                is_active=True,
                metadata={
                    "target": 50,
                    "min": 0,
                    "max": 100
                }
            )
        ]
        
        for tag in tags:
            db.add(tag)
        
        db.flush()
        print(f"✅ Tags criadas: {len(tags)}")
        
        # 5. Criar Alarmes de Exemplo
        print("\n🔔 Criando alarmes de exemplo...")
        alarms = [
            Alarm(
                tag_id=tags[0].id,  # Motor Current
                name="Motor01_HighCurrent",
                description="Corrente acima do normal",
                alarm_type="high",
                priority="medium",
                condition="value > 85",
                threshold_value=85.0,
                is_active=True,
                organization_id=org.id
            ),
            Alarm(
                tag_id=tags[3].id,  # Temperature
                name="Temp01_High",
                description="Temperatura alta",
                alarm_type="high",
                priority="high",
                condition="value > 80",
                threshold_value=80.0,
                is_active=True,
                organization_id=org.id
            ),
            Alarm(
                tag_id=tags[4].id,  # Boiler Pressure
                name="Boiler01_HighPressure",
                description="Pressão crítica na caldeira",
                alarm_type="high",
                priority="critical",
                condition="value > 12",
                threshold_value=12.0,
                is_active=True,
                organization_id=org.id
            )
        ]
        
        for alarm in alarms:
            db.add(alarm)
        
        db.commit()
        print(f"✅ Alarmes criados: {len(alarms)}")
        
        # 6. Gerar dados históricos no InfluxDB (simulado)
        print("\n📈 Gerando dados históricos...")
        print("⚠️  Nota: Para gerar dados reais no InfluxDB, execute o gateway ou simulador")
        print("    Comando: docker compose up -d gateway")
        
        print("\n" + "="*60)
        print("✅ DADOS DE EXEMPLO CRIADOS COM SUCESSO!")
        print("="*60)
        print(f"""
📊 Resumo:
   - Organização: 1
   - Assets: {len(assets)} (site, áreas, unidades, equipamentos)
   - Dispositivos: {len(devices)}
   - Tags: {len(tags)}
   - Alarmes: {len(alarms)}

🌐 Acesse o frontend:
   URL: http://localhost:3000
   
📍 Páginas para visualizar:
   - Tags: http://localhost:3000/tags
   - Alarms: http://localhost:3000/alarms
   - Sites: http://localhost:3000/sites
   
🔧 Para gerar dados em tempo real:
   docker compose up -d gateway
   
📚 Documentação:
   - FRONTEND_VISUALIZATION.md
   - OPERATIONS_QUICK_GUIDE.md
        """)
        
    except Exception as e:
        print(f"\n❌ Erro ao criar dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(create_sample_data())
