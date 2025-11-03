"""
Modbus TCP/RTU Protocol Handler
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import struct
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from ..core.base_protocol import BaseProtocolHandler, TagValue
from ..core.logger import logger


class ModbusHandler(BaseProtocolHandler):
    """
    Modbus TCP/RTU protocol handler using pymodbus library
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize Modbus handler

        Config keys (TCP):
            - mode: "tcp" or "rtu"
            - host: IP address
            - port: TCP port (default: 502)
            - unit_id: Slave/Unit ID (default: 1)

        Config keys (RTU):
            - mode: "rtu"
            - port: Serial port (e.g., /dev/ttyUSB0, COM1)
            - baudrate: Baudrate (default: 9600)
            - bytesize: Data bits (default: 8)
            - parity: 'N', 'E', 'O' (default: 'N')
            - stopbits: Stop bits (default: 1)
            - unit_id: Slave/Unit ID (default: 1)
        """
        super().__init__(device_id, config)

        self.mode = config.get("mode", "tcp").lower()
        self.unit_id = config.get("unit_id", 1)

        if self.mode == "tcp":
            self.host = config.get("host")
            self.port = config.get("port", 502)
            self.client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=config.get("timeout", 5)
            )
        else:  # RTU
            self.serial_port = config.get("port")
            self.baudrate = config.get("baudrate", 9600)
            self.bytesize = config.get("bytesize", 8)
            self.parity = config.get("parity", "N")
            self.stopbits = config.get("stopbits", 1)
            self.client = AsyncModbusSerialClient(
                port=self.serial_port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=config.get("timeout", 5)
            )

    async def connect(self) -> bool:
        """Connect to Modbus device"""
        async with self._lock:
            try:
                if self.mode == "tcp":
                    logger.info(f"Connecting to Modbus TCP: {self.host}:{self.port}")
                else:
                    logger.info(f"Connecting to Modbus RTU: {self.serial_port}")

                result = await self.client.connect()

                if result:
                    self.update_status(connected=True)
                    logger.info(f"✓ Connected to Modbus device")
                    return True
                else:
                    error_msg = "Modbus connection failed"
                    logger.error(error_msg)
                    self.update_status(connected=False, error=error_msg)
                    return False

            except Exception as e:
                error_msg = f"Modbus connection error: {str(e)}"
                logger.error(error_msg)
                self.update_status(connected=False, error=error_msg)
                return False

    async def disconnect(self) -> bool:
        """Disconnect from Modbus device"""
        async with self._lock:
            try:
                self.client.close()
                self.update_status(connected=False)
                logger.info("Disconnected from Modbus device")
                return True

            except Exception as e:
                logger.error(f"Modbus disconnect error: {str(e)}")
                return False

    def _parse_address(self, address: str) -> tuple:
        """
        Parse Modbus address string

        Formats:
            - "40001" or "4:1" = Holding Register 1
            - "30001" or "3:1" = Input Register 1
            - "10001" or "1:1" = Coil 1
            - "20001" or "2:1" = Discrete Input 1

        Returns:
            (function_code, register_address, data_type)
        """
        # Handle colon format (function:address:type)
        if ":" in address:
            parts = address.split(":")
            function = int(parts[0])
            register = int(parts[1])
            data_type = parts[2] if len(parts) > 2 else "uint16"

            return function, register, data_type

        # Handle traditional format (5-digit)
        addr_int = int(address)
        function = addr_int // 10000
        register = addr_int % 10000

        # Default data type
        data_type = "uint16"

        return function, register, data_type

    async def read_tag(self, tag_address: str) -> Optional[TagValue]:
        """
        Read single Modbus tag

        Address format examples:
            - "40001" - Holding register 1
            - "4:100:float32" - Holding register 100 as float32
            - "3:50:int16" - Input register 50 as signed int16
        """
        try:
            if not self.is_connected:
                await self.connect()

            function, register, data_type = self._parse_address(tag_address)

            # Read based on function code
            if function == 1:  # Coils
                response = await self.client.read_coils(
                    address=register,
                    count=1,
                    slave=self.unit_id
                )
                value = response.bits[0] if response else None

            elif function == 2:  # Discrete Inputs
                response = await self.client.read_discrete_inputs(
                    address=register,
                    count=1,
                    slave=self.unit_id
                )
                value = response.bits[0] if response else None

            elif function == 3:  # Input Registers
                count = 1 if data_type in ["uint16", "int16"] else 2
                response = await self.client.read_input_registers(
                    address=register,
                    count=count,
                    slave=self.unit_id
                )
                value = self._decode_value(response.registers, data_type) if response else None

            elif function == 4:  # Holding Registers
                count = 1 if data_type in ["uint16", "int16"] else 2
                response = await self.client.read_holding_registers(
                    address=register,
                    count=count,
                    slave=self.unit_id
                )
                value = self._decode_value(response.registers, data_type) if response else None

            else:
                logger.error(f"Invalid Modbus function code: {function}")
                return None

            # Check for errors
            if response is None or response.isError():
                quality = "bad"
                value = None
            else:
                quality = "good"

            tag_value = TagValue(
                tag_id=tag_address,
                tag_name=tag_address,
                value=value,
                quality=quality,
                timestamp=datetime.now()
            )

            return tag_value

        except ModbusException as e:
            logger.error(f"Modbus error reading {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return None

        except Exception as e:
            logger.error(f"Failed to read Modbus tag {tag_address}: {str(e)}")
            return None

    def _decode_value(self, registers: List[int], data_type: str) -> Any:
        """Decode register values based on data type"""
        try:
            if data_type == "uint16":
                return registers[0]

            elif data_type == "int16":
                return struct.unpack('>h', struct.pack('>H', registers[0]))[0]

            elif data_type == "uint32":
                # Big-endian (high word first)
                return (registers[0] << 16) | registers[1]

            elif data_type == "int32":
                value = (registers[0] << 16) | registers[1]
                return struct.unpack('>i', struct.pack('>I', value))[0]

            elif data_type == "float32":
                # IEEE 754 float
                bytes_value = struct.pack('>HH', registers[0], registers[1])
                return struct.unpack('>f', bytes_value)[0]

            else:
                return registers[0]

        except Exception as e:
            logger.error(f"Failed to decode value: {str(e)}")
            return registers[0]

    async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
        """Read multiple Modbus tags"""
        results = []

        for address in tag_addresses:
            tag_value = await self.read_tag(address)
            if tag_value:
                results.append(tag_value)

        return results

    async def write_tag(self, tag_address: str, value: Any) -> bool:
        """Write to Modbus tag"""
        try:
            if not self.is_connected:
                await self.connect()

            function, register, data_type = self._parse_address(tag_address)

            # Write based on function code
            if function == 1:  # Coil
                response = await self.client.write_coil(
                    address=register,
                    value=bool(value),
                    slave=self.unit_id
                )

            elif function == 4:  # Holding Register
                if data_type in ["uint16", "int16"]:
                    response = await self.client.write_register(
                        address=register,
                        value=int(value),
                        slave=self.unit_id
                    )
                else:
                    # Multi-register write (float32, uint32, etc.)
                    registers = self._encode_value(value, data_type)
                    response = await self.client.write_registers(
                        address=register,
                        values=registers,
                        slave=self.unit_id
                    )
            else:
                logger.error(f"Cannot write to Modbus function {function}")
                return False

            if response and not response.isError():
                logger.info(f"✓ Wrote value {value} to Modbus tag {tag_address}")
                return True
            else:
                logger.error(f"Modbus write failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Failed to write Modbus tag {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    def _encode_value(self, value: Any, data_type: str) -> List[int]:
        """Encode value to register format"""
        try:
            if data_type == "float32":
                bytes_value = struct.pack('>f', float(value))
                return list(struct.unpack('>HH', bytes_value))

            elif data_type == "uint32":
                return [(int(value) >> 16) & 0xFFFF, int(value) & 0xFFFF]

            elif data_type == "int32":
                bytes_value = struct.pack('>i', int(value))
                return list(struct.unpack('>HH', bytes_value))

            else:
                return [int(value)]

        except Exception as e:
            logger.error(f"Failed to encode value: {str(e)}")
            return [0]

    async def health_check(self) -> bool:
        """Check Modbus device health"""
        try:
            # Try to read a holding register (register 0)
            response = await self.client.read_holding_registers(
                address=0,
                count=1,
                slave=self.unit_id
            )

            if response and not response.isError():
                self.update_status(connected=True)
                return True
            else:
                self.update_status(connected=False, error="Health check failed")
                return False

        except Exception as e:
            logger.error(f"Modbus health check failed: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False
