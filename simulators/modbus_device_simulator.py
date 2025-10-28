#!/usr/bin/env python3
"""
SmartPort Modbus TCP Device Simulator
Simulates industrial devices for testing the Gateway

Usage:
    python modbus_device_simulator.py --host 0.0.0.0 --port 502
"""

import argparse
import logging
import random
import time
import math
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndustrialDataSimulator(Thread):
    """Simulates industrial process data"""

    def __init__(self, context, update_interval=1.0):
        super().__init__(daemon=True)
        self.context = context
        self.update_interval = update_interval
        self.running = True
        self.iteration = 0

    def run(self):
        """Update simulated data continuously"""
        logger.info("Starting data simulator thread")

        while self.running:
            try:
                self.update_data()
                time.sleep(self.update_interval)
                self.iteration += 1
            except Exception as e:
                logger.error(f"Error updating data: {e}")

    def update_data(self):
        """Update register values with simulated data"""
        slave_context = self.context[0x00]

        # Simulate temperature (Holding Register 40001-40010)
        # Range: 20-100°C with sine wave pattern
        base_temp = 60
        temp_variation = 20 * math.sin(self.iteration / 10)
        temperature = int((base_temp + temp_variation) * 10)  # Scaled by 10
        slave_context.setValues(3, 1, [temperature])

        # Simulate pressure (Holding Register 40011-40020)
        # Range: 0-10 bar with random walk
        base_pressure = 50  # 5.0 bar scaled by 10
        pressure_change = random.randint(-5, 5)
        pressure = max(0, min(100, base_pressure + pressure_change))
        slave_context.setValues(3, 11, [pressure])

        # Simulate flow rate (Holding Register 40021-40030)
        # Range: 0-1000 L/min
        flow = int(500 + 200 * math.sin(self.iteration / 15) + random.randint(-50, 50))
        slave_context.setValues(3, 21, [flow])

        # Simulate level (Holding Register 40031-40040)
        # Range: 0-100%
        level = int(50 + 30 * math.cos(self.iteration / 20) + random.randint(-5, 5))
        level = max(0, min(100, level))
        slave_context.setValues(3, 31, [level])

        # Simulate power consumption (Holding Register 40041-40050)
        # Range: 0-10000 W
        power = int(5000 + 2000 * math.sin(self.iteration / 12) + random.randint(-200, 200))
        slave_context.setValues(3, 41, [power])

        # Simulate pump speed (Holding Register 40051-40060)
        # Range: 0-3000 RPM
        rpm = int(1500 + 500 * math.sin(self.iteration / 8))
        slave_context.setValues(3, 51, [rpm])

        # Simulate digital inputs (Coils 1-16)
        # Motor running, valve open, alarm status, etc.
        motor_running = 1 if temp_variation > 0 else 0
        valve_open = 1 if pressure > 40 else 0
        alarm_active = 1 if temperature > 850 or pressure > 90 else 0
        emergency_stop = 0

        slave_context.setValues(1, 1, [motor_running])
        slave_context.setValues(1, 2, [valve_open])
        slave_context.setValues(1, 3, [alarm_active])
        slave_context.setValues(1, 4, [emergency_stop])

        # Log current values periodically
        if self.iteration % 10 == 0:
            logger.info(
                f"Simulated Data - Temp: {temperature/10:.1f}°C, "
                f"Pressure: {pressure/10:.1f} bar, "
                f"Flow: {flow} L/min, "
                f"Level: {level}%, "
                f"Power: {power} W, "
                f"RPM: {rpm}, "
                f"Motor: {motor_running}, "
                f"Alarm: {alarm_active}"
            )

    def stop(self):
        """Stop the simulator thread"""
        self.running = False


def create_modbus_context():
    """Create Modbus datastore with initial values"""

    # Initialize data blocks
    # Coils (digital outputs): 10000 addresses
    coils = ModbusSequentialDataBlock(1, [0] * 10000)

    # Discrete Inputs (digital inputs): 10000 addresses
    discrete_inputs = ModbusSequentialDataBlock(1, [0] * 10000)

    # Holding Registers (read/write analog): 10000 addresses
    holding_registers = ModbusSequentialDataBlock(1, [0] * 10000)

    # Input Registers (read-only analog): 10000 addresses
    input_registers = ModbusSequentialDataBlock(1, [0] * 10000)

    # Create slave context
    slave_context = ModbusSlaveContext(
        di=discrete_inputs,
        co=coils,
        hr=holding_registers,
        ir=input_registers
    )

    # Create server context (single slave with ID 0x00)
    context = ModbusServerContext(slaves=slave_context, single=True)

    return context


def setup_device_identification():
    """Setup Modbus device identification"""
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'SmartPort'
    identity.ProductCode = 'SIM-MODBUS-01'
    identity.VendorUrl = 'https://smartport.io'
    identity.ProductName = 'SmartPort Modbus TCP Simulator'
    identity.ModelName = 'Industrial Process Simulator'
    identity.MajorMinorRevision = '1.0.0'

    return identity


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='SmartPort Modbus TCP Device Simulator')
    parser.add_argument('--host', default='0.0.0.0', help='Host address to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=502, help='Port to listen (default: 502)')
    parser.add_argument('--update-interval', type=float, default=1.0, help='Data update interval in seconds (default: 1.0)')

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("SmartPort Modbus TCP Device Simulator")
    logger.info("="*60)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Update Interval: {args.update_interval}s")
    logger.info("="*60)

    # Create Modbus context
    context = create_modbus_context()

    # Setup device identification
    identity = setup_device_identification()

    # Start data simulator
    simulator = IndustrialDataSimulator(context, args.update_interval)
    simulator.start()

    logger.info("Data simulator started")
    logger.info(f"Modbus TCP server starting on {args.host}:{args.port}")
    logger.info("Register mapping:")
    logger.info("  40001: Temperature (°C * 10)")
    logger.info("  40011: Pressure (bar * 10)")
    logger.info("  40021: Flow Rate (L/min)")
    logger.info("  40031: Level (%)")
    logger.info("  40041: Power (W)")
    logger.info("  40051: Pump Speed (RPM)")
    logger.info("  Coil 1: Motor Running")
    logger.info("  Coil 2: Valve Open")
    logger.info("  Coil 3: Alarm Active")
    logger.info("  Coil 4: Emergency Stop")
    logger.info("="*60)

    try:
        # Start Modbus TCP server
        StartTcpServer(
            context=context,
            identity=identity,
            address=(args.host, args.port)
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down simulator...")
        simulator.stop()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        simulator.stop()
        raise


if __name__ == '__main__':
    main()
