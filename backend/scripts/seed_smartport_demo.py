"""
Seed SmartPort Demo Data

Creates realistic demo data for SmartPort MVP client presentations.

Includes:
- 1 demo organization and port site
- 2 berths (Berço 1 - occupied, Berço 2 - available)
- 4 vessels (different statuses: loading, waiting, completed, scheduled)
- 3 loading operations (1 in progress, 2 completed)
- Multiple cargos (soybean, corn, sugar)
- 8 port equipment items (conveyors, elevators, shiploaders)
- Operation events for timeline
- Maintenance records for predictive maintenance demo

Usage:
    python scripts/seed_smartport_demo.py
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.organization import Organization, Site
from app.models.port.vessel import Vessel, VesselType, VesselStatus
from app.models.port.berth import Berth, BerthType, BerthStatus
from app.models.port.loading_operation import (
    LoadingOperation,
    Cargo,
    OperationEvent,
    OperationType,
    OperationStatus,
    CommodityType,
)
from app.models.port.equipment import (
    PortEquipment,
    MaintenanceRecord,
    EquipmentType,
    EquipmentStatus,
    MaintenanceType,
)


async def seed_demo_data():
    """Seed SmartPort demo data"""
    print("🚢 Starting SmartPort Demo Data Seed...")

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # ===== 1. CREATE ORGANIZATION & SITE =====
            print("\n📦 Creating demo organization and port site...")

            org = Organization(
                id=uuid.uuid4(),
                name="Terminal Santos Grãos S.A.",
                slug="terminal-santos",
                description="Terminal portuário especializado em grãos e commodities agrícolas",
                contact_name="Carlos Silva",
                contact_email="carlos.silva@terminalsantos.com.br",
                contact_phone="+55 13 3219-4500",
                is_active=True,
                settings={
                    "timezone": "America/Sao_Paulo",
                    "currency": "BRL",
                    "language": "pt-BR",
                }
            )
            session.add(org)
            await session.flush()

            site = Site(
                id=uuid.uuid4(),
                organization_id=org.id,
                name="Terminal Santos - Cais Principal",
                slug="santos-principal",
                description="Terminal de granéis sólidos vegetais - Porto de Santos",
                address="Av. Conselheiro Rodrigues Alves, 1245",
                city="Santos",
                state="São Paulo",
                country="Brasil",
                postal_code="11013-001",
                latitude="-23.9575",
                longitude="-46.3328",
                site_type="port",
                is_active=True,
                settings={
                    "operating_hours": "24/7",
                    "max_vessels_simultaneous": 2,
                    "main_commodities": ["soybean", "corn", "sugar", "wheat"],
                }
            )
            session.add(site)
            await session.flush()

            print(f"✅ Organization: {org.name}")
            print(f"✅ Site: {site.name}")

            # ===== 2. CREATE BERTHS =====
            print("\n⚓ Creating berths...")

            berth1 = Berth(
                id=uuid.uuid4(),
                site_id=site.id,
                name="Berço 1 - Graneleiro Principal",
                code="B1",
                description="Berço de granéis sólidos com 3 shiploaders",
                berth_type=BerthType.BULK,
                length=300.0,  # meters
                depth=15.5,  # meters
                max_draft=14.0,
                max_dwt=100000.0,  # tons
                max_loa=280.0,
                loading_rate=3500.0,  # tons/hour design capacity
                unloading_rate=2800.0,
                storage_capacity=150000.0,  # tons
                num_shiploaders=3,
                num_conveyors=5,
                num_cranes=0,
                latitude="-23.9580",
                longitude="-46.3335",
                status=BerthStatus.OCCUPIED,
                commodities=["soybean", "corn", "wheat", "soybean_meal"],
                is_active=True,
            )
            session.add(berth1)

            berth2 = Berth(
                id=uuid.uuid4(),
                site_id=site.id,
                name="Berço 2 - Graneleiro Secundário",
                code="B2",
                description="Berço de granéis sólidos com 2 shiploaders",
                berth_type=BerthType.BULK,
                length=250.0,
                depth=13.0,
                max_draft=12.5,
                max_dwt=75000.0,
                max_loa=240.0,
                loading_rate=2500.0,
                unloading_rate=2000.0,
                storage_capacity=100000.0,
                num_shiploaders=2,
                num_conveyors=4,
                num_cranes=0,
                latitude="-23.9590",
                longitude="-46.3340",
                status=BerthStatus.AVAILABLE,
                commodities=["sugar", "soybean", "corn"],
                is_active=True,
            )
            session.add(berth2)

            await session.flush()
            print(f"✅ {berth1.code}: {berth1.name} - {berth1.status.value}")
            print(f"✅ {berth2.code}: {berth2.name} - {berth2.status.value}")

            # ===== 3. CREATE VESSELS =====
            print("\n🚢 Creating vessels...")

            # Vessel 1: Currently loading at Berth 1
            vessel1 = Vessel(
                id=uuid.uuid4(),
                site_id=site.id,
                name="MV GRAIN CARRIER",
                imo_number="IMO9876543",
                call_sign="V7AB2",
                mmsi="355123456",
                vessel_type=VesselType.BULK_CARRIER,
                flag="Libéria",
                classification="Lloyd's Register",
                dwt=82500.0,
                grt=45200.0,
                nrt=28100.0,
                length=225.0,
                beam=32.2,
                draft=12.8,
                capacity=82500.0,
                owner="Global Shipping Ltd",
                operator="Grain Logistics Inc",
                agent="Santos Port Agents",
                status=VesselStatus.LOADING,
                current_berth_id=berth1.id,
                eta=datetime.utcnow() - timedelta(days=2),
                ata=datetime.utcnow() - timedelta(days=1, hours=18),
                etb=datetime.utcnow() - timedelta(days=1, hours=16),
                atb=datetime.utcnow() - timedelta(days=1, hours=14),
                etc=datetime.utcnow() + timedelta(hours=10),
                etd=datetime.utcnow() + timedelta(hours=12),
                voyage_number="GCAR2025-015",
                previous_port="Paranaguá, Brasil",
                next_port="Rotterdam, Holanda",
                notes="Carregamento de soja para exportação - Cliente: ADM",
            )
            session.add(vessel1)

            # Vessel 2: Waiting at anchorage
            vessel2 = Vessel(
                id=uuid.uuid4(),
                site_id=site.id,
                name="MV BULK EXPLORER",
                imo_number="IMO9765432",
                call_sign="C6PQ9",
                mmsi="355234567",
                vessel_type=VesselType.BULK_CARRIER,
                flag="Panamá",
                classification="DNV-GL",
                dwt=75000.0,
                grt=42000.0,
                nrt=26000.0,
                length=210.0,
                beam=30.5,
                draft=11.5,
                capacity=75000.0,
                owner="Ocean Carriers S.A.",
                operator="Bulk Transport Co",
                agent="Santos Port Agents",
                status=VesselStatus.ANCHORED,
                eta=datetime.utcnow() - timedelta(hours=12),
                ata=datetime.utcnow() - timedelta(hours=6),
                etb=datetime.utcnow() + timedelta(hours=8),
                etc=datetime.utcnow() + timedelta(days=1, hours=20),
                etd=datetime.utcnow() + timedelta(days=2),
                voyage_number="BEXP2025-022",
                previous_port="Rio Grande, Brasil",
                next_port="Shanghai, China",
                notes="Aguardando berço para carregamento de milho",
            )
            session.add(vessel2)

            # Vessel 3: Recently completed and departed
            vessel3 = Vessel(
                id=uuid.uuid4(),
                site_id=site.id,
                name="MV EXPORT CHAMPION",
                imo_number="IMO9654321",
                call_sign="3FMU8",
                mmsi="355345678",
                vessel_type=VesselType.BULK_CARRIER,
                flag="Malta",
                classification="Bureau Veritas",
                dwt=95000.0,
                grt=52000.0,
                nrt=32000.0,
                length=245.0,
                beam=36.0,
                draft=13.5,
                capacity=95000.0,
                owner="Mediterranean Shipping",
                operator="Export Carriers Ltd",
                agent="Santos Port Agents",
                status=VesselStatus.DEPARTED,
                eta=datetime.utcnow() - timedelta(days=5),
                ata=datetime.utcnow() - timedelta(days=4, hours=20),
                etb=datetime.utcnow() - timedelta(days=4, hours=18),
                atb=datetime.utcnow() - timedelta(days=4, hours=16),
                etc=datetime.utcnow() - timedelta(days=2, hours=10),
                atc=datetime.utcnow() - timedelta(days=2, hours=8),
                etd=datetime.utcnow() - timedelta(days=2, hours=6),
                atd=datetime.utcnow() - timedelta(days=2, hours=4),
                voyage_number="EXCH2025-007",
                previous_port="Santos, Brasil",
                next_port="Hamburg, Alemanha",
                notes="Carregamento concluído com sucesso - 94.850 toneladas de soja",
            )
            session.add(vessel3)

            # Vessel 4: Scheduled to arrive
            vessel4 = Vessel(
                id=uuid.uuid4(),
                site_id=site.id,
                name="MV OCEAN LIBERTY",
                imo_number="IMO9543210",
                call_sign="9HA3456",
                mmsi="355456789",
                vessel_type=VesselType.BULK_CARRIER,
                flag="Marshall Islands",
                classification="ABS",
                dwt=78000.0,
                grt=44000.0,
                nrt=27000.0,
                length=220.0,
                beam=31.5,
                draft=12.0,
                capacity=78000.0,
                owner="Liberty Shipping Co",
                operator="Grain Carriers Inc",
                agent="Santos Port Agents",
                status=VesselStatus.SCHEDULED,
                eta=datetime.utcnow() + timedelta(days=2, hours=14),
                etb=datetime.utcnow() + timedelta(days=2, hours=18),
                etc=datetime.utcnow() + timedelta(days=4, hours=10),
                etd=datetime.utcnow() + timedelta(days=4, hours=14),
                voyage_number="OLIB2025-031",
                previous_port="Navegando de Itajaí",
                next_port="Singapura",
                notes="Programado para carregamento de farelo de soja",
            )
            session.add(vessel4)

            await session.flush()

            # Update berth1 with current vessel
            berth1.current_vessel_id = vessel1.id
            await session.flush()

            print(f"✅ {vessel1.name} - {vessel1.status.value} @ {berth1.code}")
            print(f"✅ {vessel2.name} - {vessel2.status.value}")
            print(f"✅ {vessel3.name} - {vessel3.status.value}")
            print(f"✅ {vessel4.name} - {vessel4.status.value}")

            # ===== 4. CREATE PORT EQUIPMENT =====
            print("\n🏭 Creating port equipment...")

            equipment_list = [
                # Conveyors
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth1.id,
                    name="Correia Transportadora TC-4515",
                    code="TC4515",
                    equipment_type=EquipmentType.CONVEYOR,
                    manufacturer="Continental AG",
                    model="ST-2500",
                    serial_number="CT2500-2020-045",
                    year_manufactured=2020,
                    year_installed=2021,
                    rated_capacity=2500.0,
                    max_capacity=2800.0,
                    design_speed=3.5,  # m/s
                    power_rating=450.0,  # kW
                    status=EquipmentStatus.OPERATING,
                    health_score=92.5,
                    failure_probability=8.5,
                    total_operating_hours=12450.0,
                    total_downtime_hours=125.0,
                    total_throughput=2850000.0,
                    current_throughput=1850.0,
                    last_maintenance_date=datetime.utcnow() - timedelta(days=45),
                    next_maintenance_date=datetime.utcnow() + timedelta(days=135),
                    maintenance_interval_hours=720.0,
                    alarm_thresholds={
                        "temperature_high": 75,
                        "vibration_high": 4.5,
                        "current_high": 380,
                        "speed_low": 3.0
                    },
                    criticality="high",
                ),
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth1.id,
                    name="Correia Transportadora TC-2521",
                    code="TC2521",
                    equipment_type=EquipmentType.CONVEYOR,
                    manufacturer="Metso",
                    model="MTC-2200",
                    serial_number="MTC2200-2019-112",
                    year_manufactured=2019,
                    year_installed=2020,
                    rated_capacity=2200.0,
                    max_capacity=2500.0,
                    design_speed=3.2,
                    power_rating=420.0,
                    status=EquipmentStatus.OPERATING,
                    health_score=73.0,  # Lower health - candidate for predictive maintenance
                    failure_probability=27.0,  # Higher failure risk
                    total_operating_hours=18200.0,
                    total_downtime_hours=285.0,
                    total_throughput=3920000.0,
                    current_throughput=1650.0,
                    last_maintenance_date=datetime.utcnow() - timedelta(days=90),
                    next_maintenance_date=datetime.utcnow() + timedelta(days=30),
                    maintenance_interval_hours=720.0,
                    alarm_thresholds={
                        "temperature_high": 70,
                        "vibration_high": 4.0,
                        "current_high": 350,
                        "speed_low": 2.8
                    },
                    criticality="critical",
                    notes="⚠️ Atenção: Rolamento apresentando temperatura elevada - Monitorar",
                ),
                # Elevators
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth1.id,
                    name="Elevador de Caçambas EL-4511",
                    code="EL4511",
                    equipment_type=EquipmentType.ELEVATOR,
                    manufacturer="Bruks Siwertell",
                    model="BE-3000",
                    serial_number="BE3000-2021-028",
                    year_manufactured=2021,
                    year_installed=2022,
                    rated_capacity=3000.0,
                    max_capacity=3200.0,
                    power_rating=520.0,
                    status=EquipmentStatus.OPERATING,
                    health_score=88.5,
                    failure_probability=11.5,
                    total_operating_hours=8920.0,
                    total_downtime_hours=68.0,
                    total_throughput=1850000.0,
                    current_throughput=1920.0,
                    last_maintenance_date=datetime.utcnow() - timedelta(days=30),
                    next_maintenance_date=datetime.utcnow() + timedelta(days=150),
                    maintenance_interval_hours=720.0,
                    criticality="high",
                ),
                # Shiploaders
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth1.id,
                    name="Shiploader SL-01",
                    code="SL01",
                    equipment_type=EquipmentType.SHIPLOADER,
                    manufacturer="Bedeschi",
                    model="BSL-2500",
                    serial_number="BSL2500-2018-005",
                    year_manufactured=2018,
                    year_installed=2019,
                    rated_capacity=2500.0,
                    max_capacity=2800.0,
                    power_rating=850.0,
                    status=EquipmentStatus.OPERATING,
                    health_score=95.0,
                    failure_probability=5.0,
                    total_operating_hours=22100.0,
                    total_downtime_hours=180.0,
                    total_throughput=4250000.0,
                    current_throughput=1820.0,
                    last_maintenance_date=datetime.utcnow() - timedelta(days=60),
                    next_maintenance_date=datetime.utcnow() + timedelta(days=120),
                    maintenance_interval_hours=720.0,
                    criticality="critical",
                ),
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth2.id,
                    name="Shiploader SL-02",
                    code="SL02",
                    equipment_type=EquipmentType.SHIPLOADER,
                    manufacturer="Bedeschi",
                    model="BSL-2000",
                    serial_number="BSL2000-2019-012",
                    year_manufactured=2019,
                    year_installed=2020,
                    rated_capacity=2000.0,
                    max_capacity=2300.0,
                    power_rating=720.0,
                    status=EquipmentStatus.IDLE,
                    health_score=91.0,
                    failure_probability=9.0,
                    total_operating_hours=15800.0,
                    total_downtime_hours=145.0,
                    total_throughput=2980000.0,
                    last_maintenance_date=datetime.utcnow() - timedelta(days=20),
                    next_maintenance_date=datetime.utcnow() + timedelta(days=160),
                    maintenance_interval_hours=720.0,
                    criticality="high",
                ),
                # Weighing scales
                PortEquipment(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    berth_id=berth1.id,
                    name="Balança Dinâmica WS-101",
                    code="WS101",
                    equipment_type=EquipmentType.WEIGHING_SCALE,
                    manufacturer="Schenck Process",
                    model="MULTICOR-C350",
                    serial_number="MC350-2020-087",
                    year_manufactured=2020,
                    year_installed=2021,
                    rated_capacity=5000.0,
                    power_rating=15.0,
                    status=EquipmentStatus.OPERATING,
                    health_score=96.5,
                    failure_probability=3.5,
                    total_operating_hours=10200.0,
                    total_downtime_hours=25.0,
                    criticality="high",
                ),
            ]

            for eq in equipment_list:
                session.add(eq)

            await session.flush()
            print(f"✅ Created {len(equipment_list)} equipment items")

            # ===== 5. CREATE LOADING OPERATIONS =====
            print("\n📦 Creating loading operations...")

            # Operation 1: Currently in progress
            op1_start = datetime.utcnow() - timedelta(hours=14, minutes=32)
            op1 = LoadingOperation(
                id=uuid.uuid4(),
                site_id=site.id,
                vessel_id=vessel1.id,
                berth_id=berth1.id,
                operation_type=OperationType.LOADING,
                operation_number="OP-2025-001-SANTOS",
                status=OperationStatus.IN_PROGRESS,
                planned_start=op1_start,
                planned_end=op1_start + timedelta(hours=42),
                actual_start=op1_start,
                planned_rate=1950.0,
                actual_rate=1785.0,
                current_rate=1850.0,
                total_planned_quantity=75000.0,
                total_actual_quantity=48750.0,  # 65% complete
                efficiency=91.5,
                downtime_hours=1.8,
                working_hours=14.5,
                is_delayed=False,
                equipment_used=["TC4515", "TC2521", "EL4511", "SL01", "WS101"],
                weather_conditions="Céu parcialmente nublado, 24°C, vento SE 12 km/h",
                shift_supervisor="João Almeida",
            )
            session.add(op1)
            await session.flush()

            # Cargos for operation 1
            cargo1_1 = Cargo(
                id=uuid.uuid4(),
                loading_operation_id=op1.id,
                commodity=CommodityType.SOYBEAN,
                commodity_grade="Grade A",
                description="Soja em grãos para exportação - Safra 2024/2025",
                planned_quantity=75000.0,
                actual_quantity=48750.0,
                unit="tons",
                origin="Mato Grosso, Brasil",
                destination="Rotterdam, Holanda",
                shipper="ADM do Brasil Ltda",
                consignee="European Grain Imports BV",
                specifications={
                    "moisture": 14.2,
                    "protein": 35.8,
                    "damaged_grains": 1.1,
                    "impurities": 0.8,
                    "germination": 85
                },
                bl_number="SANTOS2025001234",
                customs_reference="BR-EXP-2025-445521",
            )
            session.add(cargo1_1)

            # Events for operation 1
            events_op1 = [
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="created",
                    event_time=op1_start - timedelta(hours=24),
                    description="Operação criada e programada",
                    event_data={"created_by": "Sistema", "scheduled": True},
                    user_name="Sistema Automático",
                ),
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="vessel_berthed",
                    event_time=op1_start - timedelta(minutes=18),
                    description="Navio atracado no Berço 1",
                    event_data={"berth": "B1", "pilot": "Cmdt. Paulo Santos"},
                    user_name="Paulo Santos",
                ),
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="start",
                    event_time=op1_start,
                    description="Início do carregamento - Shiploader SL-01 conectado",
                    event_data={"equipment": ["SL01", "TC4515", "EL4511"]},
                    user_name="João Almeida",
                ),
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="pause",
                    event_time=op1_start + timedelta(hours=6, minutes=15),
                    description="Pausa para troca de silo - Manutenção preventiva",
                    event_data={"reason": "Silo change", "duration_minutes": 45},
                    user_name="João Almeida",
                ),
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="resume",
                    event_time=op1_start + timedelta(hours=7),
                    description="Carregamento retomado",
                    event_data={"new_silo": "A2"},
                    user_name="João Almeida",
                ),
                OperationEvent(
                    id=uuid.uuid4(),
                    loading_operation_id=op1.id,
                    event_type="equipment_alarm",
                    event_time=op1_start + timedelta(hours=10, minutes=22),
                    description="Alerta de temperatura - TC2521",
                    event_data={"equipment": "TC2521", "temperature": 68, "threshold": 65},
                    user_name="Sistema Automático",
                ),
            ]

            for event in events_op1:
                session.add(event)

            print(f"✅ Operation {op1.operation_number}: {op1.status.value} - {op1.total_actual_quantity}/{op1.total_planned_quantity} tons (65%)")

            # Operation 2: Completed yesterday
            op2_start = datetime.utcnow() - timedelta(days=4, hours=16)
            op2_end = datetime.utcnow() - timedelta(days=2, hours=8)
            op2 = LoadingOperation(
                id=uuid.uuid4(),
                site_id=site.id,
                vessel_id=vessel3.id,
                berth_id=berth1.id,
                operation_type=OperationType.LOADING,
                operation_number="OP-2025-002-SANTOS",
                status=OperationStatus.COMPLETED,
                planned_start=op2_start,
                planned_end=op2_start + timedelta(hours=48),
                actual_start=op2_start,
                actual_end=op2_end,
                planned_rate=2000.0,
                actual_rate=1965.0,
                total_planned_quantity=95000.0,
                total_actual_quantity=94850.0,
                efficiency=98.2,
                downtime_hours=2.5,
                working_hours=48.2,
                is_delayed=False,
                equipment_used=["TC4515", "EL4511", "SL01", "WS101"],
                weather_conditions="Tempo bom durante toda operação",
                shift_supervisor="Maria Santos / João Almeida",
            )
            session.add(op2)
            await session.flush()

            cargo2_1 = Cargo(
                id=uuid.uuid4(),
                loading_operation_id=op2.id,
                commodity=CommodityType.SOYBEAN,
                planned_quantity=95000.0,
                actual_quantity=94850.0,
                specifications={"moisture": 13.8, "protein": 36.2, "impurities": 0.7},
            )
            session.add(cargo2_1)

            print(f"✅ Operation {op2.operation_number}: {op2.status.value} - {op2.total_actual_quantity} tons")

            # Operation 3: Completed last week
            op3_start = datetime.utcnow() - timedelta(days=10, hours=8)
            op3_end = datetime.utcnow() - timedelta(days=8, hours=14)
            op3 = LoadingOperation(
                id=uuid.uuid4(),
                site_id=site.id,
                vessel_id=vessel3.id,  # Reuse vessel for history
                berth_id=berth2.id,
                operation_type=OperationType.LOADING,
                operation_number="OP-2025-003-SANTOS",
                status=OperationStatus.COMPLETED,
                planned_start=op3_start,
                planned_end=op3_start + timedelta(hours=36),
                actual_start=op3_start,
                actual_end=op3_end,
                planned_rate=1800.0,
                actual_rate=1725.0,
                total_planned_quantity=62000.0,
                total_actual_quantity=61890.0,
                efficiency=95.8,
                downtime_hours=1.2,
                working_hours=35.9,
                is_delayed=False,
                equipment_used=["SL02"],
                shift_supervisor="Carlos Mendes",
            )
            session.add(op3)
            await session.flush()

            cargo3_1 = Cargo(
                id=uuid.uuid4(),
                loading_operation_id=op3.id,
                commodity=CommodityType.CORN,
                planned_quantity=62000.0,
                actual_quantity=61890.0,
                specifications={"moisture": 14.5, "impurities": 1.2},
            )
            session.add(cargo3_1)

            print(f"✅ Operation {op3.operation_number}: {op3.status.value} - {op3.total_actual_quantity} tons")

            # ===== 6. CREATE MAINTENANCE RECORDS =====
            print("\n🔧 Creating maintenance records...")

            # Maintenance for TC2521 (the equipment with issues)
            maint1 = MaintenanceRecord(
                id=uuid.uuid4(),
                equipment_id=[eq for eq in equipment_list if eq.code == "TC2521"][0].id,
                maintenance_type=MaintenanceType.PREVENTIVE,
                scheduled_date=datetime.utcnow() - timedelta(days=92),
                actual_date=datetime.utcnow() - timedelta(days=90),
                duration_hours=6.5,
                work_description="Manutenção preventiva programada - Lubrificação geral, inspeção de rolamentos e correia",
                parts_replaced=[
                    {"part": "Rolamento SKF 6314", "quantity": 2, "cost": 1850.00},
                    {"part": "Óleo lubrificante", "quantity": 20, "unit": "L", "cost": 450.00}
                ],
                labor_cost=2400.00,
                parts_cost=2300.00,
                total_cost=4700.00,
                technician_name="Roberto Lima",
                supervisor_name="Eng. Fernando Costa",
                findings="Rolamento traseiro com temperatura 8°C acima do normal. Substituído preventivamente.",
                recommendations="Monitorar temperatura dos novos rolamentos. Próxima verificação em 30 dias.",
                next_maintenance_date=datetime.utcnow() + timedelta(days=30),
            )
            session.add(maint1)

            print("✅ Created maintenance records")

            # ===== COMMIT ALL DATA =====
            await session.commit()
            print("\n✅ All demo data committed successfully!")

            # ===== SUMMARY =====
            print("\n" + "="*60)
            print("📊 SMARTPORT DEMO DATA SUMMARY")
            print("="*60)
            print(f"Organization: {org.name}")
            print(f"Site: {site.name}")
            print(f"Berths: 2 ({berth1.code}, {berth2.code})")
            print(f"Vessels: 4 (1 loading, 1 waiting, 1 departed, 1 scheduled)")
            print(f"Operations: 3 (1 in progress, 2 completed)")
            print(f"Equipment: {len(equipment_list)} items")
            print(f"Maintenance Records: 1")
            print("="*60)
            print("\n🎉 Demo data ready for client presentations!")
            print("\n📝 Next steps:")
            print("   1. Run: alembic upgrade head")
            print("   2. Run: python scripts/seed_smartport_demo.py")
            print("   3. Access API docs: http://localhost:8000/docs")
            print("   4. Start frontend development!")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error seeding data: {e}")
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
