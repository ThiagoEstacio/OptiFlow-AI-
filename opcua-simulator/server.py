#!/usr/bin/env python3
"""
OptiFlow OPC UA Simulator - Grain Terminal
Simulates a complete grain terminal with conveyors, silos, elevators and energy monitoring
Behaves exactly like a real industrial OPC UA server
"""

import asyncio
import logging
import sys
import time
import random
import math
from datetime import datetime
from asyncua import Server, ua
from asyncua.common.methods import uamethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GrainTerminalSimulator:
    """Simulates a grain terminal with realistic dynamic behavior"""
    
    def __init__(self):
        self.start_time = time.time()
        self.running = True
        
        # Equipment state
        self.conveyors = {}
        self.silos = {}
        self.elevators = {}
        self.energy = {}
        
    def initialize_equipment(self):
        """Initialize equipment with default values"""
        # 3 Conveyors (CORR01-03)
        for i in range(1, 4):
            name = f"CORR{i:02d}"
            self.conveyors[name] = {
                "running": True,
                "speed_mps": 2.5 + random.uniform(-0.2, 0.2),
                "load_pct": random.uniform(50, 80),
                "current_a": random.uniform(30, 50),
                "power_kw": random.uniform(35, 55),
                "temp_c": random.uniform(35, 45),
                "vibration_mms": random.uniform(1.5, 3.5),
                "misalignment": random.uniform(0, 2),
            }
        
        # 3 Silos (SILO01-03)
        for i in range(1, 4):
            name = f"SILO{i:02d}"
            self.silos[name] = {
                "level_pct": random.uniform(40, 90),
                "temp_grain_c": random.uniform(15, 25),
                "humidity_pct": random.uniform(12, 16),
                "weight_t": random.uniform(500, 2000),
                "pressure_pa": random.uniform(100, 500),
            }
        
        # 2 Elevators (ELEV01-02)
        for i in range(1, 3):
            name = f"ELEV{i:02d}"
            self.elevators[name] = {
                "running": True,
                "bucket_speed_mps": 1.5 + random.uniform(-0.1, 0.1),
                "current_a": random.uniform(20.0, 35.0),
                "power_kw": random.uniform(25.0, 40.0),
                "temp_c": random.uniform(40.0, 50.0),
            }
        
        # Energy monitoring
        self.energy = {
            "grid_power_kw": 150.0,  # Will be calculated
            "total_energy_kwh": 1250.5,
            "power_factor": random.uniform(0.85, 0.95),
            "grid_voltage_v": 380.0 + random.uniform(-5, 5),
        }
    
    def update_simulation(self):
        """Update all equipment values with realistic dynamics"""
        elapsed = time.time() - self.start_time
        
        # Update conveyors with sine wave variations
        for name, conv in self.conveyors.items():
            if conv["running"]:
                # Speed varies slightly
                conv["speed_mps"] += random.uniform(-0.05, 0.05)
                conv["speed_mps"] = max(2.0, min(3.0, conv["speed_mps"]))
                
                # Load varies with sine wave (material flow)
                base_load = 65 + 15 * math.sin(elapsed * 0.1)
                conv["load_pct"] = base_load + random.uniform(-5, 5)
                conv["load_pct"] = max(0, min(100, conv["load_pct"]))
                
                # Current proportional to load
                conv["current_a"] = 30 + (conv["load_pct"] / 100) * 25 + random.uniform(-2, 2)
                
                # Power proportional to current
                conv["power_kw"] = conv["current_a"] * 0.95 + random.uniform(-1, 1)
                
                # Temperature increases with load
                target_temp = 35 + (conv["load_pct"] / 100) * 15
                conv["temp_c"] += (target_temp - conv["temp_c"]) * 0.1
                conv["temp_c"] += random.uniform(-0.5, 0.5)
                
                # Vibration increases with speed
                conv["vibration_mms"] = 2.0 + (conv["speed_mps"] / 3.0) * 2.0 + random.uniform(-0.3, 0.3)
                
                # Misalignment slowly drifts
                conv["misalignment"] += random.uniform(-0.1, 0.1)
                conv["misalignment"] = max(0, min(5, conv["misalignment"]))
            else:
                # Equipment stopped
                conv["speed_mps"] = 0
                conv["load_pct"] = 0
                conv["current_a"] = 0
                conv["power_kw"] = 0
                conv["temp_c"] -= 0.5  # Cooling down
                conv["temp_c"] = max(25, conv["temp_c"])
        
        # Update silos (level changes slowly)
        for name, silo in self.silos.items():
            # Level changes slowly (filling/emptying)
            silo["level_pct"] += random.uniform(-0.5, 0.5)
            silo["level_pct"] = max(10, min(95, silo["level_pct"]))
            
            # Weight proportional to level
            silo["weight_t"] = (silo["level_pct"] / 100) * 2500 + random.uniform(-10, 10)
            
            # Temperature varies with ambient
            silo["temp_grain_c"] += random.uniform(-0.2, 0.2)
            silo["temp_grain_c"] = max(10, min(30, silo["temp_grain_c"]))
            
            # Humidity stable
            silo["humidity_pct"] += random.uniform(-0.1, 0.1)
            silo["humidity_pct"] = max(11, min(17, silo["humidity_pct"]))
            
            # Pressure proportional to level
            silo["pressure_pa"] = 100 + (silo["level_pct"] / 100) * 400 + random.uniform(-10, 10)
        
        # Update elevators
        for name, elev in self.elevators.items():
            if elev["running"]:
                elev["bucket_speed_mps"] += random.uniform(-0.02, 0.02)
                elev["bucket_speed_mps"] = max(1.2, min(1.8, elev["bucket_speed_mps"]))
                
                elev["current_a"] = 25 + random.uniform(-3, 3)
                elev["power_kw"] = elev["current_a"] * 1.05 + random.uniform(-1, 1)
                
                elev["temp_c"] += random.uniform(-0.5, 0.5)
                elev["temp_c"] = max(40, min(60, elev["temp_c"]))
        
        # Calculate total energy consumption
        total_power = 0
        for conv in self.conveyors.values():
            total_power += conv["power_kw"]
        for elev in self.elevators.values():
            total_power += elev["power_kw"]
        
        self.energy["grid_power_kw"] = total_power + random.uniform(-2, 2)
        self.energy["total_energy_kwh"] += (self.energy["grid_power_kw"] / 3600)  # kWh increment
        self.energy["power_factor"] += random.uniform(-0.01, 0.01)
        self.energy["power_factor"] = max(0.80, min(0.98, self.energy["power_factor"]))
        self.energy["grid_voltage_v"] += random.uniform(-1, 1)
        self.energy["grid_voltage_v"] = max(370, min(390, self.energy["grid_voltage_v"]))


async def main():
    """Main OPC UA server"""
    logger.info("=" * 60)
    logger.info("  🚀 OptiFlow OPC UA Simulator - Grain Terminal")
    logger.info("=" * 60)
    
    # Create simulator
    simulator = GrainTerminalSimulator()
    simulator.initialize_equipment()
    
    # Create OPC UA server
    server = Server()
    await server.init()
    
    # Configure server
    server.set_endpoint("opc.tcp://0.0.0.0:4840/optiflow/terminal")
    server.set_server_name("OptiFlow Grain Terminal Simulator")
    
    # Set security policy (None for development)
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    
    # Setup namespace
    uri = "http://optiflow.ai/grain-terminal"
    idx = await server.register_namespace(uri)
    
    logger.info(f"  Namespace: {uri}")
    logger.info(f"  Namespace Index: {idx}")
    logger.info(f"  Endpoint: opc.tcp://0.0.0.0:4840/optiflow/terminal")
    logger.info("=" * 60)
    
    # Get Objects node
    objects = server.nodes.objects
    
    # Create root folder
    terminal = await objects.add_folder(idx, "GrainTerminal")
    
    # Create equipment folders
    conveyors_folder = await terminal.add_folder(idx, "Conveyors")
    silos_folder = await terminal.add_folder(idx, "Silos")
    elevators_folder = await terminal.add_folder(idx, "Elevators")
    energy_folder = await terminal.add_folder(idx, "Energy")
    
    # Create conveyor nodes with consistent naming: CORR01_VARIABLE_PV
    conveyor_nodes = {}
    for name, data in simulator.conveyors.items():
        conv_folder = await conveyors_folder.add_folder(idx, name)
        conveyor_nodes[name] = {
            "running": await conv_folder.add_variable(idx, "running", data["running"]),
            "speed_mps": await conv_folder.add_variable(idx, "speed_mps", data["speed_mps"]),
            "load_pct": await conv_folder.add_variable(idx, "load_pct", data["load_pct"]),
            "current_a": await conv_folder.add_variable(idx, "current_a", data["current_a"]),
            "power_kw": await conv_folder.add_variable(idx, "power_kw", data["power_kw"]),
            "temp_c": await conv_folder.add_variable(idx, "temp_c", data["temp_c"]),
            "vibration_mms": await conv_folder.add_variable(idx, "vibration_mms", data["vibration_mms"]),
            "misalignment": await conv_folder.add_variable(idx, "misalignment", data["misalignment"]),
        }
        # Make writable
        for var in conveyor_nodes[name].values():
            await var.set_writable()
    
    # Create silo nodes with consistent naming: SILO01_VARIABLE_PV
    silo_nodes = {}
    for name, data in simulator.silos.items():
        silo_folder = await silos_folder.add_folder(idx, name)
        silo_nodes[name] = {
            "level_pct": await silo_folder.add_variable(idx, "level_pct", data["level_pct"]),
            "temp_grain_c": await silo_folder.add_variable(idx, "temp_grain_c", data["temp_grain_c"]),
            "humidity_pct": await silo_folder.add_variable(idx, "humidity_pct", data["humidity_pct"]),
            "weight_t": await silo_folder.add_variable(idx, "weight_t", data["weight_t"]),
            "pressure_pa": await silo_folder.add_variable(idx, "pressure_pa", data["pressure_pa"]),
        }
        for var in silo_nodes[name].values():
            await var.set_writable()
    
    # Create elevator nodes
    elevator_nodes = {}
    for name, data in simulator.elevators.items():
        elev_folder = await elevators_folder.add_folder(idx, name)
        elevator_nodes[name] = {
            "running": await elev_folder.add_variable(idx, "running", data["running"]),
            "bucket_speed_mps": await elev_folder.add_variable(idx, "bucket_speed_mps", data["bucket_speed_mps"]),
            "current_a": await elev_folder.add_variable(idx, "current_a", data["current_a"]),
            "power_kw": await elev_folder.add_variable(idx, "power_kw", data["power_kw"]),
            "temp_c": await elev_folder.add_variable(idx, "temp_c", data["temp_c"]),
        }
        for var in elevator_nodes[name].values():
            await var.set_writable()
    
    # Create energy nodes - use "Energy" as equipment name in gateway
    grid_power_var = await energy_folder.add_variable(idx, "grid_power_kw", 0.0)
    await grid_power_var.set_writable()
    await grid_power_var.write_value(float(simulator.energy["grid_power_kw"]), varianttype=ua.VariantType.Double)
    
    total_energy_var = await energy_folder.add_variable(idx, "total_energy_kwh", 0.0)
    await total_energy_var.set_writable()
    await total_energy_var.write_value(float(simulator.energy["total_energy_kwh"]), varianttype=ua.VariantType.Double)
    
    power_factor_var = await energy_folder.add_variable(idx, "power_factor", 0.0)
    await power_factor_var.set_writable()
    await power_factor_var.write_value(float(simulator.energy["power_factor"]), varianttype=ua.VariantType.Double)
    
    grid_voltage_var = await energy_folder.add_variable(idx, "grid_voltage_v", 0.0)
    await grid_voltage_var.set_writable()
    await grid_voltage_var.write_value(float(simulator.energy["grid_voltage_v"]), varianttype=ua.VariantType.Double)
    
    energy_nodes = {
        "grid_power_kw": grid_power_var,
        "total_energy_kwh": total_energy_var,
        "power_factor": power_factor_var,
        "grid_voltage_v": grid_voltage_var,
    }
    
    logger.info("\n📊 Equipment Summary:")
    logger.info(f"  Conveyors: {len(simulator.conveyors)}")
    logger.info(f"  Silos: {len(simulator.silos)}")
    logger.info(f"  Elevators: {len(simulator.elevators)}")
    logger.info(f"  Total Tags: {len(conveyor_nodes) * 8 + len(silo_nodes) * 5 + len(elevator_nodes) * 5 + 4}")
    
    # Start server
    async with server:
        logger.info("\n" + "=" * 60)
        logger.info("  ✅ OPC UA Server Started Successfully")
        logger.info("  📡 Clients can connect to:")
        logger.info("     opc.tcp://opcua-server:4840/optiflow/terminal")
        logger.info("  Press Ctrl+C to stop")
        logger.info("=" * 60 + "\n")
        
        # Main simulation loop
        update_count = 0
        while True:
            try:
                # Update simulation
                simulator.update_simulation()
                
                # Update OPC UA nodes - Conveyors
                for name, data in simulator.conveyors.items():
                    await conveyor_nodes[name]["running"].write_value(data["running"])
                    await conveyor_nodes[name]["speed_mps"].write_value(data["speed_mps"])
                    await conveyor_nodes[name]["load_pct"].write_value(data["load_pct"])
                    await conveyor_nodes[name]["current_a"].write_value(data["current_a"])
                    await conveyor_nodes[name]["power_kw"].write_value(data["power_kw"])
                    await conveyor_nodes[name]["temp_c"].write_value(data["temp_c"])
                    await conveyor_nodes[name]["vibration_mms"].write_value(data["vibration_mms"])
                    await conveyor_nodes[name]["misalignment"].write_value(data["misalignment"])
                
                # Update silos
                for name, data in simulator.silos.items():
                    await silo_nodes[name]["level_pct"].write_value(data["level_pct"])
                    await silo_nodes[name]["temp_grain_c"].write_value(data["temp_grain_c"])
                    await silo_nodes[name]["humidity_pct"].write_value(data["humidity_pct"])
                    await silo_nodes[name]["weight_t"].write_value(data["weight_t"])
                    await silo_nodes[name]["pressure_pa"].write_value(data["pressure_pa"])
                
                # Update elevators
                for name, data in simulator.elevators.items():
                    await elevator_nodes[name]["running"].write_value(data["running"])
                    await elevator_nodes[name]["bucket_speed_mps"].write_value(data["bucket_speed_mps"])
                    await elevator_nodes[name]["current_a"].write_value(data["current_a"])
                    await elevator_nodes[name]["power_kw"].write_value(data["power_kw"])
                    await elevator_nodes[name]["temp_c"].write_value(data["temp_c"])
                
                # Update energy
                await energy_nodes["grid_power_kw"].write_value(float(simulator.energy["grid_power_kw"]), varianttype=ua.VariantType.Double)
                await energy_nodes["total_energy_kwh"].write_value(float(simulator.energy["total_energy_kwh"]), varianttype=ua.VariantType.Double)
                await energy_nodes["power_factor"].write_value(float(simulator.energy["power_factor"]), varianttype=ua.VariantType.Double)
                await energy_nodes["grid_voltage_v"].write_value(float(simulator.energy["grid_voltage_v"]), varianttype=ua.VariantType.Double)
                
                update_count += 1
                if update_count % 10 == 0:
                    logger.info(f"📊 Update #{update_count} | Power: {simulator.energy['grid_power_kw']:.1f} kW | Energy: {simulator.energy['total_energy_kwh']:.1f} kWh")
                
                await asyncio.sleep(1)  # Update every second
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Shutting down server...")
                break
            except Exception as e:
                logger.error(f"❌ Error in simulation loop: {e}", exc_info=True)
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
