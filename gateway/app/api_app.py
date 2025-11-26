"""
Gateway HTTP API - For configuration and tag browsing
Similar to KEPServerEX admin interface
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from app.core.logger import logger

# Optional imports
try:
    from app.services.opcua_browser import OPCUABrowser
except ImportError:
    OPCUABrowser = None

try:
    from app.services.gateway_metrics import get_gateway_metrics, init_gateway_metrics
except ImportError:
    get_gateway_metrics = None
    init_gateway_metrics = None

try:
    from app.api.routes import adapters
except ImportError:
    adapters = None  # Adapters routes optional

try:
    from app.api.routes import tags_realtime
except ImportError:
    tags_realtime = None  # Realtime tags routes optional

try:
    from app.api.routes import formulas
except ImportError:
    formulas = None  # Formula engine routes optional

try:
    from app.api.routes import websocket
except ImportError:
    websocket = None  # WebSocket routes optional

try:
    from app.api.routes import security
except ImportError:
    security = None  # Security routes optional

try:
    from app.api.routes import config_sync
except ImportError:
    config_sync = None  # Config sync routes optional

try:
    from app.api.routes import alarms as alarms_routes
except ImportError:
    alarms_routes = None  # Alarm routes optional

# DEPRECATED - Moved to Backend:
# - tags_advanced (Tag CRUD) -> Backend: /api/v1/tags
# - tags_automation (Alarms, Events, Actions) -> Backend: /api/v1/alarms, /api/v1/events


# Pydantic models
class BrowseRequest(BaseModel):
    """Request to browse OPC-UA server"""
    endpoint: str
    namespace_index: Optional[int] = None
    tag_filter: Optional[str] = None


class DiscoverTagsResponse(BaseModel):
    """Response for tag discovery"""
    success: bool
    endpoint: str
    namespaces: List[Dict[str, Any]]
    tags: List[Dict[str, Any]]
    tag_count: int
    error: Optional[str] = None


class SearchTagsRequest(BaseModel):
    """Request to search tags"""
    endpoint: str
    search_term: str
    namespace_index: Optional[int] = None


# Create FastAPI app
app = FastAPI(
    title="OptiFlow Gateway API",
    description="Configuration and tag browsing API for OptiFlow Gateway",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
if adapters:
    app.include_router(adapters.router, prefix="/api/adapters", tags=["adapters"])

# Include tag routers
# - tags_realtime: For realtime value reads, list, search (used by operational dashboards)
if tags_realtime:
    app.include_router(tags_realtime.router, prefix="/api/tags", tags=["tags-realtime"])

# Formula Engine Routes (local evaluation only)
if formulas:
    app.include_router(formulas.router, prefix="/api", tags=["formulas"])
    logger.info("✅ Formula engine routes mounted at /api/formulas")

# WebSocket Routes for real-time streaming
if websocket:
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
    logger.info("✅ WebSocket routes mounted at /ws")

# Security Routes
if security:
    app.include_router(security.router, prefix="/api", tags=["security"])
    logger.info("✅ Security routes mounted at /api/security")

# Config Sync Routes (Backend → Gateway)
if config_sync:
    app.include_router(config_sync.router, prefix="/api", tags=["config-sync"])
    logger.info("✅ Config sync routes mounted at /api/config")

# Alarm Routes (Gateway is the source of alarms)
if alarms_routes:
    app.include_router(alarms_routes.router, prefix="/api/alarms", tags=["alarms"])
    logger.info("✅ Alarm routes mounted at /api/alarms")

# Mount static files for UI
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/ui", StaticFiles(directory=str(static_path), html=True), name="ui")
    logger.info(f"✅ Static UI files mounted at /ui from {static_path}")
else:
    logger.warning(f"⚠️  Static directory not found at {static_path}")


@app.get("/")
async def root():
    """Root endpoint - redirect to UI"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/index.html")


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "name": "OptiFlow Gateway API",
        "version": "1.0.0",
        "description": "Tag browsing and configuration API"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/compression/stats")
async def get_compression_stats():
    """
    Get compression statistics

    Returns SDT (Swinging Door Trending) compression statistics
    """
    try:
        from app.services.compression import get_compressor
        compressor = get_compressor()
        return compressor.get_statistics()
    except ImportError:
        return {
            "total_received": 0,
            "total_archived": 0,
            "total_compressed": 0,
            "compression_ratio_percent": 0,
            "configured_tags": 0,
            "note": "Compression service not available"
        }
    except Exception as e:
        logger.error(f"Error getting compression stats: {e}")
        return {
            "total_received": 0,
            "total_archived": 0,
            "total_compressed": 0,
            "compression_ratio_percent": 0,
            "configured_tags": 0,
            "error": str(e)
        }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint

    Expõe métricas do gateway em formato Prometheus:
    - Devices conectados por protocolo
    - Tags lidos/s e qualidade
    - Erros de leitura
    - Buffer size e operações
    - Comunicação com backend
    - Performance de protocolos (OPC-UA, Modbus, MQTT)
    """
    if not get_gateway_metrics:
        return {"error": "Metrics service not available"}

    try:
        gateway_metrics = get_gateway_metrics()
        metrics_data = gateway_metrics.export_metrics()
        content_type = gateway_metrics.get_content_type()
        
        return Response(
            content=metrics_data,
            media_type=content_type
        )
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}", exc_info=True)
        return Response(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@app.get("/health/metrics")
async def metrics_health():
    """
    Metrics health check
    
    Verifica se o sistema de métricas está funcionando
    """
    try:
        gateway_metrics = get_gateway_metrics()
        metrics_data = gateway_metrics.export_metrics()
        
        return {
            "status": "healthy",
            "metrics_service": "running",
            "metrics_size_bytes": len(metrics_data),
            "message": "Gateway metrics operational"
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "metrics_service": "error",
            "error": str(e),
            "message": "Gateway metrics not operational"
        }


@app.post("/api/browse", response_model=DiscoverTagsResponse)
async def browse_opcua_server(request: BrowseRequest):
    """
    Browse an OPC-UA server and discover all available tags
    Similar to KEPServerEX tag browsing

    Args:
        request: Browse request with endpoint and optional filters

    Returns:
        Discovered namespaces and tags
    """
    if not OPCUABrowser:
        raise HTTPException(503, "OPC-UA browser service not available")

    browser = OPCUABrowser(request.endpoint)

    try:
        logger.info(f"API: Browsing OPC-UA server {request.endpoint}")

        # Connect to server
        connected = await browser.connect()
        if not connected:
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to OPC-UA server"
            )

        # Get namespaces
        namespaces = await browser.get_namespaces()
        logger.info(f"API: Found {len(namespaces)} namespaces")

        # Discover tags
        namespace_filter = [request.namespace_index] if request.namespace_index is not None else None
        tags = await browser.discover_all_tags(namespace_filter=namespace_filter)

        # Apply tag name filter if provided
        if request.tag_filter:
            search_lower = request.tag_filter.lower()
            tags = [
                tag for tag in tags
                if search_lower in tag["tag_name"].lower() or
                   search_lower in tag["display_name"].lower()
            ]

        logger.info(f"API: Discovered {len(tags)} tags")

        return DiscoverTagsResponse(
            success=True,
            endpoint=request.endpoint,
            namespaces=namespaces,
            tags=tags,
            tag_count=len(tags)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Browse failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Browse operation failed: {str(e)}"
        )
    finally:
        await browser.disconnect()


@app.post("/api/search")
async def search_tags(request: SearchTagsRequest):
    """
    Search for tags by name in an OPC-UA server

    Args:
        request: Search request with endpoint and search term

    Returns:
        Matching tags
    """
    browser = OPCUABrowser(request.endpoint)

    try:
        logger.info(f"API: Searching tags in {request.endpoint} for '{request.search_term}'")

        # Connect to server
        connected = await browser.connect()
        if not connected:
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to OPC-UA server"
            )

        # Search tags
        namespace_filter = [request.namespace_index] if request.namespace_index is not None else None
        matches = await browser.search_tags(request.search_term, namespace_filter=namespace_filter)

        logger.info(f"API: Found {len(matches)} matching tags")

        return {
            "success": True,
            "endpoint": request.endpoint,
            "search_term": request.search_term,
            "matches": matches,
            "match_count": len(matches)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )
    finally:
        await browser.disconnect()


@app.get("/api/namespaces/{endpoint:path}")
async def get_namespaces(endpoint: str):
    """
    Get all available namespaces from an OPC-UA server

    Args:
        endpoint: OPC-UA server endpoint URL

    Returns:
        List of namespaces
    """
    # Decode endpoint (path parameter encoding)
    endpoint = endpoint.replace("%3A", ":").replace("%2F", "/")

    browser = OPCUABrowser(endpoint)

    try:
        logger.info(f"API: Getting namespaces from {endpoint}")

        # Connect to server
        connected = await browser.connect()
        if not connected:
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to OPC-UA server"
            )

        # Get namespaces
        namespaces = await browser.get_namespaces()

        logger.info(f"API: Found {len(namespaces)} namespaces")

        return {
            "success": True,
            "endpoint": endpoint,
            "namespaces": namespaces
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Get namespaces failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Get namespaces operation failed: {str(e)}"
        )
    finally:
        await browser.disconnect()


if __name__ == "__main__":
    import uvicorn
    
    # Initialize gateway metrics on startup
    init_gateway_metrics(
        gateway_id="gateway-01",
        version="1.0.0",
        protocols=["opc_ua", "modbus", "mqtt"]
    )
    logger.info("✅ Gateway metrics initialized")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
