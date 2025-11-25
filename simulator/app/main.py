"""
OptiFlow Simulator - Main Entry Point
======================================

Microserviço simulador que combina:
1. OPC-UA Server (porta 4840) - Gateway conecta aqui
2. REST API (porta 4850) - Controle do simulador

**Arquitetura**:
```
Simulator Microservice
├── OPC-UA Server (4840)
│   └── Expõe tags do PLC virtual
│       └── Gateway conecta e lê tags
│           └── Gateway publica no Kafka
│               └── Backend consome
│
└── REST API (4850)
    └── Controle da simulação
        ├── /start, /stop, /reset
        ├── /status
        └── /gates/*/setpoint
```

**Deployment**:
- Standalone: python app/main.py
- Docker: docker run -p 4840:4840 -p 4850:4850 optiflow-simulator
- Compose: docker-compose up simulator
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.opcua_server import get_opcua_server
from app.api.routes import simulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global OPC-UA server task
_opcua_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager

    STARTUP:
    - Inicia OPC-UA server em background (porta 4840)

    SHUTDOWN:
    - Para OPC-UA server gracefully
    """
    global _opcua_task

    # === STARTUP ===
    logger.info("🚀 Starting OptiFlow Simulator...")

    # Inicia OPC-UA server em background
    opcua_server = get_opcua_server()
    _opcua_task = asyncio.create_task(opcua_server.start())

    # Aguarda um pouco para server inicializar
    await asyncio.sleep(2.0)

    logger.info("✅ Simulator ready!")
    logger.info("   - OPC-UA Server: opc.tcp://0.0.0.0:4840")
    logger.info("   - REST API: http://0.0.0.0:4850")
    logger.info("   - Gateway should connect to: opc.tcp://simulator:4840")

    yield  # API está ativa

    # === SHUTDOWN ===
    logger.info("🛑 Stopping OptiFlow Simulator...")

    # Para OPC-UA server
    if _opcua_task and not _opcua_task.done():
        _opcua_task.cancel()
        try:
            await _opcua_task
        except asyncio.CancelledError:
            pass

    await opcua_server.stop()

    logger.info("✅ Simulator stopped gracefully")


# === FASTAPI APP ===

app = FastAPI(
    title="OptiFlow Simulator",
    description="Virtual PLC Simulator for OptiFlow Platform (Grain Terminal)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS (permitir acesso do frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restringir em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(simulator.router)


# === ROOT ENDPOINTS ===

@app.get("/")
async def root():
    """
    Root endpoint - Informações do simulador
    """
    from app.services.grain_terminal_simulator import get_simulator

    sim = get_simulator()

    return {
        "service": "OptiFlow Simulator",
        "version": "1.0.0",
        "type": "Virtual PLC (Grain Terminal)",
        "status": "running",
        "simulator": {
            "running": sim.running,
            "time_s": sim.time_s,
            "tags_count": len(sim.get_all_tags())
        },
        "endpoints": {
            "opcua": "opc.tcp://0.0.0.0:4840",
            "rest_api": "http://0.0.0.0:4850",
            "docs": "http://0.0.0.0:4850/docs",
            "simulator_control": {
                "start": "POST /simulator/start",
                "stop": "POST /simulator/stop",
                "reset": "POST /simulator/reset",
                "status": "GET /simulator/status",
                "tags": "GET /simulator/tags"
            }
        },
        "gateway_config": {
            "adapter_type": "opcua",
            "host": "simulator",  # Docker service name
            "port": 4840,
            "endpoint": "opc.tcp://simulator:4840",
            "security_mode": "None",
            "namespace": 2,
            "tags_example": "ns=2;s=CORR01/TEMP_C_PV"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint (Kubernetes liveness probe)
    """
    from app.services.grain_terminal_simulator import get_simulator

    sim = get_simulator()

    return {
        "status": "healthy",
        "simulator_running": sim.running,
        "opcua_server": "running"  # Assume running se não crashou
    }


# === MAIN ENTRY POINT ===

if __name__ == "__main__":
    # Production: Use Gunicorn with Uvicorn workers
    # gunicorn app.main:app \
    #   --workers 1 \
    #   --worker-class uvicorn.workers.UvicornWorker \
    #   --bind 0.0.0.0:4850

    # Development: Run with Uvicorn directly
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=4850,
        reload=True,  # Auto-reload on code changes
        log_level="info",
        access_log=True,
    )
