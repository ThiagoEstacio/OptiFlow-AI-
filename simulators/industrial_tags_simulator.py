#!/usr/bin/env python3
"""
Industrial Tags Simulator for OptiFlow AI Platform
Generates realistic industrial data for all visualization components

Similar to PI Vision and Power BI data sources
Supports all tag categories: process, energy, quality, production, maintenance, alarm, setpoint, status
"""

import time
import math
import random
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endianness
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IndustrialTagsSimulator:
    """
    Complete industrial tags simulator
    Generates data for multiple industrial scenarios
    """

    def __init__(self, host="0.0.0.0", port=5020, update_interval=1.0):
        self.host = host
        self.port = port
        self.update_interval = update_interval
        self.running = False
        self.iteration = 0

        # Process variables state
        self.state = {
            # PROCESS TAGS
            "temperature": 65.0,
            "pressure": 5.0,
            "flow_rate": 500.0,
            "level": 50.0,
            "ph": 7.0,
            "conductivity": 1000.0,
            "density": 1.2,
            "viscosity": 10.0,

            # ENERGY TAGS
            "power_consumption": 5000.0,
            "current": 100.0,
            "voltage": 380.0,
            "power_factor": 0.85,
            "energy_total": 0.0,
            "frequency": 60.0,

            # PRODUCTION TAGS
            "production_rate": 100.0,
            "production_count": 0,
            "cycle_time": 30.0,
            "oee": 85.0,
            "quality_rate": 98.5,
            "performance_rate": 95.0,

            # EQUIPMENT TAGS
            "motor_speed": 1500.0,
            "motor_torque": 75.0,
            "bearing_temp": 45.0,
            "vibration_x": 2.5,
            "vibration_y": 2.3,
            "vibration_z": 1.8,

            # STATUS/ALARM TAGS (binary)
            "motor_running": 1,
            "valve_open": 1,
            "pump_running": 1,
            "alarm_high_temp": 0,
            "alarm_high_pressure": 0,
            "emergency_stop": 0,
            "maintenance_mode": 0,
            "auto_mode": 1,
        }

        # Tag definitions with metadata (like PI Vision tags)
        self.tag_definitions = self._create_tag_definitions()

        # Initialize Modbus data store
        self._init_modbus_store()

    def _create_tag_definitions(self) -> Dict:
        """
        Create tag definitions with metadata
        Similar to PI Vision tag configuration
        """
        return {
            # PROCESS TAGS - Analog (Holding Registers)
            "TEMP_REACTOR_01": {
                "address": 40001, "type": "float", "unit": "°C", "category": "process",
                "min": 20, "max": 100, "alarm_high": 85, "alarm_low": 30,
                "description": "Reactor temperature sensor"
            },
            "PRES_VESSEL_01": {
                "address": 40003, "type": "float", "unit": "bar", "category": "process",
                "min": 0, "max": 10, "alarm_high": 9, "alarm_low": 1,
                "description": "Pressure vessel gauge"
            },
            "FLOW_INLET_01": {
                "address": 40005, "type": "float", "unit": "L/min", "category": "process",
                "min": 0, "max": 1000, "alarm_high": 950, "alarm_low": 50,
                "description": "Inlet flow meter"
            },
            "LEVEL_TANK_01": {
                "address": 40007, "type": "float", "unit": "%", "category": "process",
                "min": 0, "max": 100, "alarm_high": 90, "alarm_low": 10,
                "description": "Tank level transmitter"
            },
            "PH_ANALYZER_01": {
                "address": 40009, "type": "float", "unit": "pH", "category": "quality",
                "min": 0, "max": 14, "alarm_high": 9, "alarm_low": 5,
                "description": "pH analyzer"
            },
            "COND_ANALYZER_01": {
                "address": 40011, "type": "float", "unit": "µS/cm", "category": "quality",
                "min": 0, "max": 5000, "alarm_high": 4500, "alarm_low": 100,
                "description": "Conductivity analyzer"
            },

            # ENERGY TAGS
            "POWER_MOTOR_01": {
                "address": 40013, "type": "float", "unit": "kW", "category": "energy",
                "min": 0, "max": 10000, "alarm_high": 9500, "alarm_low": 0,
                "description": "Motor power consumption"
            },
            "CURRENT_MOTOR_01": {
                "address": 40015, "type": "float", "unit": "A", "category": "energy",
                "min": 0, "max": 200, "alarm_high": 190, "alarm_low": 0,
                "description": "Motor current"
            },
            "VOLTAGE_LINE_01": {
                "address": 40017, "type": "float", "unit": "V", "category": "energy",
                "min": 0, "max": 500, "alarm_high": 420, "alarm_low": 340,
                "description": "Line voltage"
            },
            "PF_MOTOR_01": {
                "address": 40019, "type": "float", "unit": "", "category": "energy",
                "min": 0, "max": 1, "alarm_high": 1, "alarm_low": 0.7,
                "description": "Power factor"
            },

            # PRODUCTION TAGS
            "RATE_PRODUCTION": {
                "address": 40021, "type": "float", "unit": "units/h", "category": "production",
                "min": 0, "max": 200, "alarm_high": 0, "alarm_low": 50,
                "description": "Production rate"
            },
            "COUNT_PRODUCTION": {
                "address": 40023, "type": "integer", "unit": "units", "category": "production",
                "min": 0, "max": 999999, "alarm_high": 0, "alarm_low": 0,
                "description": "Production counter"
            },
            "OEE_LINE_01": {
                "address": 40025, "type": "float", "unit": "%", "category": "production",
                "min": 0, "max": 100, "alarm_high": 0, "alarm_low": 70,
                "description": "Overall Equipment Effectiveness"
            },
            "QUALITY_RATE": {
                "address": 40027, "type": "float", "unit": "%", "category": "quality",
                "min": 0, "max": 100, "alarm_high": 0, "alarm_low": 95,
                "description": "Quality rate"
            },

            # EQUIPMENT/MAINTENANCE TAGS
            "SPEED_MOTOR_01": {
                "address": 40029, "type": "float", "unit": "RPM", "category": "process",
                "min": 0, "max": 3000, "alarm_high": 2900, "alarm_low": 100,
                "description": "Motor speed"
            },
            "TEMP_BEARING_01": {
                "address": 40031, "type": "float", "unit": "°C", "category": "maintenance",
                "min": 20, "max": 100, "alarm_high": 80, "alarm_low": 0,
                "description": "Bearing temperature"
            },
            "VIB_X_MOTOR_01": {
                "address": 40033, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 10, "alarm_high": 7.5, "alarm_low": 0,
                "description": "Vibration X-axis"
            },
            "VIB_Y_MOTOR_01": {
                "address": 40035, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 10, "alarm_high": 7.5, "alarm_low": 0,
                "description": "Vibration Y-axis"
            },

            # DIGITAL/STATUS TAGS (Coils)
            "STATUS_MOTOR_RUNNING": {
                "address": 1, "type": "boolean", "unit": "", "category": "status",
                "description": "Motor running status"
            },
            "STATUS_VALVE_OPEN": {
                "address": 2, "type": "boolean", "unit": "", "category": "status",
                "description": "Valve open status"
            },
            "STATUS_PUMP_RUNNING": {
                "address": 3, "type": "boolean", "unit": "", "category": "status",
                "description": "Pump running status"
            },
            "ALARM_HIGH_TEMP": {
                "address": 4, "type": "boolean", "unit": "", "category": "alarm",
                "description": "High temperature alarm"
            },
            "ALARM_HIGH_PRES": {
                "address": 5, "type": "boolean", "unit": "", "category": "alarm",
                "description": "High pressure alarm"
            },
            "ALARM_EMERGENCY": {
                "address": 6, "type": "boolean", "unit": "", "category": "alarm",
                "description": "Emergency stop"
            },
            "MODE_MAINTENANCE": {
                "address": 7, "type": "boolean", "unit": "", "category": "status",
                "description": "Maintenance mode"
            },
            "MODE_AUTO": {
                "address": 8, "type": "boolean", "unit": "", "category": "status",
                "description": "Automatic mode"
            },
        }

    def _init_modbus_store(self):
        """Initialize Modbus data store"""
        # Holding registers (analog values) - 100 registers
        holding_registers = ModbusSequentialDataBlock(40001, [0] * 100)

        # Coils (digital outputs) - 100 coils
        coils = ModbusSequentialDataBlock(1, [False] * 100)

        # Create slave context
        self.slave_context = ModbusSlaveContext(
            di=None,  # Discrete Inputs
            co=coils,  # Coils
            hr=holding_registers,  # Holding Registers
            ir=None,  # Input Registers
        )

        # Create server context
        self.context = ModbusServerContext(slaves=self.slave_context, single=True)

    def update_process_values(self):
        """Update process values with realistic patterns"""
        t = self.iteration * self.update_interval

        # PROCESS TAGS - Realistic patterns
        # Temperature: slow sine wave with noise
        self.state["temperature"] = 65 + 15 * math.sin(t / 100) + random.gauss(0, 0.5)

        # Pressure: correlated with temperature + random walk
        self.state["pressure"] = 5 + 2 * math.sin(t / 120 + 0.5) + random.gauss(0, 0.1)

        # Flow rate: periodic variations
        self.state["flow_rate"] = 500 + 200 * math.sin(t / 80) + random.gauss(0, 5)

        # Level: slow drift
        self.state["level"] = 50 + 20 * math.sin(t / 200) + random.gauss(0, 1)

        # pH: small variations
        self.state["ph"] = 7.0 + 0.5 * math.sin(t / 150) + random.gauss(0, 0.1)

        # Conductivity: correlated with production
        self.state["conductivity"] = 1000 + 500 * math.sin(t / 180) + random.gauss(0, 20)

        # ENERGY TAGS
        # Power consumption: correlated with motor speed
        motor_load_factor = (self.state["motor_speed"] / 1500.0) ** 2
        self.state["power_consumption"] = 5000 * motor_load_factor + random.gauss(0, 100)

        # Current: correlated with power
        self.state["current"] = (self.state["power_consumption"] / 380.0 / math.sqrt(3) /
                                 self.state["power_factor"]) + random.gauss(0, 2)

        # Voltage: stable with small noise
        self.state["voltage"] = 380 + random.gauss(0, 2)

        # Power factor: slight variations
        self.state["power_factor"] = 0.85 + 0.05 * math.sin(t / 300) + random.gauss(0, 0.01)

        # Energy total: cumulative
        self.state["energy_total"] += self.state["power_consumption"] * self.update_interval / 3600.0

        # PRODUCTION TAGS
        # Production rate: step changes
        base_rate = 100 + 30 * math.sin(t / 400)
        self.state["production_rate"] = max(0, base_rate + random.gauss(0, 5))

        # Production count: cumulative
        self.state["production_count"] += int(self.state["production_rate"] * self.update_interval / 3600.0)

        # OEE: correlated with quality and performance
        availability = 0.95 if self.state["motor_running"] else 0.0
        self.state["oee"] = (availability *
                            self.state["quality_rate"] / 100 *
                            self.state["performance_rate"] / 100 * 100)

        # Quality rate: high with occasional dips
        if random.random() < 0.01:  # 1% chance of quality issue
            self.state["quality_rate"] = max(85, 98.5 + random.gauss(-5, 2))
        else:
            self.state["quality_rate"] = min(100, 98.5 + random.gauss(0, 0.5))

        # Performance rate: varies with speed
        self.state["performance_rate"] = min(100, 95 + 5 * math.sin(t / 250) + random.gauss(0, 1))

        # EQUIPMENT TAGS
        # Motor speed: follows production rate
        target_speed = 1500 + 500 * math.sin(t / 200)
        self.state["motor_speed"] = target_speed + random.gauss(0, 10)

        # Motor torque: correlated with power
        self.state["motor_torque"] = self.state["power_consumption"] / (self.state["motor_speed"] * 2 * math.pi / 60) * 1000

        # Bearing temperature: correlated with speed and time
        friction_heat = (self.state["motor_speed"] / 1500) * 10
        self.state["bearing_temp"] = 35 + friction_heat + random.gauss(0, 1)

        # Vibration: increases with speed, random spikes
        base_vib = (self.state["motor_speed"] / 1500) * 2
        self.state["vibration_x"] = base_vib + random.gauss(0, 0.2)
        self.state["vibration_y"] = base_vib * 0.9 + random.gauss(0, 0.2)
        self.state["vibration_z"] = base_vib * 0.7 + random.gauss(0, 0.15)

        # STATUS/ALARM TAGS
        # Motor running: mostly on, occasional stops
        if random.random() < 0.001:  # 0.1% chance to toggle
            self.state["motor_running"] = 1 - self.state["motor_running"]

        # Alarms based on conditions
        self.state["alarm_high_temp"] = 1 if self.state["temperature"] > 85 else 0
        self.state["alarm_high_pressure"] = 1 if self.state["pressure"] > 9 else 0

        # Emergency: very rare
        if random.random() < 0.0001:
            self.state["emergency_stop"] = 1
        elif self.iteration % 1000 == 0:
            self.state["emergency_stop"] = 0

    def write_to_modbus(self):
        """Write current state to Modbus registers"""
        # Write analog values to holding registers
        builder = BinaryPayloadBuilder(byteorder=Endianness.Big, wordorder=Endianness.Big)

        # Temperature (40001-40002)
        self.context[0].setValues(3, 40001, [int(self.state["temperature"] * 10)])

        # Pressure (40003-40004)
        self.context[0].setValues(3, 40003, [int(self.state["pressure"] * 100)])

        # Flow rate (40005-40006)
        self.context[0].setValues(3, 40005, [int(self.state["flow_rate"])])

        # Level (40007-40008)
        self.context[0].setValues(3, 40007, [int(self.state["level"] * 10)])

        # pH (40009-40010)
        self.context[0].setValues(3, 40009, [int(self.state["ph"] * 100)])

        # Conductivity (40011-40012)
        self.context[0].setValues(3, 40011, [int(self.state["conductivity"])])

        # Power (40013-40014)
        self.context[0].setValues(3, 40013, [int(self.state["power_consumption"])])

        # Current (40015-40016)
        self.context[0].setValues(3, 40015, [int(self.state["current"] * 10)])

        # Voltage (40017-40018)
        self.context[0].setValues(3, 40017, [int(self.state["voltage"])])

        # Power factor (40019-40020)
        self.context[0].setValues(3, 40019, [int(self.state["power_factor"] * 1000)])

        # Production rate (40021-40022)
        self.context[0].setValues(3, 40021, [int(self.state["production_rate"])])

        # Production count (40023-40024)
        self.context[0].setValues(3, 40023, [int(self.state["production_count"])])

        # OEE (40025-40026)
        self.context[0].setValues(3, 40025, [int(self.state["oee"] * 10)])

        # Quality rate (40027-40028)
        self.context[0].setValues(3, 40027, [int(self.state["quality_rate"] * 10)])

        # Motor speed (40029-40030)
        self.context[0].setValues(3, 40029, [int(self.state["motor_speed"])])

        # Bearing temp (40031-40032)
        self.context[0].setValues(3, 40031, [int(self.state["bearing_temp"] * 10)])

        # Vibration X (40033-40034)
        self.context[0].setValues(3, 40033, [int(self.state["vibration_x"] * 100)])

        # Vibration Y (40035-40036)
        self.context[0].setValues(3, 40035, [int(self.state["vibration_y"] * 100)])

        # Write digital values to coils
        self.context[0].setValues(1, 1, [bool(self.state["motor_running"])])
        self.context[0].setValues(1, 2, [bool(self.state["valve_open"])])
        self.context[0].setValues(1, 3, [bool(self.state["pump_running"])])
        self.context[0].setValues(1, 4, [bool(self.state["alarm_high_temp"])])
        self.context[0].setValues(1, 5, [bool(self.state["alarm_high_pressure"])])
        self.context[0].setValues(1, 6, [bool(self.state["emergency_stop"])])
        self.context[0].setValues(1, 7, [bool(self.state["maintenance_mode"])])
        self.context[0].setValues(1, 8, [bool(self.state["auto_mode"])])

    def update_loop(self):
        """Main update loop"""
        logger.info("🔄 Starting data update loop...")

        while self.running:
            self.update_process_values()
            self.write_to_modbus()

            # Log every 10 iterations
            if self.iteration % 10 == 0:
                logger.info(f"📊 Iteration {self.iteration}:")
                logger.info(f"   Temperature: {self.state['temperature']:.1f}°C")
                logger.info(f"   Pressure: {self.state['pressure']:.2f} bar")
                logger.info(f"   Flow: {self.state['flow_rate']:.0f} L/min")
                logger.info(f"   Power: {self.state['power_consumption']:.0f} kW")
                logger.info(f"   Production Rate: {self.state['production_rate']:.0f} units/h")
                logger.info(f"   OEE: {self.state['oee']:.1f}%")
                logger.info(f"   Motor: {'ON' if self.state['motor_running'] else 'OFF'}")

            self.iteration += 1
            time.sleep(self.update_interval)

    def start(self):
        """Start the simulator"""
        self.running = True

        # Start update thread
        update_thread = threading.Thread(target=self.update_loop, daemon=True)
        update_thread.start()

        # Setup Modbus server identity
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'OptiFlow AI'
        identity.ProductCode = 'INDUSTRIAL-SIM'
        identity.VendorUrl = 'https://optiflow-ai.com'
        identity.ProductName = 'Industrial Tags Simulator'
        identity.ModelName = 'ITS-1000'
        identity.MajorMinorRevision = '1.0.0'

        logger.info("=" * 80)
        logger.info("🏭 OptiFlow AI - Industrial Tags Simulator")
        logger.info("=" * 80)
        logger.info(f"📡 Modbus TCP Server: {self.host}:{self.port}")
        logger.info(f"⏱️  Update Interval: {self.update_interval}s")
        logger.info(f"🏷️  Total Tags: {len(self.tag_definitions)}")
        logger.info("")
        logger.info("📋 Tag Categories:")
        categories = {}
        for tag_name, tag_def in self.tag_definitions.items():
            cat = tag_def["category"]
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items()):
            logger.info(f"   • {cat}: {count} tags")
        logger.info("")
        logger.info("🎯 Compatible with: PI Vision, Power BI, Grafana, and OptiFlow AI dashboards")
        logger.info("=" * 80)

        # Start Modbus server
        try:
            StartTcpServer(self.context, identity=identity, address=(self.host, self.port))
        except KeyboardInterrupt:
            self.running = False
            logger.info("\n🛑 Simulator stopped by user")
        except Exception as e:
            self.running = False
            logger.error(f"❌ Server error: {e}")

    def print_tag_list(self):
        """Print complete tag list"""
        print("\n" + "=" * 100)
        print("📋 INDUSTRIAL TAGS LIST - OptiFlow AI Simulator")
        print("=" * 100)
        print(f"{'Tag Name':<25} {'Address':<10} {'Type':<10} {'Unit':<10} {'Category':<15} {'Description':<30}")
        print("-" * 100)

        for tag_name, tag_def in sorted(self.tag_definitions.items()):
            print(f"{tag_name:<25} {tag_def['address']:<10} {tag_def['type']:<10} "
                  f"{tag_def['unit']:<10} {tag_def['category']:<15} {tag_def['description']:<30}")

        print("=" * 100)
        print(f"Total: {len(self.tag_definitions)} tags")
        print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='OptiFlow AI - Industrial Tags Simulator (PI Vision/Power BI compatible)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start simulator on default port 5020
  python industrial_tags_simulator.py

  # Start on custom port
  python industrial_tags_simulator.py --port 5030

  # Faster updates (0.5 second interval)
  python industrial_tags_simulator.py --interval 0.5

  # List all available tags
  python industrial_tags_simulator.py --list-tags
        """
    )

    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host address to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5020,
                        help='Modbus TCP port (default: 5020)')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Update interval in seconds (default: 1.0)')
    parser.add_argument('--list-tags', action='store_true',
                        help='Print complete tag list and exit')

    args = parser.parse_args()

    simulator = IndustrialTagsSimulator(
        host=args.host,
        port=args.port,
        update_interval=args.interval
    )

    if args.list_tags:
        simulator.print_tag_list()
        return

    simulator.start()


if __name__ == '__main__':
    main()
