"""
Modbus TCP Simulator for OptiFlow Testing
Simulates a PLC with holding registers for industrial data
"""

import asyncio
import logging
import random
import math
from datetime import datetime
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext, ModbusSequentialDataBlock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register mapping (Holding Registers starting at 40001)
REGISTERS = {
    # Pump Station (40001-40010)
    0: "pump1_flow_lpm",      # 40001: Pump 1 Flow (L/min)
    1: "pump1_pressure_bar",  # 40002: Pump 1 Pressure (bar)
    2: "pump1_current_a",     # 40003: Pump 1 Current (A)
    3: "pump1_speed_rpm",     # 40004: Pump 1 Speed (RPM)
    4: "pump1_temp_c",        # 40005: Pump 1 Temperature (°C)
    5: "pump2_flow_lpm",      # 40006: Pump 2 Flow (L/min)
    6: "pump2_pressure_bar",  # 40007: Pump 2 Pressure (bar)
    7: "pump2_current_a",     # 40008: Pump 2 Current (A)
    8: "pump2_speed_rpm",     # 40009: Pump 2 Speed (RPM)
    9: "pump2_temp_c",        # 40010: Pump 2 Temperature (°C)

    # Tank Levels (40011-40015)
    10: "tank1_level_pct",    # 40011: Tank 1 Level (%)
    11: "tank2_level_pct",    # 40012: Tank 2 Level (%)
    12: "tank3_level_pct",    # 40013: Tank 3 Level (%)
    13: "tank1_temp_c",       # 40014: Tank 1 Temperature (°C)
    14: "tank2_temp_c",       # 40015: Tank 2 Temperature (°C)

    # Valve Positions (40016-40020)
    15: "valve1_position",    # 40016: Valve 1 Position (%)
    16: "valve2_position",    # 40017: Valve 2 Position (%)
    17: "valve3_position",    # 40018: Valve 3 Position (%)
    18: "valve4_position",    # 40019: Valve 4 Position (%)
    19: "valve5_position",    # 40020: Valve 5 Position (%)

    # Energy Meters (40021-40025)
    20: "total_power_kw",     # 40021: Total Power (kW)
    21: "daily_energy_kwh",   # 40022: Daily Energy (kWh)
    22: "power_factor",       # 40023: Power Factor (x100)
    23: "voltage_v",          # 40024: Voltage (V)
    24: "frequency_hz",       # 40025: Frequency (Hz x10)
}


class ModbusSimulator:
    """Simulates industrial Modbus device with realistic values"""

    def __init__(self):
        self.time_offset = 0
        self.pump1_running = True
        self.pump2_running = True

    def get_simulated_values(self) -> dict:
        """Generate realistic simulated values"""
        t = self.time_offset
        self.time_offset += 0.1

        # Sinusoidal variations with noise
        def with_noise(base, amplitude, noise_pct=0.02):
            variation = amplitude * math.sin(t * 0.1)
            noise = random.uniform(-noise_pct, noise_pct) * base
            return base + variation + noise

        values = {}

        # Pump 1 (running)
        if self.pump1_running:
            values[0] = int(with_noise(150, 20))      # Flow: ~150 L/min
            values[1] = int(with_noise(45, 5) * 10)   # Pressure: ~4.5 bar (x10)
            values[2] = int(with_noise(12, 2) * 10)   # Current: ~12A (x10)
            values[3] = int(with_noise(1750, 50))     # Speed: ~1750 RPM
            values[4] = int(with_noise(55, 5) * 10)   # Temp: ~55°C (x10)
        else:
            values[0] = 0
            values[1] = 0
            values[2] = 0
            values[3] = 0
            values[4] = int(25 * 10)  # Ambient temp

        # Pump 2 (running)
        if self.pump2_running:
            values[5] = int(with_noise(140, 15))      # Flow
            values[6] = int(with_noise(42, 4) * 10)   # Pressure
            values[7] = int(with_noise(11, 1.5) * 10) # Current
            values[8] = int(with_noise(1720, 40))     # Speed
            values[9] = int(with_noise(52, 4) * 10)   # Temp
        else:
            values[5] = 0
            values[6] = 0
            values[7] = 0
            values[8] = 0
            values[9] = int(25 * 10)

        # Tank Levels (slow change)
        values[10] = int(with_noise(65, 10))   # Tank 1: ~65%
        values[11] = int(with_noise(78, 8))    # Tank 2: ~78%
        values[12] = int(with_noise(45, 12))   # Tank 3: ~45%
        values[13] = int(with_noise(28, 3) * 10)  # Tank 1 Temp
        values[14] = int(with_noise(30, 2) * 10)  # Tank 2 Temp

        # Valve Positions
        values[15] = int(with_noise(75, 5))    # Valve 1: ~75%
        values[16] = int(with_noise(100, 0))   # Valve 2: 100% (fully open)
        values[17] = int(with_noise(50, 10))   # Valve 3: ~50%
        values[18] = int(with_noise(25, 5))    # Valve 4: ~25%
        values[19] = int(with_noise(0, 0))     # Valve 5: 0% (closed)

        # Energy
        values[20] = int(with_noise(85, 15) * 10)   # Power: ~85 kW (x10)
        values[21] = int(with_noise(450, 20))       # Daily Energy: ~450 kWh
        values[22] = int(with_noise(92, 3))         # Power Factor: 0.92
        values[23] = int(with_noise(380, 10))       # Voltage: ~380V
        values[24] = int(with_noise(500, 1))        # Frequency: 50.0 Hz (x10)

        return values


simulator = ModbusSimulator()


async def update_registers(context):
    """Periodically update register values"""
    while True:
        try:
            values = simulator.get_simulated_values()

            # Update holding registers (function code 3)
            slave_context = context[0]
            for addr, value in values.items():
                # Ensure value is within valid range (0-65535 for 16-bit)
                value = max(0, min(65535, value))
                slave_context.setValues(3, addr, [value])

            logger.debug(f"Updated {len(values)} registers")

        except Exception as e:
            logger.error(f"Error updating registers: {e}")

        await asyncio.sleep(1.0)  # Update every second


async def run_server():
    """Start the Modbus TCP server"""

    # Initialize data store with 100 holding registers
    store = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr=ModbusSequentialDataBlock(0, [0]*100),  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0]*100),  # Input Registers
    )
    context = ModbusServerContext(devices=store, single=True)

    # Start background task to update values
    asyncio.create_task(update_registers(context))

    logger.info("=" * 50)
    logger.info("Modbus TCP Simulator Starting")
    logger.info("=" * 50)
    logger.info(f"Host: 0.0.0.0:502")
    logger.info(f"Registers: {len(REGISTERS)} holding registers")
    logger.info("Register Map:")
    for addr, name in REGISTERS.items():
        logger.info(f"  40{addr+1:03d}: {name}")
    logger.info("=" * 50)

    # Start server
    await StartAsyncTcpServer(
        context=context,
        address=("0.0.0.0", 502)
    )


if __name__ == "__main__":
    asyncio.run(run_server())
