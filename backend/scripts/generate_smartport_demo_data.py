"""
Generate SmartPort Demo Data

Creates realistic demo data for SmartPort including:
- Berths (10-15 berths)
- Vessels (20-30 vessels in various states)
- Port Operations (current and historical)

Usage:
    python scripts/generate_smartport_demo_data.py
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.berth import Berth, BerthType, BerthStatus
from app.models.vessel import Vessel, VesselType, VesselStatus
from app.models.port_operation import PortOperation, OperationType, OperationStatus, CargoType


# ============================================================================
# Demo Data Configuration
# ============================================================================

# Port location: Santos, Brazil (largest port in South America)
PORT_LAT = -23.9618
PORT_LON = -46.3322

# Berth names and configurations
BERTH_CONFIGS = [
    # Container terminals
    {"name": "Terminal 1 - Berth A", "code": "T1-A", "type": BerthType.CONTAINER, "loa": 366, "beam": 60, "draft": 16, "cranes": 4},
    {"name": "Terminal 1 - Berth B", "code": "T1-B", "type": BerthType.CONTAINER, "loa": 366, "beam": 60, "draft": 16, "cranes": 4},
    {"name": "Terminal 2 - Berth A", "code": "T2-A", "type": BerthType.CONTAINER, "loa": 400, "beam": 62, "draft": 17, "cranes": 6},
    {"name": "Terminal 2 - Berth B", "code": "T2-B", "type": BerthType.CONTAINER, "loa": 400, "beam": 62, "draft": 17, "cranes": 6},

    # Bulk terminals
    {"name": "Bulk Terminal - North", "code": "BT-N", "type": BerthType.BULK, "loa": 300, "beam": 50, "draft": 15, "cranes": 2},
    {"name": "Bulk Terminal - South", "code": "BT-S", "type": BerthType.BULK, "loa": 300, "beam": 50, "draft": 15, "cranes": 2},

    # General cargo
    {"name": "General Cargo Terminal 1", "code": "GC-1", "type": BerthType.GENERAL_CARGO, "loa": 250, "beam": 40, "draft": 12, "cranes": 3},
    {"name": "General Cargo Terminal 2", "code": "GC-2", "type": BerthType.GENERAL_CARGO, "loa": 250, "beam": 40, "draft": 12, "cranes": 3},

    # RoRo terminal
    {"name": "RoRo Terminal", "code": "RR-1", "type": BerthType.RO_RO, "loa": 200, "beam": 35, "draft": 10, "cranes": 0},

    # Tanker terminal
    {"name": "Tanker Terminal - East", "code": "TK-E", "type": BerthType.TANKER, "loa": 350, "beam": 58, "draft": 18, "cranes": 0},
    {"name": "Tanker Terminal - West", "code": "TK-W", "type": BerthType.TANKER, "loa": 350, "beam": 58, "draft": 18, "cranes": 0},
]

# Vessel names and characteristics
VESSEL_NAMES = [
    # Container ships
    ("MSC Gülsün", "IMO9863639", VesselType.CONTAINER_SHIP, 400, 61.5, 16.5, 23756),
    ("EVER GIVEN", "IMO9811000", VesselType.CONTAINER_SHIP, 400, 59, 16, 20124),
    ("CMA CGM Antoine De Saint Exupery", "IMO9454436", VesselType.CONTAINER_SHIP, 365, 51, 16, 20600),
    ("COSCO Shipping Universe", "IMO9795940", VesselType.CONTAINER_SHIP, 400, 58.6, 16, 21237),
    ("ONE Innovation", "IMO9811073", VesselType.CONTAINER_SHIP, 400, 61, 16.5, 24136),
    ("Maersk Mc-Kinney Moller", "IMO9619907", VesselType.CONTAINER_SHIP, 399, 59, 16, 18270),

    # Bulk carriers
    ("Valemax Ore Brasil", "IMO9629309", VesselType.BULK_CARRIER, 362, 65, 23, 0),
    ("Berge Everest", "IMO9535162", VesselType.BULK_CARRIER, 362, 65, 23, 0),
    ("Big Hope", "IMO9443124", VesselType.BULK_CARRIER, 292, 45, 18, 0),

    # Tankers
    ("TI Europe", "IMO9246633", VesselType.TANKER, 380, 68, 24.5, 0),
    ("Costas", "IMO9314825", VesselType.TANKER, 333, 60, 22, 0),

    # General cargo
    ("BBC Emerald", "IMO9465891", VesselType.GENERAL_CARGO, 170, 26, 9.5, 0),
    ("SAL Heavy Lift", "IMO9448522", VesselType.GENERAL_CARGO, 156, 25, 8.8, 0),

    # RoRo
    ("Höegh Autoliners", "IMO9697600", VesselType.RO_RO, 200, 38, 10.7, 0),
]

# Additional smaller vessels
ADDITIONAL_VESSELS = [
    ("Container Feeder 1", "IMO8800001", VesselType.CONTAINER_SHIP, 200, 30, 10, 1800),
    ("Container Feeder 2", "IMO8800002", VesselType.CONTAINER_SHIP, 210, 32, 11, 2000),
    ("Container Feeder 3", "IMO8800003", VesselType.CONTAINER_SHIP, 195, 28, 9.5, 1600),
    ("Bulk Carrier 1", "IMO8800011", VesselType.BULK_CARRIER, 225, 32, 14, 0),
    ("Bulk Carrier 2", "IMO8800012", VesselType.BULK_CARRIER, 235, 35, 15, 0),
    ("General Cargo 1", "IMO8800021", VesselType.GENERAL_CARGO, 150, 23, 8, 0),
    ("General Cargo 2", "IMO8800022", VesselType.GENERAL_CARGO, 160, 24, 8.5, 0),
]

VESSEL_CONFIGS = VESSEL_NAMES + ADDITIONAL_VESSELS

# Shipping lines
OPERATORS = [
    "Maersk Line", "MSC", "CMA CGM", "COSCO", "Hapag-Lloyd",
    "ONE", "Evergreen", "Yang Ming", "Vale", "BHP"
]

# Ports
PORTS = [
    "Shanghai", "Singapore", "Ningbo-Zhoushan", "Shenzhen", "Guangzhou",
    "Busan", "Hong Kong", "Rotterdam", "Hamburg", "Antwerp",
    "Los Angeles", "Long Beach", "New York", "Durban", "Buenos Aires"
]


# ============================================================================
# Data Generation Functions
# ============================================================================

async def create_berths(db: AsyncSession) -> List[Berth]:
    """Create demo berths"""
    print("Creating berths...")
    berths = []

    for idx, config in enumerate(BERTH_CONFIGS):
        # Calculate position (spread around the port)
        lat_offset = random.uniform(-0.01, 0.01)
        lon_offset = random.uniform(-0.01, 0.01)

        # Determine initial status
        if idx < 6:  # First 6 berths are occupied
            status = BerthStatus.OCCUPIED
        elif idx < 8:  # Next 2 are reserved
            status = BerthStatus.RESERVED
        else:  # Rest are available
            status = BerthStatus.AVAILABLE

        berth = Berth(
            id=uuid4(),
            name=config["name"],
            code=config["code"],
            berth_type=config["type"],
            status=status,
            max_loa=config["loa"],
            max_beam=config["beam"],
            max_draft=config["draft"],
            max_displacement=config["loa"] * 1000,  # Rough estimate
            max_crane_capacity=70.0 if config["cranes"] > 0 else None,
            number_of_cranes=config["cranes"],
            has_shore_power=random.choice([True, False]),
            has_fresh_water=True,
            has_bunker_facility=config["type"] == BerthType.TANKER,
            latitude=PORT_LAT + lat_offset,
            longitude=PORT_LON + lon_offset,
            description=f"Modern {config['type'].value} berth with state-of-the-art equipment",
            created_at=datetime.utcnow() - timedelta(days=random.randint(365, 1825)),
        )

        db.add(berth)
        berths.append(berth)

    await db.flush()
    print(f"✓ Created {len(berths)} berths")
    return berths


async def create_vessels(db: AsyncSession, berths: List[Berth]) -> List[Vessel]:
    """Create demo vessels"""
    print("Creating vessels...")
    vessels = []

    for idx, (name, imo, vtype, loa, beam, draft, teu) in enumerate(VESSEL_CONFIGS):
        # Determine vessel status
        if idx < 6:  # First 6 are berthed/loading/unloading
            status = random.choice([VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING])
        elif idx < 10:  # Next 4 are approaching/anchored
            status = random.choice([VesselStatus.APPROACHING, VesselStatus.ANCHORED])
        else:  # Rest are in various states
            status = random.choice(list(VesselStatus))

        # Calculate arrival/departure times
        now = datetime.utcnow()
        if status in [VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING]:
            eta = now - timedelta(hours=random.randint(2, 48))
            ata = eta + timedelta(hours=random.uniform(0.5, 2))
            etd = now + timedelta(hours=random.randint(4, 24))
            atd = None
        elif status in [VesselStatus.APPROACHING, VesselStatus.ANCHORED]:
            eta = now + timedelta(hours=random.randint(1, 12))
            ata = None
            etd = eta + timedelta(hours=random.randint(12, 48))
            atd = None
        elif status == VesselStatus.DEPARTED:
            eta = now - timedelta(days=random.randint(1, 7))
            ata = eta + timedelta(hours=random.uniform(0.5, 2))
            etd = ata + timedelta(hours=random.randint(12, 48))
            atd = etd + timedelta(hours=random.uniform(-1, 1))
        else:
            eta = now + timedelta(hours=random.randint(24, 168))
            ata = None
            etd = eta + timedelta(hours=random.randint(12, 48))
            atd = None

        # Position
        if status == VesselStatus.APPROACHING:
            lat = PORT_LAT + random.uniform(-0.5, -0.1)
            lon = PORT_LON + random.uniform(-0.5, -0.1)
        elif status == VesselStatus.ANCHORED:
            lat = PORT_LAT + random.uniform(-0.1, 0.1)
            lon = PORT_LON + random.uniform(-0.1, 0.1)
        else:
            lat = None
            lon = None

        vessel = Vessel(
            id=uuid4(),
            name=name,
            imo=imo,
            mmsi=f"{random.randint(200000000, 799999999)}",
            call_sign=f"{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{random.randint(1000, 9999)}",
            flag=random.choice(["Panama", "Liberia", "Marshall Islands", "Hong Kong", "Singapore"]),
            vessel_type=vtype,
            status=status,
            loa=loa,
            beam=beam,
            draft=draft,
            max_draft=draft + 1,
            gross_tonnage=loa * beam * draft * 0.5,
            deadweight_tonnage=loa * beam * draft * 0.7,
            capacity_teu=teu if teu > 0 else None,
            capacity_cubic_meters=loa * beam * draft * 10 if vtype == VesselType.BULK_CARRIER else None,
            eta=eta,
            ata=ata,
            etd=etd,
            atd=atd,
            last_latitude=lat,
            last_longitude=lon,
            last_position_update=now if lat else None,
            heading=random.uniform(0, 360) if lat else None,
            speed_knots=random.uniform(8, 15) if status == VesselStatus.APPROACHING else 0,
            origin_port=random.choice(PORTS),
            destination_port=random.choice(PORTS),
            voyage_number=f"{random.randint(100, 999)}{chr(random.randint(65, 90))}",
            owner=random.choice(OPERATORS),
            operator=random.choice(OPERATORS),
            agent=random.choice(OPERATORS),
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        )

        db.add(vessel)
        vessels.append(vessel)

    await db.flush()
    print(f"✓ Created {len(vessels)} vessels")
    return vessels


async def create_operations(db: AsyncSession, berths: List[Berth], vessels: List[Vessel]) -> List[PortOperation]:
    """Create demo port operations"""
    print("Creating port operations...")
    operations = []

    # Assign berthed vessels to berths and create operations
    berthed_vessels = [v for v in vessels if v.status in [VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING]]
    occupied_berths = [b for b in berths if b.status == BerthStatus.OCCUPIED]

    # Link vessels to berths
    for vessel, berth in zip(berthed_vessels[:len(occupied_berths)], occupied_berths):
        berth.current_vessel_id = vessel.id
        berth.occupation_start = vessel.ata
        berth.estimated_departure = vessel.etd

    # Create operations for berthed vessels
    for vessel in berthed_vessels[:6]:
        # Find appropriate berth
        suitable_berths = [b for b in berths if b.berth_type.value in vessel.vessel_type.value]
        if not suitable_berths:
            suitable_berths = berths

        berth = random.choice(suitable_berths)

        # Operation type based on vessel type
        if vessel.vessel_type == VesselType.CONTAINER_SHIP:
            op_type = random.choice([OperationType.LOADING, OperationType.UNLOADING])
            cargo_type = CargoType.CONTAINERS
            containers_planned = random.randint(500, 2000)
            containers_completed = random.randint(int(containers_planned * 0.3), int(containers_planned * 0.9))
            tonnage_planned = containers_planned * 15  # Average 15 tonnes per container
            tonnage_completed = containers_completed * 15
        elif vessel.vessel_type == VesselType.BULK_CARRIER:
            op_type = OperationType.UNLOADING
            cargo_type = CargoType.BULK_SOLID
            containers_planned = None
            containers_completed = 0
            tonnage_planned = random.randint(50000, 150000)
            tonnage_completed = random.randint(int(tonnage_planned * 0.3), int(tonnage_planned * 0.9))
        elif vessel.vessel_type == VesselType.TANKER:
            op_type = random.choice([OperationType.LOADING, OperationType.BUNKERING])
            cargo_type = CargoType.BULK_LIQUID
            containers_planned = None
            containers_completed = 0
            tonnage_planned = random.randint(80000, 200000)
            tonnage_completed = random.randint(int(tonnage_planned * 0.4), int(tonnage_planned * 0.8))
        else:
            op_type = OperationType.UNLOADING
            cargo_type = CargoType.GENERAL_CARGO
            containers_planned = None
            containers_completed = 0
            tonnage_planned = random.randint(5000, 20000)
            tonnage_completed = random.randint(int(tonnage_planned * 0.3), int(tonnage_planned * 0.9))

        # Status
        if vessel.status == VesselStatus.BERTHED:
            status = OperationStatus.SCHEDULED
            actual_start = None
        else:
            status = OperationStatus.IN_PROGRESS
            actual_start = vessel.ata or datetime.utcnow()

        operation = PortOperation(
            id=uuid4(),
            vessel_id=vessel.id,
            berth_id=berth.id,
            operation_type=op_type,
            status=status,
            cargo_type=cargo_type,
            containers_planned=containers_planned,
            containers_completed=containers_completed,
            tonnage_planned=tonnage_planned,
            tonnage_completed=tonnage_completed,
            scheduled_start=vessel.ata or datetime.utcnow(),
            actual_start=actual_start,
            estimated_end=vessel.etd or datetime.utcnow() + timedelta(hours=24),
            cranes_assigned=berth.number_of_cranes if cargo_type == CargoType.CONTAINERS else 0,
            workforce_assigned=random.randint(10, 50),
            estimated_cost=random.uniform(50000, 200000),
            currency="USD",
            priority=random.randint(1, 5),
            cargo_description=f"{cargo_type.value} from {vessel.origin_port}",
            weather_delay=random.choice([True, False]) if random.random() < 0.2 else False,
            created_at=vessel.ata or datetime.utcnow() - timedelta(hours=48),
        )

        # Calculate metrics
        operation.calculate_productivity()
        operation.calculate_efficiency()

        db.add(operation)
        operations.append(operation)

    # Create some completed operations (last 7 days)
    for _ in range(15):
        vessel = random.choice(vessels)
        berth = random.choice([b for b in berths if b.berth_type.value in vessel.vessel_type.value] or berths)

        days_ago = random.randint(1, 7)
        scheduled_start = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
        actual_start = scheduled_start + timedelta(hours=random.uniform(-1, 2))
        estimated_end = scheduled_start + timedelta(hours=random.randint(12, 48))
        actual_end = actual_start + timedelta(hours=random.randint(10, 50))

        if vessel.vessel_type == VesselType.CONTAINER_SHIP:
            containers_planned = random.randint(500, 2000)
            containers_completed = containers_planned
            tonnage_planned = containers_planned * 15
            tonnage_completed = tonnage_planned
        else:
            containers_planned = None
            containers_completed = 0
            tonnage_planned = random.randint(50000, 150000)
            tonnage_completed = tonnage_planned

        operation = PortOperation(
            id=uuid4(),
            vessel_id=vessel.id,
            berth_id=berth.id,
            operation_type=random.choice([OperationType.LOADING, OperationType.UNLOADING]),
            status=OperationStatus.COMPLETED,
            cargo_type=CargoType.CONTAINERS if vessel.vessel_type == VesselType.CONTAINER_SHIP else CargoType.BULK_SOLID,
            containers_planned=containers_planned,
            containers_completed=containers_completed,
            tonnage_planned=tonnage_planned,
            tonnage_completed=tonnage_completed,
            scheduled_start=scheduled_start,
            actual_start=actual_start,
            estimated_end=estimated_end,
            actual_end=actual_end,
            cranes_assigned=random.randint(2, 6),
            workforce_assigned=random.randint(10, 50),
            estimated_cost=random.uniform(50000, 200000),
            actual_cost=random.uniform(45000, 210000),
            currency="USD",
            priority=random.randint(1, 5),
            created_at=scheduled_start - timedelta(hours=48),
        )

        operation.calculate_productivity()
        operation.calculate_efficiency()

        db.add(operation)
        operations.append(operation)

    await db.flush()
    print(f"✓ Created {len(operations)} port operations")
    return operations


async def main():
    """Main function to generate all demo data"""
    print("\n" + "="*60)
    print("SmartPort Demo Data Generation")
    print("="*60 + "\n")

    async with SessionLocal() as db:
        try:
            # Create all demo data
            berths = await create_berths(db)
            vessels = await create_vessels(db, berths)
            operations = await create_operations(db, berths, vessels)

            # Commit all changes
            await db.commit()

            print("\n" + "="*60)
            print("✓ Demo data generation completed successfully!")
            print("="*60)
            print(f"\nSummary:")
            print(f"  - Berths: {len(berths)}")
            print(f"  - Vessels: {len(vessels)}")
            print(f"  - Operations: {len(operations)}")
            print(f"\nBerth Status:")
            print(f"  - Available: {len([b for b in berths if b.status == BerthStatus.AVAILABLE])}")
            print(f"  - Occupied: {len([b for b in berths if b.status == BerthStatus.OCCUPIED])}")
            print(f"  - Reserved: {len([b for b in berths if b.status == BerthStatus.RESERVED])}")
            print(f"\nVessel Status:")
            for status in VesselStatus:
                count = len([v for v in vessels if v.status == status])
                print(f"  - {status.value}: {count}")
            print(f"\nOperation Status:")
            for status in OperationStatus:
                count = len([o for o in operations if o.status == status])
                if count > 0:
                    print(f"  - {status.value}: {count}")

        except Exception as e:
            print(f"\n✗ Error generating demo data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
