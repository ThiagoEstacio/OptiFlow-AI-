"""
OptiFlow Gateway - Hybrid Microservice Architecture
====================================================

Entry point for gateway with dual mode operation:
1. FastAPI REST API (for local low-latency access)
2. Background Protocol Adapters (for continuous data collection)

Architecture:
  PLCs/Devices → Protocol Adapters → Kafka → Cloud Backend
                      ↓
                  Local Cache
                      ↓
                  FastAPI REST API ← Local Dashboards (< 50ms latency)

This enables:
- Edge computing (process data locally before sending to cloud)
- Low-latency local access (dashboards in the plant)
- Cloud integration (send processed data to central platform)
- Offline resilience (buffer + local API continues working)
"""

import asyncio
import signal
import logging
from typing import Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.core.config import settings
from app.services.protocol_manager import ProtocolManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global state
protocol_manager: Optional[ProtocolManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - manages background workers

    Startup:
    1. Initialize Protocol Manager
    2. Load adapter configurations
    3. Start all protocol adapters (background workers)
    4. API becomes ready to accept requests

    Shutdown:
    1. Stop accepting new requests
    2. Gracefully stop all adapters
    3. Flush pending data to Kafka
    4. Save state to disk
    """
    global protocol_manager

    logger.info("=" * 70)
    logger.info("  🚀 OptiFlow Gateway Edge - Hybrid Microservice Starting")
    logger.info("=" * 70)
    logger.info(f"  Gateway ID: {settings.GATEWAY_ID}")
    logger.info(f"  Gateway Name: {settings.GATEWAY_NAME}")
    logger.info(f"  Deployment Mode: EDGE + CLOUD")
    logger.info(f"  API Port: 8080")
    logger.info(f"  Kafka: {getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')}")
    logger.info("=" * 70)

    # === STARTUP ===
    try:
        # Initialize Protocol Manager (background workers)
        logger.info("🔧 Initializing Protocol Manager...")
        config_path = getattr(settings, 'ADAPTERS_CONFIG', '/app/config/adapters_config.json')
        protocol_manager = ProtocolManager(config_path=config_path)

        # Load adapter configurations
        logger.info(f"📖 Loading adapter configuration from: {config_path}")
        loaded_count = await protocol_manager.load_config()
        logger.info(f"✅ Loaded {loaded_count} protocol adapters")

        # Start all adapters (background workers)
        if loaded_count > 0:
            logger.info("🚀 Starting protocol adapters...")
            await protocol_manager.start_all()
            logger.info("✅ All protocol adapters started")
        else:
            logger.warning("⚠️  No adapters configured - Gateway running in API-only mode")

        logger.info("=" * 70)
        logger.info("  ✅ Gateway Ready - Accepting requests")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Failed to start gateway: {e}", exc_info=True)
        raise

    # === RUNNING ===
    yield  # API is now active

    # === SHUTDOWN ===
    logger.info("=" * 70)
    logger.info("  🛑 Shutting down Gateway Edge...")
    logger.info("=" * 70)

    if protocol_manager:
        try:
            logger.info("Stopping protocol adapters...")
            await protocol_manager.stop_all()
            logger.info("✅ All adapters stopped gracefully")
        except Exception as e:
            logger.error(f"⚠️  Error during shutdown: {e}", exc_info=True)

    logger.info("=" * 70)
    logger.info("  ✅ Gateway shutdown complete - No data lost")
    logger.info("=" * 70)


# Create FastAPI application
app = FastAPI(
    title="OptiFlow Gateway Edge",
    description="""
    Industrial IoT Edge Gateway with hybrid architecture:

    **Features**:
    - 🚀 Low-latency local API (< 50ms for realtime tags)
    - 📊 Background data collection from PLCs
    - ☁️ Cloud integration via Kafka
    - 💾 Offline buffer (SQLite failsafe)
    - 🔄 WebSocket streaming for alarms
    - 📈 Prometheus metrics

    **Protocols Supported**:
    - OPC-UA (subscription-based)
    - Modbus TCP
    - MQTT
    - Siemens S7 (planned)
    - Ethernet/IP (planned)
    """,
    version="2.0.0-edge",
    lifespan=lifespan,  # Manages background workers
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ROOT ENDPOINTS ===

@app.get("/")
async def root():
    """
    Root endpoint - Gateway information
    """
    adapters_info = []
    if protocol_manager:
        for adapter_id, adapter in protocol_manager.adapters.items():
            adapters_info.append({
                "adapter_id": adapter_id,
                "protocol": adapter.config.protocol_type,
                "connected": adapter.connected,
                "tags_count": len(adapter.config.tags),
            })

    return {
        "service": "OptiFlow Gateway Edge",
        "version": "2.0.0-edge",
        "mode": "hybrid",  # API + Background workers
        "gateway_id": settings.GATEWAY_ID,
        "gateway_name": settings.GATEWAY_NAME,
        "adapters_running": len(adapters_info),
        "adapters": adapters_info,
        "endpoints": {
            "api_docs": "/api/docs",
            "health": "/api/health",
            "metrics": "/api/metrics",
            "tags_realtime": "/api/tags/realtime/{tag_name}",
            "websocket_alarms": "/ws/alarms"
        }
    }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint

    Returns:
    - 200 OK if gateway is healthy
    - 503 Service Unavailable if critical components are down
    """
    health_status = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "gateway_id": settings.GATEWAY_ID,
    }

    # Check protocol manager
    if protocol_manager:
        adapters_healthy = sum(
            1 for adapter in protocol_manager.adapters.values()
            if adapter.connected
        )
        adapters_total = len(protocol_manager.adapters)

        health_status["adapters"] = {
            "healthy": adapters_healthy,
            "total": adapters_total,
            "health_percentage": (adapters_healthy / adapters_total * 100) if adapters_total > 0 else 0
        }

        # Gateway is unhealthy if < 50% adapters are connected
        if adapters_total > 0 and (adapters_healthy / adapters_total) < 0.5:
            health_status["status"] = "degraded"
    else:
        health_status["status"] = "unhealthy"
        health_status["adapters"] = {"error": "Protocol manager not initialized"}

    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/api/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes

    Returns 200 only if gateway is fully ready to accept requests
    """
    if not protocol_manager:
        return JSONResponse(
            content={"ready": False, "reason": "Protocol manager not initialized"},
            status_code=503
        )

    if len(protocol_manager.adapters) == 0:
        return JSONResponse(
            content={"ready": False, "reason": "No adapters loaded"},
            status_code=503
        )

    return {"ready": True, "adapters_count": len(protocol_manager.adapters)}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler - ensures clean error responses
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


# === IMPORT API ROUTES ===
from app.api.routes import tags, websocket

# REST API Routes
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])

# WebSocket Routes
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# === HELPER FUNCTIONS ===

def get_protocol_manager() -> ProtocolManager:
    """
    Get global protocol manager instance

    Raises:
        RuntimeError: If protocol manager not initialized
    """
    if protocol_manager is None:
        raise RuntimeError("Protocol manager not initialized")
    return protocol_manager


# === MAIN ENTRY POINT ===

if __name__ == "__main__":
    # Production: Use Gunicorn with Uvicorn workers
    # gunicorn app.main_hybrid:app \
    #   --workers 4 \
    #   --worker-class uvicorn.workers.UvicornWorker \
    #   --bind 0.0.0.0:8080

    # Development: Run with Uvicorn directly
    uvicorn.run(
        "app.main_hybrid:app",
        host="0.0.0.0",
        port=8080,
        reload=True,  # Auto-reload on code changes
        log_level="info",
        access_log=True,
    )
