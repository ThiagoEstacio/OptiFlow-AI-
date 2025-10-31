"""
OPC-UA Server for Grain Terminal Simulator

Publishes all process variables, alarms, and accepts commands
following the TEAG.AREA.EQUIP.TAG.SUFIXO naming convention

Server URL: opc.tcp://localhost:4840/optiflow/terminal
Namespace: http://optiflow.com/terminal

Compatible with: UAExpert, Prosys OPC UA Browser, Ignition, etc.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from asyncua import Server, ua
from asyncua.common.methods import uamethod

from app.services.grain_terminal_simulator import GrainTerminalSimulator

logger = logging.getLogger(__name__)


class GrainTerminalOPCUAServer:
    """
    OPC-UA Server wrapping the Grain Terminal Simulator

    Structure:
    - Root
      ├── TEAG (Terminal Exportador de Grãos)
      │   ├── ARZ (Armazém)
      │   │   ├── GATES (Vazadores)
      │   │   │   ├── GATE01
      │   │   │   │   ├── POSICAO.PV (Double)
      │   │   │   │   ├── POSICAO.SP (Double)
      │   │   │   │   ├── VAZAO.PV (Double)
      │   │   │   │   └── CMD (Method)
      │   │   │   └── ...GATE10
      │   │   └── CORR01 (Correia 1)
      │   │       ├── RPM.PV
      │   │       ├── VAZAO.PV
      │   │       ├── CORRENTE.PV
      │   │       ├── POTENCIA.PV
      │   │       ├── TEMP_MANCAL.PV
      │   │       └── ...
      │   ├── ELV (Elevador)
      │   │   └── ELV01
      │   ├── BAL (Balança)
      │   │   └── BAL01
      │   └── SLD (Shiploader)
      │       └── SLD01
      └── KPIs
          ├── PRODUCAO_TOTAL
          ├── ENERGIA_TOTAL
          └── EFICIENCIA
    """

    def __init__(self, simulator: GrainTerminalSimulator, endpoint: str = "opc.tcp://0.0.0.0:4840/optiflow/terminal"):
        self.simulator = simulator
        self.server = Server()
        self.endpoint = endpoint

        # Node references (will be populated during setup)
        self.nodes: Dict[str, any] = {}

        # Update rate
        self.update_rate_hz = 1.0  # 1 Hz

        # Running flag
        self.running = False

    async def init(self):
        """Initialize the OPC-UA server"""
        await self.server.init()

        # Set endpoint
        self.server.set_endpoint(self.endpoint)

        # Set server info
        self.server.set_server_name("OptiFlow Grain Terminal Simulator")

        # Setup security (none for now - can add later)
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

        # Register namespace
        uri = "http://optiflow.com/terminal"
        self.idx = await self.server.register_namespace(uri)

        logger.info(f"OPC-UA Server initialized - Namespace index: {self.idx}")

        # Create address space
        await self._create_address_space()

        logger.info("Address space created successfully")

    async def _create_address_space(self):
        """Create the complete OPC-UA address space"""

        # Get objects node
        objects = self.server.get_objects_node()

        # Root: TEAG
        teag = await objects.add_object(self.idx, "TEAG")

        # System-level vars
        self.nodes['SYSTEM_RUNNING'] = await teag.add_variable(
            self.idx, "SYSTEM.RUNNING.PV", False
        )
        await self.nodes['SYSTEM_RUNNING'].set_writable()

        # WAREHOUSE
        self.nodes['WAREHOUSE_INVENTORY'] = await teag.add_variable(
            self.idx, "ARZ.INVENTARIO.PV", 0.0
        )
        self.nodes['WAREHOUSE_LEVEL'] = await teag.add_variable(
            self.idx, "ARZ.NIVEL.PV", 0.0
        )

        # ================================================================
        # GATES (Vazadores)
        # ================================================================
        arz = await teag.add_object(self.idx, "ARZ")

        gates_folder = await arz.add_object(self.idx, "GATES")

        for gate_id in range(1, 11):  # 10 gates
            gate_name = f"GATE{gate_id:02d}"
            gate_obj = await gates_folder.add_object(self.idx, gate_name)

            # Variables
            self.nodes[f'{gate_name}_POSITION_PV'] = await gate_obj.add_variable(
                self.idx, "POSICAO.PV", 0.0
            )
            self.nodes[f'{gate_name}_POSITION_SP'] = await gate_obj.add_variable(
                self.idx, "POSICAO.SP", 0.0
            )
            await self.nodes[f'{gate_name}_POSITION_SP'].set_writable()

            self.nodes[f'{gate_name}_FLOW_PV'] = await gate_obj.add_variable(
                self.idx, "VAZAO.PV", 0.0
            )

            self.nodes[f'{gate_name}_PLUGGED'] = await gate_obj.add_variable(
                self.idx, "ENTUPIDO.AL", False
            )

        # ================================================================
        # BELTS (Correias)
        # ================================================================
        for belt_id in ['CORR01', 'CORR02', 'CORR03']:
            belt_obj = await arz.add_object(self.idx, belt_id)

            self.nodes[f'{belt_id}_RUNNING'] = await belt_obj.add_variable(
                self.idx, "LIGADO.FB", False
            )

            self.nodes[f'{belt_id}_RPM'] = await belt_obj.add_variable(
                self.idx, "RPM.PV", 0.0
            )

            self.nodes[f'{belt_id}_SPEED'] = await belt_obj.add_variable(
                self.idx, "VELOCIDADE.PV", 0.0
            )

            self.nodes[f'{belt_id}_FLOW'] = await belt_obj.add_variable(
                self.idx, "VAZAO.PV", 0.0
            )

            self.nodes[f'{belt_id}_LOAD'] = await belt_obj.add_variable(
                self.idx, "CARGA.PV", 0.0
            )

            self.nodes[f'{belt_id}_CURRENT'] = await belt_obj.add_variable(
                self.idx, "CORRENTE.PV", 0.0
            )

            self.nodes[f'{belt_id}_POWER'] = await belt_obj.add_variable(
                self.idx, "POTENCIA.PV", 0.0
            )

            self.nodes[f'{belt_id}_TEMP_BEARING'] = await belt_obj.add_variable(
                self.idx, "TEMP_MANCAL.PV", 25.0
            )

            self.nodes[f'{belt_id}_TEMP_BELT'] = await belt_obj.add_variable(
                self.idx, "TEMP_CORREIA.PV", 25.0
            )

            self.nodes[f'{belt_id}_TEMP_DRUM'] = await belt_obj.add_variable(
                self.idx, "TEMP_TAMBOR.PV", 25.0
            )

            self.nodes[f'{belt_id}_UNDERSPEED_WARN'] = await belt_obj.add_variable(
                self.idx, "SUBVELOCIDADE.WARN", False
            )

            self.nodes[f'{belt_id}_UNDERSPEED_ALARM'] = await belt_obj.add_variable(
                self.idx, "SUBVELOCIDADE.AL", False
            )

        # ================================================================
        # ELEVATOR
        # ================================================================
        elv = await teag.add_object(self.idx, "ELV")

        elv01 = await elv.add_object(self.idx, "ELV01")

        self.nodes['ELV01_RUNNING'] = await elv01.add_variable(
            self.idx, "LIGADO.FB", False
        )

        self.nodes['ELV01_SPEED'] = await elv01.add_variable(
            self.idx, "VELOCIDADE.PV", 0.0
        )

        self.nodes['ELV01_FLOW'] = await elv01.add_variable(
            self.idx, "VAZAO.PV", 0.0
        )

        self.nodes['ELV01_CURRENT'] = await elv01.add_variable(
            self.idx, "CORRENTE.PV", 0.0
        )

        self.nodes['ELV01_POWER'] = await elv01.add_variable(
            self.idx, "POTENCIA.PV", 0.0
        )

        self.nodes['ELV01_TEMP_MOTOR'] = await elv01.add_variable(
            self.idx, "TEMP_MOTOR.PV", 25.0
        )

        self.nodes['ELV01_TEMP_GEARBOX'] = await elv01.add_variable(
            self.idx, "TEMP_REDUCAO.PV", 25.0
        )

        self.nodes['ELV01_SLIP'] = await elv01.add_variable(
            self.idx, "ESCORREGAMENTO.AL", False
        )

        self.nodes['ELV01_BELT_LOOSE'] = await elv01.add_variable(
            self.idx, "CORREIA_FROUXA.AL", False
        )

        # ================================================================
        # BALANCE (Balança)
        # ================================================================
        bal = await teag.add_object(self.idx, "BAL")

        bal01 = await bal.add_object(self.idx, "BAL01")

        self.nodes['BAL01_RUNNING'] = await bal01.add_variable(
            self.idx, "LIGADO.FB", False
        )

        self.nodes['BAL01_WEIGHT'] = await bal01.add_variable(
            self.idx, "PESO.PV", 0.0
        )

        self.nodes['BAL01_TARGET'] = await bal01.add_variable(
            self.idx, "PESO.SP", 1000.0
        )

        self.nodes['BAL01_CYCLES'] = await bal01.add_variable(
            self.idx, "CICLOS.TOT", 0
        )

        self.nodes['BAL01_TOTAL'] = await bal01.add_variable(
            self.idx, "TOTAL.TOT", 0.0
        )

        self.nodes['BAL01_FLOW'] = await bal01.add_variable(
            self.idx, "VAZAO.PV", 0.0
        )

        self.nodes['BAL01_STATE'] = await bal01.add_variable(
            self.idx, "ESTADO.PV", "idle"
        )

        # ================================================================
        # SHIPLOADER
        # ================================================================
        sld = await teag.add_object(self.idx, "SLD")

        sld01 = await sld.add_object(self.idx, "SLD01")

        self.nodes['SLD01_RUNNING'] = await sld01.add_variable(
            self.idx, "LIGADO.FB", False
        )

        self.nodes['SLD01_FLOW_SP'] = await sld01.add_variable(
            self.idx, "VAZAO.SP", 1500.0
        )
        await self.nodes['SLD01_FLOW_SP'].set_writable()

        self.nodes['SLD01_FLOW_PV'] = await sld01.add_variable(
            self.idx, "VAZAO.PV", 0.0
        )

        self.nodes['SLD01_POWER'] = await sld01.add_variable(
            self.idx, "POTENCIA.PV", 0.0
        )

        self.nodes['SLD01_DUST_LEVEL'] = await sld01.add_variable(
            self.idx, "POEIRA.PV", 0.0
        )

        # ================================================================
        # KPIs (at root level)
        # ================================================================
        kpis = await teag.add_object(self.idx, "KPIs")

        self.nodes['TOTAL_KWH'] = await kpis.add_variable(
            self.idx, "ENERGIA_TOTAL.TOT", 0.0
        )

        self.nodes['TOTAL_MASS'] = await kpis.add_variable(
            self.idx, "PRODUCAO_TOTAL.TOT", 0.0
        )

        self.nodes['KWH_PER_TON'] = await kpis.add_variable(
            self.idx, "EFICIENCIA_ENERGIA.PV", 0.0
        )

        self.nodes['COST'] = await kpis.add_variable(
            self.idx, "CUSTO_ENERGIA.TOT", 0.0
        )

        # ================================================================
        # CONTROL (Commands)
        # ================================================================
        control = await teag.add_object(self.idx, "CONTROL")

        # Command: Start System
        @uamethod
        def start_system(parent):
            logger.info("OPC-UA Command: START SYSTEM")
            self.simulator.start()
            return True

        await control.add_method(
            self.idx, "CMD_START", start_system, [], [ua.VariantType.Boolean]
        )

        # Command: Stop System
        @uamethod
        def stop_system(parent):
            logger.info("OPC-UA Command: STOP SYSTEM")
            self.simulator.stop()
            return True

        await control.add_method(
            self.idx, "CMD_STOP", stop_system, [], [ua.VariantType.Boolean]
        )

        # Command: Emergency Stop
        @uamethod
        def emergency_stop(parent):
            logger.info("OPC-UA Command: EMERGENCY STOP")
            self.simulator.emergency_stop_trigger()
            return True

        await control.add_method(
            self.idx, "CMD_EMERGENCY_STOP", emergency_stop, [], [ua.VariantType.Boolean]
        )

        logger.info(f"Created {len(self.nodes)} OPC-UA nodes")

    async def start(self):
        """Start the OPC-UA server and simulation loop"""
        logger.info(f"Starting OPC-UA Server at {self.endpoint}")

        async with self.server:
            logger.info("✅ OPC-UA Server is running")
            logger.info(f"   Endpoint: {self.endpoint}")
            logger.info(f"   Namespace: {self.idx}")
            logger.info(f"   Nodes: {len(self.nodes)}")
            logger.info("   Connect with UAExpert or any OPC-UA client")

            self.running = True

            # Start simulation
            self.simulator.start()
            logger.info("🚀 Simulator started")

            # Main loop
            while self.running:
                try:
                    # Step simulation
                    self.simulator.step()

                    # Update OPC-UA nodes
                    await self._update_nodes()

                    # Sleep for update rate
                    await asyncio.sleep(1.0 / self.update_rate_hz)

                except Exception as e:
                    logger.error(f"Error in simulation loop: {e}", exc_info=True)
                    await asyncio.sleep(1.0)

    async def stop(self):
        """Stop the server"""
        logger.info("Stopping OPC-UA Server...")
        self.running = False
        self.simulator.stop()
        await self.server.stop()

    async def _update_nodes(self):
        """Update all OPC-UA node values from simulator"""
        try:
            # System
            await self.nodes['SYSTEM_RUNNING'].write_value(self.simulator.running)
            await self.nodes['WAREHOUSE_INVENTORY'].write_value(self.simulator.warehouse_inventory_t)
            await self.nodes['WAREHOUSE_LEVEL'].write_value(self.simulator.warehouse_level_pct)

            # Gates
            for gate in self.simulator.gates:
                gate_name = f'GATE{gate.id:02d}'
                await self.nodes[f'{gate_name}_POSITION_PV'].write_value(gate.position_fb)
                await self.nodes[f'{gate_name}_FLOW_PV'].write_value(gate.flow_tph)
                await self.nodes[f'{gate_name}_PLUGGED'].write_value(gate.plugged)

                # Read SP from OPC-UA (if client wrote to it)
                sp_value = await self.nodes[f'{gate_name}_POSITION_SP'].read_value()
                if sp_value != gate.open_pct_sp:
                    self.simulator.set_gate_manual(gate.id, sp_value)

            # Belts
            for belt_id, belt in self.simulator.belts.items():
                await self.nodes[f'{belt_id}_RUNNING'].write_value(belt.running)
                await self.nodes[f'{belt_id}_RPM'].write_value(belt.rpm)
                await self.nodes[f'{belt_id}_SPEED'].write_value(belt.speed_mps)
                await self.nodes[f'{belt_id}_FLOW'].write_value(belt.flow_tph)
                await self.nodes[f'{belt_id}_LOAD'].write_value(belt.load_pct)
                await self.nodes[f'{belt_id}_CURRENT'].write_value(belt.current_A)
                await self.nodes[f'{belt_id}_POWER'].write_value(belt.power_kW)
                await self.nodes[f'{belt_id}_TEMP_BEARING'].write_value(belt.temp_bearing_C)
                await self.nodes[f'{belt_id}_TEMP_BELT'].write_value(belt.temp_belt_C)
                await self.nodes[f'{belt_id}_TEMP_DRUM'].write_value(belt.temp_drum_C)
                await self.nodes[f'{belt_id}_UNDERSPEED_WARN'].write_value(belt.underspeed_warn)
                await self.nodes[f'{belt_id}_UNDERSPEED_ALARM'].write_value(belt.underspeed_alarm)

            # Elevator
            await self.nodes['ELV01_RUNNING'].write_value(self.simulator.elevator.running)
            await self.nodes['ELV01_SPEED'].write_value(self.simulator.elevator.speed_mps)
            await self.nodes['ELV01_FLOW'].write_value(self.simulator.elevator.flow_tph)
            await self.nodes['ELV01_CURRENT'].write_value(self.simulator.elevator.current_A)
            await self.nodes['ELV01_POWER'].write_value(self.simulator.elevator.power_kW)
            await self.nodes['ELV01_TEMP_MOTOR'].write_value(self.simulator.elevator.temp_motor_C)
            await self.nodes['ELV01_TEMP_GEARBOX'].write_value(self.simulator.elevator.temp_gearbox_C)
            await self.nodes['ELV01_SLIP'].write_value(self.simulator.elevator.slip)
            await self.nodes['ELV01_BELT_LOOSE'].write_value(self.simulator.elevator.belt_loose)

            # Balance
            await self.nodes['BAL01_RUNNING'].write_value(self.simulator.balance.running)
            await self.nodes['BAL01_WEIGHT'].write_value(self.simulator.balance.weight_kg)
            await self.nodes['BAL01_TARGET'].write_value(self.simulator.balance.target_kg)
            await self.nodes['BAL01_CYCLES'].write_value(self.simulator.balance.cycle_count)
            await self.nodes['BAL01_TOTAL'].write_value(self.simulator.balance.total_mass_t)
            await self.nodes['BAL01_FLOW'].write_value(self.simulator.balance.avg_flow_tph)
            await self.nodes['BAL01_STATE'].write_value(self.simulator.balance.cycle_state.value)

            # Shiploader
            await self.nodes['SLD01_RUNNING'].write_value(self.simulator.shiploader.running)
            await self.nodes['SLD01_FLOW_PV'].write_value(self.simulator.shiploader.flow_pv_tph)
            await self.nodes['SLD01_POWER'].write_value(self.simulator.shiploader.power_kW)
            await self.nodes['SLD01_DUST_LEVEL'].write_value(self.simulator.shiploader.dust_level)

            # Read SP from OPC-UA
            sld_sp = await self.nodes['SLD01_FLOW_SP'].read_value()
            if sld_sp != self.simulator.shiploader.flow_sp_tph:
                self.simulator.set_shiploader_setpoint(sld_sp)

            # KPIs
            await self.nodes['TOTAL_KWH'].write_value(self.simulator.total_kWh)
            await self.nodes['TOTAL_MASS'].write_value(self.simulator.total_mass_t)
            await self.nodes['KWH_PER_TON'].write_value(self.simulator.kWh_per_ton)
            await self.nodes['COST'].write_value(self.simulator.cost_BRL)

        except Exception as e:
            logger.error(f"Error updating nodes: {e}")


# ============================================================================
# STANDALONE RUNNER
# ============================================================================

async def main():
    """Main entry point for standalone server"""
    logging.basicConfig(level=logging.INFO)

    # Create simulator
    simulator = GrainTerminalSimulator()

    # Create OPC-UA server
    opcua_server = GrainTerminalOPCUAServer(simulator)

    # Initialize
    await opcua_server.init()

    # Start
    try:
        await opcua_server.start()
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    finally:
        await opcua_server.stop()


if __name__ == "__main__":
    asyncio.run(main())
