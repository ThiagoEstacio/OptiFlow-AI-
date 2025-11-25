"""
OPC-UA Server - Virtual PLC
============================

Servidor OPC-UA que expõe as tags do simulador para o Gateway conectar.
Simula um PLC real (Siemens, Allen-Bradley, etc.) com namespace industrial.

**Arquitetura**:
- Simulator → OPC-UA Server → Gateway → Kafka → Backend
- Gateway se comporta igual a produção (conecta via OPC-UA)
- Suporta autodiscovery (Browse) e leitura (Read)
- READ-ONLY por design (sem métodos Write/Call)

**Endpoints**:
- opc.tcp://0.0.0.0:4840 (padrão OPC-UA)

**Namespace**:
- ns=2 (industrial namespace)
- Estrutura: ns=2;s=SYSTEM/CORR01/TEMP_C_PV
"""

import logging
import asyncio
from typing import Optional
from asyncua import Server, ua
from asyncua.common.node import Node

from app.services.grain_terminal_simulator import get_simulator

logger = logging.getLogger(__name__)


class OPCUASimulatorServer:
    """
    OPC-UA Server que expõe tags do simulador

    O Gateway conecta neste server via Protocol Adapter OPC-UA
    """

    def __init__(self, endpoint: str = "opc.tcp://0.0.0.0:4840"):
        self.endpoint = endpoint
        self.server: Optional[Server] = None
        self.simulator = get_simulator()

        # Node references (para atualização rápida)
        self.tag_nodes = {}

        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Inicia OPC-UA server"""
        try:
            # Cria servidor
            self.server = Server()
            await self.server.init()

            # Configura endpoint
            self.server.set_endpoint(self.endpoint)

            # Server name
            self.server.set_server_name("OptiFlow Virtual PLC")

            # Security (None para desenvolvimento)
            self.server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                # ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt  # Produção
            ])

            # Namespace industrial (ns=2)
            namespace_idx = await self.server.register_namespace("http://optiflow.ai/virtual-plc")

            # Cria estrutura de folders (hierarquia industrial)
            root = self.server.nodes.objects
            plant_folder = await root.add_folder(namespace_idx, "GrainTerminal")

            # === SYSTEM FOLDER ===
            system_folder = await plant_folder.add_folder(namespace_idx, "SYSTEM")

            # System tags
            system_tags = {
                "SYSTEM_RUNNING_PV": ("RUNNING_PV", ua.VariantType.Boolean),
                "SYSTEM_TIME_S_PV": ("TIME_S_PV", ua.VariantType.Float),
                "TOTAL_MASS_T_PV": ("TOTAL_MASS_T_PV", ua.VariantType.Float),
                "TOTAL_KWH_PV": ("TOTAL_KWH_PV", ua.VariantType.Float),
                "WAREHOUSE_LEVEL_PCT_PV": ("WAREHOUSE_LEVEL_PCT_PV", ua.VariantType.Float),
                "TEST_COUNTER_PV": ("TEST_COUNTER_PV", ua.VariantType.Float),
            }

            for sim_tag, (opc_name, var_type) in system_tags.items():
                node = await system_folder.add_variable(
                    namespace_idx,
                    opc_name,
                    0.0 if var_type == ua.VariantType.Float else False
                )
                await node.set_writable(False)  # READ-ONLY
                self.tag_nodes[sim_tag] = node

            # === GATES FOLDER ===
            gates_folder = await plant_folder.add_folder(namespace_idx, "ARZ_GATES")

            for i in range(1, 8):  # Gates 01-07
                gate_folder = await gates_folder.add_folder(namespace_idx, f"GATE{i:02d}")

                # Posição
                pos_node = await gate_folder.add_variable(namespace_idx, "POSICAO_PV", 0.0)
                await pos_node.set_writable(False)
                self.tag_nodes[f'ARZ_GATES_GATE{i:02d}_POSICAO_PV'] = pos_node

                # Vazão
                flow_node = await gate_folder.add_variable(namespace_idx, "VAZAO_TPH_PV", 0.0)
                await flow_node.set_writable(False)
                self.tag_nodes[f'ARZ_GATES_GATE{i:02d}_VAZAO_TPH_PV'] = flow_node

            # === BELTS FOLDER ===
            for belt_name in ["CORR01", "CORR02", "CORR03"]:
                belt_folder = await plant_folder.add_folder(namespace_idx, belt_name)

                belt_tags = {
                    f"{belt_name}_RUNNING_PV": ("RUNNING_PV", ua.VariantType.Boolean),
                    f"{belt_name}_SPEED_MPS_PV": ("SPEED_MPS_PV", ua.VariantType.Float),
                    f"{belt_name}_FLOW_TPH_PV": ("FLOW_TPH_PV", ua.VariantType.Float),
                    f"{belt_name}_LOAD_PCT_PV": ("LOAD_PCT_PV", ua.VariantType.Float),
                    f"{belt_name}_POWER_KW_PV": ("POWER_KW_PV", ua.VariantType.Float),
                    f"{belt_name}_CURRENT_A_PV": ("CURRENT_A_PV", ua.VariantType.Float),
                    f"{belt_name}_TEMP_C_PV": ("TEMP_C_PV", ua.VariantType.Float),
                    f"{belt_name}_MISALIGNMENT_PV": ("MISALIGNMENT_PV", ua.VariantType.Float),
                }

                for sim_tag, (opc_name, var_type) in belt_tags.items():
                    node = await belt_folder.add_variable(
                        namespace_idx,
                        opc_name,
                        0.0 if var_type == ua.VariantType.Float else False
                    )
                    await node.set_writable(False)  # READ-ONLY
                    self.tag_nodes[sim_tag] = node

            # === SHIPLOADER FOLDER ===
            shiploader_folder = await plant_folder.add_folder(namespace_idx, "SLD01")

            shiploader_tags = {
                "SLD01_SETPOINT_TPH_PV": ("SETPOINT_TPH_PV", ua.VariantType.Float),
                "SLD01_FLOW_TPH_PV": ("FLOW_TPH_PV", ua.VariantType.Float),
                "SLD01_POWER_KW_PV": ("POWER_KW_PV", ua.VariantType.Float),
                "SLD01_CURRENT_A_PV": ("CURRENT_A_PV", ua.VariantType.Float),
            }

            for sim_tag, (opc_name, var_type) in shiploader_tags.items():
                node = await shiploader_folder.add_variable(namespace_idx, opc_name, 0.0)
                await node.set_writable(False)  # READ-ONLY
                self.tag_nodes[sim_tag] = node

            # Inicia servidor
            async with self.server:
                logger.info(f"✅ OPC-UA Server started at {self.endpoint}")
                logger.info(f"   Namespace: {namespace_idx}")
                logger.info(f"   Total tags: {len(self.tag_nodes)}")
                logger.info(f"   Security: None (development)")

                # Inicia task de atualização
                self._running = True
                self._update_task = asyncio.create_task(self._update_loop())

                # Mantém servidor rodando
                await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"❌ Error starting OPC-UA server: {e}", exc_info=True)
            raise

    async def stop(self):
        """Para OPC-UA server"""
        self._running = False

        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        if self.server:
            await self.server.stop()

        logger.info("🛑 OPC-UA Server stopped")

    async def _update_loop(self):
        """
        Loop que atualiza valores das tags no OPC-UA server

        Lê valores do simulador e atualiza nodes OPC-UA a cada 1s
        """
        logger.info("🔄 OPC-UA update loop started (1Hz)")

        try:
            while self._running:
                # Lê todas as tags do simulador
                tags_data = self.simulator.get_all_tags()

                # Atualiza nodes OPC-UA
                for tag_name, value in tags_data.items():
                    if tag_name in self.tag_nodes:
                        node = self.tag_nodes[tag_name]

                        # Converte para tipo correto
                        if tag_name.endswith("_RUNNING_PV"):
                            await node.write_value(bool(value))
                        else:
                            await node.write_value(float(value))

                # Aguarda 1 segundo
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("🔄 OPC-UA update loop cancelled")

        except Exception as e:
            logger.error(f"❌ Error in OPC-UA update loop: {e}", exc_info=True)

        finally:
            logger.info("🔄 OPC-UA update loop stopped")


# Singleton global
_opcua_server: Optional[OPCUASimulatorServer] = None


def get_opcua_server() -> OPCUASimulatorServer:
    """Retorna instância global do servidor OPC-UA"""
    global _opcua_server
    if _opcua_server is None:
        _opcua_server = OPCUASimulatorServer()
    return _opcua_server
