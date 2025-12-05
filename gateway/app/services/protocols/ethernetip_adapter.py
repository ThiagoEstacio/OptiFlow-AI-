"""
EtherNet/IP CIP Protocol Adapter
=================================

Connects to Rockwell/Allen-Bradley PLCs using EtherNet/IP CIP protocol
and publishes tag data to Kafka.

Features:
- Supports ControlLogix, CompactLogix, Micro800 series PLCs
- Read/Write of atomic tags (BOOL, SINT, INT, DINT, REAL, etc.)
- Read/Write of arrays and UDT structures
- Program-scoped and Controller-scoped tags
- Automatic reconnection on connection loss
- Optimized batch reading for multiple tags

Based on pycomm3 library (EtherNet/IP CIP implementation).

Reference PLCs:
- ControlLogix 5580 (Shiploaders, Trippers)
- CompactLogix 5380 (Stacker Reclaimers)
- Micro850 (Small conveyor stations)

SIMULATION MODE:
When connecting to 'nodered' host, uses HTTP fallback to read simulated
data from Node-RED grain terminal simulator (TRP01, SLD01 tags).
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
import aiohttp
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

try:
    from pycomm3 import LogixDriver
    from pycomm3.exceptions import CommError
    ETHERNETIP_AVAILABLE = True
except ImportError:
    ETHERNETIP_AVAILABLE = False
    logging.warning("pycomm3 not installed - EtherNet/IP adapter will use simulation mode only")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

# Import metrics
try:
    from app.services.gateway_metrics import get_gateway_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EIPTagSpec:
    """Specification for an EtherNet/IP tag"""
    name: str
    address: str  # Logix tag name (e.g., "Program:MainProgram.Temperature")
    data_type: str  # bool, sint, int, dint, real, string
    tag_id: Optional[str] = None
    program: Optional[str] = None  # Program scope (None = controller scope)
    array_index: Optional[int] = None  # For array access
    config: Dict[str, Any] = field(default_factory=dict)


class EtherNetIPAdapter(BaseProtocolAdapter):
    """
    EtherNet/IP CIP protocol adapter for Rockwell PLCs

    Reads tags from ControlLogix/CompactLogix PLCs using CIP protocol
    and publishes to Kafka.

    Configuration (extra_config):
    - slot: CPU slot number (default: 0)
    - connection_path: Optional CIP routing path
    - init_tags: Initialize tag list on connect (default: True)
    - init_program_tags: Initialize program-scoped tags (default: False)

    Tag configuration format:
    {
        'name': 'Temperature',          # Friendly name
        'address': 'Silo1_Temperature', # Logix tag name
        'type': 'real',                 # Data type: bool, sint, int, dint, real, string
        'program': 'MainProgram'        # Optional: program scope
    }

    Address formats supported:
    - Controller-scoped: 'TagName'
    - Program-scoped: 'Program:MainProgram.TagName'
    - Array element: 'ArrayTag[0]'
    - UDT member: 'UDT_Instance.Member'
    """

    # Data type mapping from config to pycomm3
    TYPE_MAP = {
        'bool': 'BOOL',
        'boolean': 'BOOL',
        'sint': 'SINT',
        'int': 'INT',
        'int16': 'INT',
        'dint': 'DINT',
        'int32': 'DINT',
        'lint': 'LINT',
        'int64': 'LINT',
        'real': 'REAL',
        'float': 'REAL',
        'float32': 'REAL',
        'lreal': 'LREAL',
        'double': 'LREAL',
        'float64': 'LREAL',
        'string': 'STRING',
    }

    def __init__(self, config: ProtocolConfig):
        super().__init__(config)

        # EtherNet/IP specific state
        self.plc: Optional[LogixDriver] = None
        self.slot = config.extra_config.get('slot', 0)
        self.connection_path = config.extra_config.get('connection_path')
        self.init_tags = config.extra_config.get('init_tags', True)
        self.init_program_tags = config.extra_config.get('init_program_tags', False)

        # Simulation mode - when connecting to nodered, use HTTP fallback
        self.simulation_mode = config.host.lower() in ['nodered', 'localhost', '127.0.0.1']
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._nodered_url = f"http://{config.host}:1880"  # Node-RED HTTP endpoint

        # Build tag specifications from config
        self._tag_specs: List[EIPTagSpec] = self._build_tag_specs()

        # Thread pool for blocking pycomm3 operations
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="eip-")

        # Cache for realtime API access
        self.last_values: Dict[str, Dict[str, Any]] = {}

        # Simulated data cache (for Node-RED simulation mode)
        self._simulated_data: Dict[str, Any] = {}

        mode = "SIMULATION (Node-RED)" if self.simulation_mode else "PRODUCTION (CIP)"
        logger.info(
            f"🔧 EtherNet/IP adapter initialized - "
            f"Host: {config.host}:{config.port}, Slot: {self.slot}, "
            f"Tags: {len(self._tag_specs)}, Mode: {mode}"
        )

    def _build_tag_specs(self) -> List[EIPTagSpec]:
        """Build tag specifications from configuration"""
        specs = []

        for tag_config in self.config.tags:
            name = tag_config.get('name')
            address = tag_config.get('address')

            if not name or not address:
                logger.warning(f"⚠️  Skipping tag with missing name or address: {tag_config}")
                continue

            # Parse program scope from address if present
            program = tag_config.get('program')
            if not program and address.startswith('Program:'):
                # Extract program name from address like "Program:MainProgram.TagName"
                parts = address.split('.')
                if len(parts) >= 2:
                    program = parts[0].replace('Program:', '')

            specs.append(EIPTagSpec(
                name=name,
                address=address,
                data_type=tag_config.get('type', 'real').lower(),
                tag_id=tag_config.get('tag_id'),
                program=program,
                config=tag_config
            ))

        return specs

    async def connect(self) -> bool:
        """Connect to Rockwell PLC via EtherNet/IP or simulation mode"""
        if self.connected:
            logger.warning(f"⚠️  {self.adapter_id} already connected")
            return True

        # SIMULATION MODE - Connect via HTTP to Node-RED
        if self.simulation_mode:
            return await self._connect_simulation()

        # PRODUCTION MODE - Connect via EtherNet/IP CIP
        return await self._connect_production()

    async def _connect_simulation(self) -> bool:
        """Connect in simulation mode (direct data generation)"""
        try:
            logger.info(f"🔌 Connecting to EtherNet/IP SIMULATION: {self.config.host}")

            # In simulation mode, we generate data directly - no external connection needed
            # This simulates a ControlLogix PLC with Tripper and Shiploader tags
            self.connected = True

            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected("ethernetip", 1)
                metrics.set_device_status(self.adapter_id, "ethernetip", True)
                metrics.track_connection_attempt(self.adapter_id, "ethernetip", True)
                metrics.set_tags_total(self.adapter_id, len(self._tag_specs))

            logger.info(
                f"✅ Connected to EtherNet/IP SIMULATION - "
                f"Simulating ControlLogix with {len(self._tag_specs)} tags (TRP01, SLD01)"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to simulation: {e}")
            self.connected = False
            return False

    async def _connect_production(self) -> bool:
        """Connect to real PLC via EtherNet/IP CIP"""
        if not ETHERNETIP_AVAILABLE:
            logger.error("❌ pycomm3 not available - cannot connect to real PLC")
            return False

        try:
            logger.info(f"🔌 Connecting to EtherNet/IP PLC: {self.config.host}:{self.config.port}")

            # Build connection path
            if self.connection_path:
                path = self.connection_path
            else:
                path = f"{self.config.host}/{self.slot}"

            # pycomm3 is synchronous, run in executor
            def _connect():
                plc = LogixDriver(
                    path,
                    init_tags=self.init_tags,
                    init_program_tags=self.init_program_tags
                )
                plc.open()
                return plc

            self.plc = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _connect
            )

            if self.plc and self.plc.connected:
                logger.info(f"✅ Connected to EtherNet/IP PLC - {self.plc.info}")
                self.connected = True

                # Update metrics
                if METRICS_AVAILABLE:
                    metrics = get_gateway_metrics()
                    metrics.set_devices_connected("ethernetip", 1)
                    metrics.set_device_status(self.adapter_id, "ethernetip", True)
                    metrics.track_connection_attempt(self.adapter_id, "ethernetip", True)
                    metrics.set_tags_total(self.adapter_id, len(self._tag_specs))

                return True
            else:
                logger.error(f"❌ Failed to connect to EtherNet/IP PLC")
                self.connected = False

                if METRICS_AVAILABLE:
                    metrics = get_gateway_metrics()
                    metrics.track_connection_attempt(self.adapter_id, "ethernetip", False)

                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to EtherNet/IP PLC: {e}", exc_info=True)
            self.connected = False

            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.track_connection_attempt(self.adapter_id, "ethernetip", False)
                metrics.set_device_status(self.adapter_id, "ethernetip", False)

            return False

    async def disconnect(self):
        """Disconnect from PLC or simulation"""
        if not self.connected:
            return

        try:
            logger.info(f"🔌 Disconnecting from {self.config.host}...")

            # Close HTTP session if in simulation mode
            if self._http_session:
                await self._http_session.close()
                self._http_session = None

            # Close PLC connection if in production mode
            if self.plc:
                def _close():
                    self.plc.close()

                await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    _close
                )
                logger.info("✅ PLC disconnected")

            self.plc = None
            self.connected = False

            # Update metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected("ethernetip", 0)
                metrics.set_device_status(self.adapter_id, "ethernetip", False)

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def read_tags(self) -> List[TagData]:
        """Read all configured tags from PLC or simulation"""
        if not self.connected:
            return []

        if not self._tag_specs:
            return []

        # SIMULATION MODE
        if self.simulation_mode:
            return await self._read_tags_simulation()

        # PRODUCTION MODE
        return await self._read_tags_production()

    async def _read_tags_simulation(self) -> List[TagData]:
        """Read tags from simulation (Node-RED or generated data)"""
        import random
        import math

        now = datetime.now()
        tags: List[TagData] = []

        # Generate realistic Rockwell PLC data for Tripper and Shiploader
        # This simulates what you would read from a real ControlLogix
        time_s = now.timestamp() % 3600  # Cycle every hour

        for spec in self._tag_specs:
            name = spec.name
            address = spec.address.upper()
            value = None
            quality = 'good'

            # TRIPPER CAR (TRP01) simulation
            if 'TRP01' in address or 'TRIPPER' in address:
                if 'POSITION' in address:
                    # Position oscillates 0-200m
                    value = 100 + 80 * math.sin(time_s / 60)
                elif 'SPEED' in address:
                    value = 15.0 + random.uniform(-2, 2)  # m/min
                elif 'TARGET' in address:
                    value = 100.0
                elif 'BAY' in address:
                    value = 3  # Selected bay
                elif 'LIMIT' in address:
                    value = 0  # No limit
                elif 'FAULT' in address or 'ALARM' in address:
                    value = 0
                else:
                    value = random.uniform(0, 100)

            # SHIPLOADER (SLD01) simulation
            elif 'SLD01' in address or 'SHIPLOADER' in address:
                if 'FLOW' in address and 'SP' not in address:
                    value = 1750 + random.uniform(-50, 50)  # t/h
                elif 'FLOW_SP' in address:
                    value = 1800.0
                elif 'POWER' in address:
                    value = 85 + random.uniform(-5, 5)  # kW
                elif 'CURRENT' in address:
                    value = 120 + random.uniform(-10, 10)  # A
                elif 'BOOM' in address and 'ANGLE' in address:
                    value = 12 + random.uniform(-1, 1)  # degrees
                elif 'SLEWING' in address:
                    value = 5 * math.sin(time_s / 30)  # degrees
                elif 'SHUTTLE' in address:
                    value = 15 + 5 * math.sin(time_s / 20)  # m
                elif 'LOADED' in address:
                    value = (time_s / 3600) * 1800  # Progressive loading
                elif 'TARGET' in address:
                    value = 55000.0  # t
                elif 'PROGRESS' in address:
                    value = ((time_s / 3600) * 1800 / 55000) * 100  # %
                elif 'TRIMMING' in address:
                    value = 0
                elif 'DUST' in address:
                    value = 1  # Dust suppression ON
                else:
                    value = random.uniform(0, 100)

            # Generic tag simulation
            else:
                if spec.data_type in ['bool', 'boolean']:
                    value = random.choice([0, 1])
                elif spec.data_type in ['int', 'int16', 'int32', 'dint']:
                    value = random.randint(0, 1000)
                else:
                    value = random.uniform(0, 100)

            # Update cache
            self.last_values[spec.address] = {
                'value': value,
                'quality': quality.capitalize(),
                'timestamp': now.isoformat()
            }

            tags.append(TagData(
                tag_name=spec.name,
                value=round(value, 2) if isinstance(value, float) else value,
                quality=quality,
                source=self.adapter_id,
                address=spec.address,
                tag_id=spec.tag_id
            ))

        return tags

    async def _read_tags_production(self) -> List[TagData]:
        """Read tags from real PLC via EtherNet/IP CIP"""
        if not self.plc:
            return []

        try:
            # Get list of tag addresses to read
            tag_addresses = [spec.address for spec in self._tag_specs]

            # Read all tags in one batch request (pycomm3 is synchronous)
            def _read_batch():
                return self.plc.read(*tag_addresses)

            results = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _read_batch
            )

            # Process results
            return self._process_read_results(results)

        except Exception as e:
            logger.error(f"❌ Error reading tags from EtherNet/IP PLC: {e}", exc_info=True)
            return []

    def _process_read_results(self, results) -> List[TagData]:
        """Process pycomm3 read results into TagData objects"""
        from datetime import datetime

        tags: List[TagData] = []
        now = datetime.now().isoformat()

        # Handle single tag result (not a list)
        if not isinstance(results, (list, tuple)):
            results = [results]

        for i, result in enumerate(results):
            spec = self._tag_specs[i] if i < len(self._tag_specs) else None

            if spec is None:
                continue

            # Check result status
            if result is None:
                quality = 'bad'
                value = None
            elif hasattr(result, 'error'):
                # pycomm3 Tag object with error
                quality = 'bad' if result.error else 'good'
                value = result.value if not result.error else None
            else:
                # Direct value
                quality = 'good'
                value = result.value if hasattr(result, 'value') else result

            # Update cache
            self.last_values[spec.address] = {
                'value': value,
                'quality': quality.capitalize(),
                'timestamp': now
            }

            tags.append(TagData(
                tag_name=spec.name,
                value=value,
                quality=quality,
                source=self.adapter_id,
                address=spec.address,
                tag_id=spec.tag_id
            ))

            # Update metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_read(self.adapter_id, "ethernetip", quality, 0.001)
                    metrics.track_data_collected(self.adapter_id, 1)
                except Exception:
                    pass

        return tags

    async def write_tag(self, address: str, value: Any) -> bool:
        """
        Write value to a PLC tag

        Args:
            address: Logix tag name
            value: Value to write

        Returns:
            True if write successful, False otherwise
        """
        if not self.connected or not self.plc:
            logger.error("Cannot write - not connected to PLC")
            return False

        try:
            def _write():
                return self.plc.write((address, value))

            result = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _write
            )

            if result and not result.error:
                logger.info(f"✅ Written {value} to {address}")
                return True
            else:
                logger.error(f"❌ Failed to write to {address}: {result.error if result else 'unknown'}")
                return False

        except Exception as e:
            logger.error(f"❌ Error writing to {address}: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if connection is still alive"""
        if not self.connected:
            return False

        # SIMULATION MODE - always healthy
        if self.simulation_mode:
            return True

        # PRODUCTION MODE - check PLC connection
        if not self.plc:
            return False

        try:
            # Try to read PLC info as health check
            def _check():
                return self.plc.get_plc_info()

            info = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _check
            )
            return info is not None

        except Exception as e:
            logger.warning(f"⚠️  Health check failed: {e}")
            return False

    async def read_all_discovered_tags(self) -> List[Dict[str, Any]]:
        """
        Read current values for ALL configured tags directly from PLC

        Used by the Gateway UI to show real-time values for all tags.

        Returns:
            List of dicts with tag info and current values
        """
        if not self.connected or not self.plc:
            logger.warning("Cannot read tags - not connected to PLC")
            return []

        results = []

        # Read all tags
        tag_data_list = await self.read_tags()

        for tag_data in tag_data_list:
            # Find original spec
            spec = next(
                (s for s in self._tag_specs if s.name == tag_data.tag_name),
                None
            )

            results.append({
                "name": tag_data.tag_name,
                "address": tag_data.address,
                "current_value": tag_data.value,
                "quality": tag_data.quality.capitalize(),
                "data_type": spec.data_type if spec else 'unknown',
                "unit": spec.config.get('unit') if spec else None,
                "last_update": tag_data.timestamp,
                "connected": tag_data.value is not None
            })

        good_count = len([r for r in results if r['connected']])
        logger.info(f"✅ Read {good_count}/{len(results)} tags successfully from EtherNet/IP")
        return results

    async def discover_tags(self) -> List[Dict[str, Any]]:
        """
        Discover all available tags from PLC

        Returns:
            List of discovered tag definitions
        """
        if not self.connected or not self.plc:
            logger.warning("Cannot discover tags - not connected to PLC")
            return []

        try:
            discovered = []

            # Get controller-scoped tags
            if hasattr(self.plc, 'tags') and self.plc.tags:
                for tag_name, tag_info in self.plc.tags.items():
                    discovered.append({
                        'name': tag_name,
                        'address': tag_name,
                        'data_type': str(tag_info.get('data_type', 'unknown')),
                        'dimensions': tag_info.get('dimensions', []),
                        'scope': 'controller'
                    })

            # Get program-scoped tags if init_program_tags was True
            if self.init_program_tags and hasattr(self.plc, 'programs'):
                for prog_name, prog_info in self.plc.programs.items():
                    if 'tags' in prog_info:
                        for tag_name, tag_info in prog_info['tags'].items():
                            discovered.append({
                                'name': f"{prog_name}.{tag_name}",
                                'address': f"Program:{prog_name}.{tag_name}",
                                'data_type': str(tag_info.get('data_type', 'unknown')),
                                'dimensions': tag_info.get('dimensions', []),
                                'scope': prog_name
                            })

            logger.info(f"🔍 Discovered {len(discovered)} tags from EtherNet/IP PLC")
            return discovered

        except Exception as e:
            logger.error(f"❌ Error discovering tags: {e}")
            return []


def create_ethernetip_adapter(
    adapter_id: str,
    host: str,
    port: int = 44818,
    slot: int = 0,
    tags: List[Dict[str, str]] = None,
    scan_rate_ms: int = 500,
    **kwargs
) -> EtherNetIPAdapter:
    """
    Convenience function to create EtherNet/IP adapter

    Args:
        adapter_id: Unique adapter identifier
        host: PLC IP address
        port: EtherNet/IP port (default: 44818)
        slot: CPU slot number (default: 0)
        tags: List of tags to monitor
        scan_rate_ms: How often to read tags (default: 500ms)
        **kwargs: Additional configuration options

    Returns:
        Configured EtherNet/IP adapter instance
    """
    config = ProtocolConfig(
        adapter_id=adapter_id,
        protocol_type='ethernetip',
        host=host,
        port=port,
        scan_rate_ms=scan_rate_ms,
        tags=tags or [],
        extra_config={
            'slot': slot,
            'connection_path': kwargs.get('connection_path'),
            'init_tags': kwargs.get('init_tags', True),
            'init_program_tags': kwargs.get('init_program_tags', False),
            **kwargs
        }
    )

    return EtherNetIPAdapter(config)
