"""
OptiFlow Gateway - Data Collection Service
"""
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main gateway loop
    """
    logger.info("🚀 Starting OptiFlow Gateway...")

    # Create health check file
    health_file = Path("/app/data/gateway.health")
    health_file.parent.mkdir(parents=True, exist_ok=True)
    health_file.touch()

    logger.info("✅ Gateway initialized successfully")
    logger.info("📡 Waiting for device configurations...")

    # Keep the gateway running
    while True:
        await asyncio.sleep(10)
        logger.debug("Gateway heartbeat...")


if __name__ == "__main__":
    asyncio.run(main())
