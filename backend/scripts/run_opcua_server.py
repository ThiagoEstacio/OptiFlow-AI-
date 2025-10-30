#!/usr/bin/env python3
"""
OptiFlow Grain Terminal OPC-UA Server
Standalone runner

Usage:
    python backend/scripts/run_opcua_server.py

Or with custom endpoint:
    python backend/scripts/run_opcua_server.py --endpoint opc.tcp://0.0.0.0:4841/optiflow/terminal
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.grain_terminal_simulator import GrainTerminalSimulator
from app.services.opcua_server import GrainTerminalOPCUAServer
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(endpoint: str):
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("  OptiFlow Grain Terminal OPC-UA Server")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  Terminal Exportador de Grãos - 1500 t/h")
    logger.info("  Real-time physics simulation with OPC-UA interface")
    logger.info("")
    logger.info(f"  Endpoint: {endpoint}")
    logger.info("=" * 70)
    logger.info("")

    # Create simulator
    logger.info("Creating simulator instance...")
    simulator = GrainTerminalSimulator()

    # Create OPC-UA server
    logger.info("Creating OPC-UA server...")
    opcua_server = GrainTerminalOPCUAServer(simulator, endpoint=endpoint)

    # Initialize
    logger.info("Initializing OPC-UA address space...")
    await opcua_server.init()

    # Print connection info
    logger.info("")
    logger.info("=" * 70)
    logger.info("  ✅ Server Ready")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  Connect with OPC-UA Client:")
    logger.info(f"    • Endpoint: {endpoint}")
    logger.info("    • Security: None (Anonymous)")
    logger.info("    • Namespace: http://optiflow.com/terminal")
    logger.info("")
    logger.info("  Recommended Clients:")
    logger.info("    • UAExpert (Unified Automation)")
    logger.info("    • Prosys OPC UA Browser")
    logger.info("    • Ignition (Inductive Automation)")
    logger.info("    • KEPServerEX")
    logger.info("")
    logger.info("  Available Tags:")
    logger.info("    • TEAG.ARZ.GATES.GATE01.POSICAO.PV")
    logger.info("    • TEAG.ARZ.CORR01.VAZAO.PV")
    logger.info("    • TEAG.ELV.ELV01.TEMP_MOTOR.PV")
    logger.info("    • TEAG.BAL.BAL01.PESO.PV")
    logger.info("    • TEAG.SLD.SLD01.VAZAO.PV")
    logger.info("    • TEAG.KPIs.ENERGIA_TOTAL.TOT")
    logger.info("    • ... and 100+ more")
    logger.info("")
    logger.info("  Writable Tags (Setpoints):")
    logger.info("    • TEAG.ARZ.GATES.GATExx.POSICAO.SP")
    logger.info("    • TEAG.SLD.SLD01.VAZAO.SP")
    logger.info("")
    logger.info("  Methods:")
    logger.info("    • TEAG.CONTROL.CMD_START()")
    logger.info("    • TEAG.CONTROL.CMD_STOP()")
    logger.info("    • TEAG.CONTROL.CMD_EMERGENCY_STOP()")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  Press Ctrl+C to stop")
    logger.info("")

    # Start server
    try:
        await opcua_server.start()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 70)
        logger.info("  Received stop signal")
        logger.info("=" * 70)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        logger.info("Stopping server...")
        await opcua_server.stop()
        logger.info("Server stopped. Goodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OptiFlow OPC-UA Server")
    parser.add_argument(
        "--endpoint",
        type=str,
        default="opc.tcp://0.0.0.0:4840/optiflow/terminal",
        help="OPC-UA endpoint URL"
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Update rate in Hz (default: 1.0)"
    )

    args = parser.parse_args()

    asyncio.run(main(args.endpoint))
