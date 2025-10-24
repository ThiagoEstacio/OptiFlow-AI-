"""
Modbus Discovery Service

Discovers Modbus devices, unit IDs, and register maps automatically.
Similar to KEPServerEX Modbus discovery.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Modbus client
try:
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.exceptions import ModbusException
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False
    logger.warning("pymodbus not installed. Modbus discovery will not work.")

logger = logging.getLogger(__name__)


@dataclass
class ModbusRegisterRange:
    """Represents a range of readable/writable registers"""
    start_address: int
    end_address: int
    register_type: str  # "holding", "input", "coil", "discrete"
    accessible: bool = False
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class ModbusDevice:
    """Represents a discovered Modbus device"""
    ip: str
    port: int = 502
    unit_id: int = 1
    responsive: bool = False
    vendor: Optional[str] = None
    model: Optional[str] = None
    register_ranges: List[ModbusRegisterRange] = field(default_factory=list)
    discovered_tags: List[Dict[str, Any]] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.utcnow)


class ModbusDiscovery:
    """
    Modbus device and register discovery

    Features:
    - Scan for active unit IDs (1-247)
    - Map holding registers
    - Map input registers
    - Map coils and discrete inputs
    - Detect vendor/model (if available)
    - Generate tag suggestions
    """

    def __init__(self, timeout: int = 3):
        self.timeout = timeout
        self.discovered_devices: List[ModbusDevice] = []

    async def scan_unit_ids(
        self,
        ip: str,
        port: int = 502,
        unit_id_range: Tuple[int, int] = (1, 10),
        test_register: int = 0
    ) -> List[int]:
        """
        Scan for active Modbus unit IDs

        Args:
            ip: IP address of Modbus device
            port: Modbus port (default 502)
            unit_id_range: Range of unit IDs to scan (start, end)
            test_register: Register address to test (default 0)

        Returns:
            List of responsive unit IDs
        """
        if not HAS_MODBUS:
            logger.error("pymodbus not installed")
            return []

        logger.info(f"Scanning Modbus unit IDs on {ip}:{port} range {unit_id_range}")

        client = AsyncModbusTcpClient(ip, port=port, timeout=self.timeout)
        await client.connect()

        active_units = []

        try:
            for unit_id in range(unit_id_range[0], unit_id_range[1] + 1):
                try:
                    # Try to read holding register 0
                    result = await client.read_holding_registers(
                        test_register,
                        count=1,
                        slave=unit_id
                    )

                    if not result.isError():
                        active_units.append(unit_id)
                        logger.info(f"Found active unit ID: {unit_id}")
                except Exception as e:
                    logger.debug(f"Unit ID {unit_id} not responsive: {e}")

        finally:
            client.close()

        logger.info(f"Scan complete. Found {len(active_units)} active unit IDs")
        return active_units

    async def map_registers(
        self,
        ip: str,
        port: int,
        unit_id: int,
        register_types: List[str] = None
    ) -> ModbusDevice:
        """
        Map all accessible registers for a Modbus device

        Args:
            ip: IP address
            port: Modbus port
            unit_id: Unit ID to map
            register_types: Types to map (default: ["holding", "input"])

        Returns:
            ModbusDevice with mapped registers
        """
        if not HAS_MODBUS:
            logger.error("pymodbus not installed")
            return None

        if register_types is None:
            register_types = ["holding", "input"]

        logger.info(f"Mapping registers for {ip}:{port} unit {unit_id}")

        device = ModbusDevice(ip=ip, port=port, unit_id=unit_id, responsive=True)

        client = AsyncModbusTcpClient(ip, port=port, timeout=self.timeout)
        await client.connect()

        try:
            # Map each register type
            if "holding" in register_types:
                holding_ranges = await self._scan_register_range(
                    client, unit_id, "holding", max_address=1000, block_size=10
                )
                device.register_ranges.extend(holding_ranges)

            if "input" in register_types:
                input_ranges = await self._scan_register_range(
                    client, unit_id, "input", max_address=1000, block_size=10
                )
                device.register_ranges.extend(input_ranges)

            if "coil" in register_types:
                coil_ranges = await self._scan_register_range(
                    client, unit_id, "coil", max_address=1000, block_size=10
                )
                device.register_ranges.extend(coil_ranges)

            if "discrete" in register_types:
                discrete_ranges = await self._scan_register_range(
                    client, unit_id, "discrete", max_address=1000, block_size=10
                )
                device.register_ranges.extend(discrete_ranges)

            # Try to detect vendor/model
            device.vendor, device.model = await self._detect_vendor(client, unit_id)

            # Generate tag suggestions
            device.discovered_tags = self._generate_tag_suggestions(device)

        finally:
            client.close()

        self.discovered_devices.append(device)

        logger.info(f"Mapping complete. Found {len(device.register_ranges)} register ranges")
        logger.info(f"Generated {len(device.discovered_tags)} tag suggestions")

        return device

    async def _scan_register_range(
        self,
        client: AsyncModbusTcpClient,
        unit_id: int,
        register_type: str,
        max_address: int = 1000,
        block_size: int = 10
    ) -> List[ModbusRegisterRange]:
        """
        Scan a range of addresses to find accessible registers

        Args:
            client: Modbus client
            unit_id: Unit ID
            register_type: "holding", "input", "coil", or "discrete"
            max_address: Maximum address to scan
            block_size: Number of registers to read per request

        Returns:
            List of accessible register ranges
        """
        ranges = []
        current_range = None

        for address in range(0, max_address, block_size):
            try:
                # Try to read a block of registers
                if register_type == "holding":
                    result = await client.read_holding_registers(
                        address, count=block_size, slave=unit_id
                    )
                elif register_type == "input":
                    result = await client.read_input_registers(
                        address, count=block_size, slave=unit_id
                    )
                elif register_type == "coil":
                    result = await client.read_coils(
                        address, count=block_size, slave=unit_id
                    )
                elif register_type == "discrete":
                    result = await client.read_discrete_inputs(
                        address, count=block_size, slave=unit_id
                    )
                else:
                    continue

                if not result.isError():
                    # Registers are accessible
                    if current_range is None:
                        # Start new range
                        current_range = ModbusRegisterRange(
                            start_address=address,
                            end_address=address + block_size - 1,
                            register_type=register_type,
                            accessible=True
                        )
                        if hasattr(result, 'registers'):
                            current_range.sample_values = result.registers[:5]
                        elif hasattr(result, 'bits'):
                            current_range.sample_values = result.bits[:5]
                    else:
                        # Extend existing range
                        current_range.end_address = address + block_size - 1
                else:
                    # Registers not accessible, close current range
                    if current_range is not None:
                        ranges.append(current_range)
                        current_range = None

            except Exception as e:
                # Error reading, close current range
                if current_range is not None:
                    ranges.append(current_range)
                    current_range = None

        # Add last range if exists
        if current_range is not None:
            ranges.append(current_range)

        logger.debug(f"Found {len(ranges)} {register_type} register ranges")
        return ranges

    async def _detect_vendor(
        self,
        client: AsyncModbusTcpClient,
        unit_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to detect device vendor and model

        Some Modbus devices have vendor/model info in specific registers.
        This is not standardized, so we try common locations.

        Args:
            client: Modbus client
            unit_id: Unit ID

        Returns:
            Tuple of (vendor, model) or (None, None)
        """
        # Try common vendor identification registers
        # This varies by manufacturer
        # For now, return None (can be expanded later)
        return None, None

    def _generate_tag_suggestions(self, device: ModbusDevice) -> List[Dict[str, Any]]:
        """
        Generate tag suggestions from discovered registers

        Args:
            device: Modbus device with mapped registers

        Returns:
            List of suggested tags
        """
        tags = []
        tag_counter = 0

        for reg_range in device.register_ranges:
            if not reg_range.accessible:
                continue

            # Generate tags for each register in the range
            # Limit to first 10 registers per range to avoid overwhelming
            num_tags = min(10, reg_range.end_address - reg_range.start_address + 1)

            for i in range(num_tags):
                address = reg_range.start_address + i
                tag_name = f"{reg_range.register_type.upper()}_{address}"

                tag = {
                    "name": tag_name,
                    "address": f"{reg_range.register_type}:{address}",
                    "data_type": "Int16" if reg_range.register_type in ["holding", "input"] else "Boolean",
                    "description": f"{reg_range.register_type.title()} register at address {address}",
                    "unit": "",
                    "writable": reg_range.register_type == "holding",
                    "device_ip": device.ip,
                    "device_port": device.port,
                    "unit_id": device.unit_id
                }

                # Add sample value if available
                if i < len(reg_range.sample_values):
                    tag["sample_value"] = reg_range.sample_values[i]

                tags.append(tag)
                tag_counter += 1

        return tags

    def get_discovered_devices(self) -> List[ModbusDevice]:
        """Get list of all discovered Modbus devices"""
        return self.discovered_devices

    def clear_discovered_devices(self):
        """Clear the list of discovered devices"""
        self.discovered_devices = []
