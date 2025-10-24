"""
Network Scanner Service

Discovers devices on the network by scanning IP ranges and ports.
Similar to KEPServerEX network discovery.
"""
import asyncio
import socket
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Represents a discovered device on the network"""
    ip: str
    port: int
    protocol: Optional[str] = None
    responsive: bool = False
    response_time_ms: Optional[float] = None
    discovered_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.discovered_at is None:
            self.discovered_at = datetime.utcnow()


class NetworkScanner:
    """
    Network scanner for industrial protocols

    Discovers devices by:
    - Scanning IP ranges
    - Testing common industrial ports
    - Identifying protocols (Modbus, OPC UA, S7)
    """

    # Common industrial protocol ports
    PROTOCOL_PORTS = {
        502: "modbus",      # Modbus TCP
        4840: "opcua",      # OPC UA
        102: "s7",          # Siemens S7
        44818: "ethernet_ip", # EtherNet/IP
        2222: "bacnet",     # BACnet
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self.discovered_devices: List[DiscoveredDevice] = []

    async def scan_ip_range(
        self,
        start_ip: str,
        end_ip: str,
        ports: List[int] = None,
        max_concurrent: int = 50
    ) -> List[DiscoveredDevice]:
        """
        Scan a range of IP addresses for devices

        Args:
            start_ip: Starting IP address (e.g., "192.168.1.1")
            end_ip: Ending IP address (e.g., "192.168.1.254")
            ports: List of ports to scan (default: common industrial ports)
            max_concurrent: Maximum concurrent scans

        Returns:
            List of discovered devices
        """
        if ports is None:
            ports = list(self.PROTOCOL_PORTS.keys())

        logger.info(f"Starting network scan: {start_ip} to {end_ip}, ports: {ports}")

        # Generate IP range
        ip_list = self._generate_ip_range(start_ip, end_ip)

        # Create scan tasks
        tasks = []
        semaphore = asyncio.Semaphore(max_concurrent)

        for ip in ip_list:
            for port in ports:
                tasks.append(self._scan_with_semaphore(semaphore, ip, port))

        # Execute scans
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        devices = [r for r in results if isinstance(r, DiscoveredDevice) and r.responsive]

        self.discovered_devices.extend(devices)

        logger.info(f"Scan complete. Found {len(devices)} devices")
        return devices

    async def _scan_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        ip: str,
        port: int
    ) -> Optional[DiscoveredDevice]:
        """Scan with concurrency limit"""
        async with semaphore:
            return await self.scan_port(ip, port)

    async def scan_port(self, ip: str, port: int) -> Optional[DiscoveredDevice]:
        """
        Test if a specific port is open on an IP

        Args:
            ip: IP address to scan
            port: Port number to test

        Returns:
            DiscoveredDevice if port is open, None otherwise
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Try to connect
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )

            # Connection successful
            writer.close()
            await writer.wait_closed()

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            device = DiscoveredDevice(
                ip=ip,
                port=port,
                protocol=self.PROTOCOL_PORTS.get(port),
                responsive=True,
                response_time_ms=response_time
            )

            logger.debug(f"Found device: {ip}:{port} ({device.protocol}) - {response_time:.1f}ms")
            return device

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # Port not open or timeout
            return None
        except Exception as e:
            logger.debug(f"Error scanning {ip}:{port}: {e}")
            return None

    async def identify_protocol(self, ip: str, port: int) -> Optional[str]:
        """
        Identify the protocol running on a port

        Attempts to identify protocol by:
        - Port number (common ports)
        - Protocol handshake/banner

        Args:
            ip: IP address
            port: Port number

        Returns:
            Protocol name or None
        """
        # First, check if it's a known port
        if port in self.PROTOCOL_PORTS:
            return self.PROTOCOL_PORTS[port]

        # Try to identify by protocol handshake
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )

            # For some protocols, read initial banner
            try:
                banner = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=1.0
                )

                # Analyze banner to identify protocol
                # This is protocol-specific and can be expanded

            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except Exception as e:
            logger.debug(f"Error identifying protocol {ip}:{port}: {e}")

        return None

    def _generate_ip_range(self, start_ip: str, end_ip: str) -> List[str]:
        """
        Generate list of IP addresses in range

        Args:
            start_ip: Starting IP (e.g., "192.168.1.1")
            end_ip: Ending IP (e.g., "192.168.1.254")

        Returns:
            List of IP addresses
        """
        start_parts = list(map(int, start_ip.split('.')))
        end_parts = list(map(int, end_ip.split('.')))

        # Convert to integers for range calculation
        start_int = (start_parts[0] << 24) + (start_parts[1] << 16) + \
                    (start_parts[2] << 8) + start_parts[3]
        end_int = (end_parts[0] << 24) + (end_parts[1] << 16) + \
                  (end_parts[2] << 8) + end_parts[3]

        ip_list = []
        for ip_int in range(start_int, end_int + 1):
            ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}." \
                 f"{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
            ip_list.append(ip)

        return ip_list

    def get_discovered_devices(
        self,
        protocol: Optional[str] = None
    ) -> List[DiscoveredDevice]:
        """
        Get list of discovered devices

        Args:
            protocol: Filter by protocol (optional)

        Returns:
            List of discovered devices
        """
        if protocol:
            return [d for d in self.discovered_devices if d.protocol == protocol]
        return self.discovered_devices

    def clear_discovered_devices(self):
        """Clear the list of discovered devices"""
        self.discovered_devices = []
