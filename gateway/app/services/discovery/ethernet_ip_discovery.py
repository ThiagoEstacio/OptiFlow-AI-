"""
EtherNet/IP Device Discovery Service

Discovers Rockwell PLCs on the network using List Identity broadcast.
"""

import asyncio
import socket
import struct
import ipaddress
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import time

from loguru import logger
from pycomm3 import LogixDriver
from pycomm3.cip import CIPDriver


@dataclass
class DiscoveredDevice:
    """Information about a discovered EtherNet/IP device"""
    ip_address: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    device_type: Optional[int] = None
    product_code: Optional[int] = None
    product_name: Optional[str] = None
    serial_number: Optional[str] = None
    revision_major: Optional[int] = None
    revision_minor: Optional[int] = None
    status: Optional[int] = None
    state: Optional[int] = None
    discovered_at: Optional[float] = None
    protocol: str = "EtherNet/IP"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class EtherNetIPDiscoveryService:
    """
    Service for discovering EtherNet/IP devices on the network.

    Uses List Identity (UDP broadcast on port 2222) to discover devices.
    """

    # EtherNet/IP constants
    ENIP_PORT = 44818  # TCP port
    ENIP_UDP_PORT = 2222  # UDP discovery port
    ENCAP_CMD_LIST_IDENTITY = 0x0063
    ENCAP_CMD_LIST_SERVICES = 0x0004

    # Vendor IDs
    VENDORS = {
        1: "Rockwell Automation/Allen-Bradley",
        2: "Omron",
        10: "Schneider Electric",
        42: "Honeywell",
        52: "Mitsubishi Electric",
        85: "DeviceNet Vendor Association",
        174: "Siemens",
    }

    def __init__(self, timeout: float = 2.0, max_devices: int = 100):
        """
        Initialize discovery service.

        Args:
            timeout: Discovery timeout in seconds
            max_devices: Maximum number of devices to discover
        """
        self.timeout = timeout
        self.max_devices = max_devices
        self._discovered: Set[str] = set()

    def _create_list_identity_request(self) -> bytes:
        """
        Create a List Identity request packet.

        Returns:
            Bytes of the request packet
        """
        # EtherNet/IP Encapsulation Header
        # Command: List Identity (0x0063)
        # Length: 0
        # Session Handle: 0
        # Status: 0
        # Sender Context: 0
        # Options: 0

        command = self.ENCAP_CMD_LIST_IDENTITY
        length = 0
        session_handle = 0
        status = 0
        sender_context = b'\x00' * 8
        options = 0

        packet = struct.pack(
            '<HHIIQII',
            command,
            length,
            session_handle,
            status,
            struct.unpack('<Q', sender_context)[0],
            options
        )

        return packet

    def _parse_identity_response(self, data: bytes, source_ip: str) -> Optional[DiscoveredDevice]:
        """
        Parse List Identity response.

        Args:
            data: Response data
            source_ip: Source IP address

        Returns:
            DiscoveredDevice or None if parsing fails
        """
        try:
            # Minimum encapsulation header size
            if len(data) < 24:
                return None

            # Parse encapsulation header
            command, length, session, status = struct.unpack_from('<HHII', data, 0)

            # Verify it's a List Identity response
            if command != self.ENCAP_CMD_LIST_IDENTITY:
                return None

            # Parse identity data (if present)
            if length < 12:
                return DiscoveredDevice(
                    ip_address=source_ip,
                    discovered_at=time.time()
                )

            offset = 24  # After encapsulation header

            # Item count
            item_count = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            if item_count == 0:
                return DiscoveredDevice(
                    ip_address=source_ip,
                    discovered_at=time.time()
                )

            # Item Type Code
            item_type = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Item Length
            item_length = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Parse CIP Identity object
            if len(data) < offset + 20:
                return DiscoveredDevice(
                    ip_address=source_ip,
                    discovered_at=time.time()
                )

            # Protocol version, socket address
            protocol_version = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Socket address (sin_family + sin_port + sin_addr)
            sin_family = struct.unpack_from('<H', data, offset)[0]
            sin_port = struct.unpack_from('>H', data, offset + 2)[0]  # Network byte order
            sin_addr = struct.unpack_from('>I', data, offset + 4)[0]
            offset += 16  # Socket address structure is 16 bytes

            # Vendor ID
            vendor_id = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Device Type
            device_type = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Product Code
            product_code = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Revision
            revision = struct.unpack_from('<BB', data, offset)
            revision_major, revision_minor = revision
            offset += 2

            # Status
            device_status = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            # Serial Number
            serial = struct.unpack_from('<I', data, offset)[0]
            offset += 4

            # Product Name (short string)
            product_name_length = struct.unpack_from('<B', data, offset)[0]
            offset += 1

            product_name = ""
            if product_name_length > 0 and len(data) >= offset + product_name_length:
                product_name = data[offset:offset + product_name_length].decode('utf-8', errors='ignore')

            return DiscoveredDevice(
                ip_address=source_ip,
                vendor_id=vendor_id,
                vendor_name=self.VENDORS.get(vendor_id, f"Unknown ({vendor_id})"),
                device_type=device_type,
                product_code=product_code,
                product_name=product_name,
                serial_number=str(serial),
                revision_major=revision_major,
                revision_minor=revision_minor,
                status=device_status,
                discovered_at=time.time()
            )

        except Exception as e:
            logger.error(f"Error parsing identity response from {source_ip}: {e}")
            return DiscoveredDevice(
                ip_address=source_ip,
                discovered_at=time.time()
            )

    async def scan_network(self, subnet: str = "192.168.1.0/24") -> List[DiscoveredDevice]:
        """
        Scan network for EtherNet/IP devices using UDP broadcast.

        Args:
            subnet: Subnet to scan in CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            List of discovered devices
        """
        devices = []
        self._discovered.clear()

        try:
            # Create UDP socket for broadcast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(self.timeout)

            # Create List Identity request
            request = self._create_list_identity_request()

            # Get network and broadcast address
            network = ipaddress.ip_network(subnet, strict=False)
            broadcast_addr = str(network.broadcast_address)

            logger.info(f"Scanning subnet {subnet} for EtherNet/IP devices...")
            logger.debug(f"Broadcasting to {broadcast_addr}:{self.ENIP_UDP_PORT}")

            # Send broadcast
            sock.sendto(request, (broadcast_addr, self.ENIP_UDP_PORT))

            # Receive responses
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    source_ip = addr[0]

                    # Avoid duplicates
                    if source_ip in self._discovered:
                        continue

                    # Parse response
                    device = self._parse_identity_response(data, source_ip)
                    if device:
                        devices.append(device)
                        self._discovered.add(source_ip)
                        logger.info(f"Discovered device: {source_ip} - {device.product_name}")

                        if len(devices) >= self.max_devices:
                            break

                except socket.timeout:
                    break
                except Exception as e:
                    logger.error(f"Error receiving response: {e}")
                    continue

            sock.close()

        except Exception as e:
            logger.error(f"Error during network scan: {e}")

        logger.info(f"Discovery complete. Found {len(devices)} devices.")
        return devices

    async def scan_ip_range(self, start_ip: str, end_ip: str) -> List[DiscoveredDevice]:
        """
        Scan a range of IP addresses (unicast probe).

        Args:
            start_ip: Starting IP address
            end_ip: Ending IP address

        Returns:
            List of discovered devices
        """
        devices = []
        self._discovered.clear()

        try:
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)

            current = start
            tasks = []

            # Create tasks for parallel scanning
            while current <= end:
                tasks.append(self._probe_device(str(current)))
                current += 1

            # Execute probes with concurrency limit
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, DiscoveredDevice):
                    devices.append(result)

        except Exception as e:
            logger.error(f"Error scanning IP range: {e}")

        return devices

    async def _probe_device(self, ip_address: str) -> Optional[DiscoveredDevice]:
        """
        Probe a specific IP address for EtherNet/IP device.

        Args:
            ip_address: IP address to probe

        Returns:
            DiscoveredDevice or None
        """
        try:
            # Try to connect using LogixDriver
            await asyncio.sleep(0)  # Yield control

            # Use pycomm3's connection test
            plc = LogixDriver(ip_address, init_tags=False)

            try:
                plc.open()

                if plc.connected:
                    # Get device info
                    info = plc.get_plc_info()

                    device = DiscoveredDevice(
                        ip_address=ip_address,
                        vendor_id=1,  # Rockwell
                        vendor_name="Rockwell Automation",
                        product_name=info.get('name', 'Unknown'),
                        serial_number=str(info.get('serial', '')),
                        revision_major=info.get('revision_major', 0),
                        revision_minor=info.get('revision_minor', 0),
                        discovered_at=time.time()
                    )

                    plc.close()
                    logger.info(f"Probed device at {ip_address}: {device.product_name}")
                    return device

            finally:
                plc.close()

        except Exception as e:
            logger.debug(f"No device at {ip_address}: {e}")

        return None

    async def get_device_details(self, ip_address: str, slot: int = 0) -> Optional[Dict]:
        """
        Get detailed information about a specific device.

        Args:
            ip_address: Device IP address
            slot: Slot number

        Returns:
            Dictionary with device details or None
        """
        try:
            plc = LogixDriver(ip_address, slot=slot, init_tags=False)

            plc.open()

            if not plc.connected:
                return None

            # Get PLC info
            info = plc.get_plc_info()

            # Get module info
            modules = []
            try:
                module_info = plc.get_module_info(slot)
                if module_info:
                    modules.append(module_info)
            except:
                pass

            plc.close()

            return {
                "ip_address": ip_address,
                "slot": slot,
                "info": info,
                "modules": modules,
                "vendor": "Rockwell Automation",
                "protocol": "EtherNet/IP"
            }

        except Exception as e:
            logger.error(f"Failed to get device details for {ip_address}: {e}")
            return None
