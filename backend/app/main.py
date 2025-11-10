"""
OptiFlow AI Platform - Main FastAPI Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from contextlib import asynccontextmanager
import time
import asyncio
import async_timeout
import psutil

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.routes.simulator import router as simulator_router
from app.api.routes.admin import router as admin_router
from app.api.routes.ai_agent import router as ai_agent_router
from app.api.v1.endpoints.websocket import router as websocket_router
from app.db.session import init_db, get_db, check_db_health
from app.services.autonomous_agent import init_autonomous_agent
from app.services.kafka_producer import init_kafka_producer, cleanup_kafka_producer
from app.services.timeseries_consumer import start_timeseries_consumer, stop_timeseries_consumer
from app.middleware.timeout import TimeoutMiddleware
from app.middleware.circuit_breaker import CircuitBreakerMiddleware
from app.middleware.prometheus_middleware import PrometheusMiddleware
from app.services.prometheus_metrics import init_metrics, get_metrics

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# ========================================
# Prometheus Metrics Configuration
# ========================================

# HTTP Request Metrics
http_requests_total = Counter(
    'optiflow_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'optiflow_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'optiflow_http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Application Metrics
app_info = Info('optiflow_app', 'OptiFlow AI Platform information')
app_info.info({
    'version': settings.APP_VERSION,
    'environment': settings.ENVIRONMENT,
    'name': settings.APP_NAME
})

# Database Metrics
db_connections_active = Gauge(
    'optiflow_db_connections_active',
    'Active database connections',
    ['database']
)

db_queries_total = Counter(
    'optiflow_db_queries_total',
    'Total database queries executed',
    ['operation']
)

db_query_duration_seconds = Histogram(
    'optiflow_db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# User & Connection Metrics
active_users = Gauge(
    'optiflow_active_users',
    'Number of active authenticated users'
)

websocket_connections = Gauge(
    'optiflow_websocket_connections',
    'Number of active WebSocket connections'
)

# Extended Tags Metrics (PI AF)
extended_tags_total = Gauge(
    'extended_tags_total',
    'Total number of extended tags',
    ['tag_type', 'gateway_id']
)

extended_tags_archived = Gauge(
    'extended_tags_archived',
    'Number of tags with archiving enabled',
    ['archive_type', 'gateway_id']
)

# Device & Tag Metrics
devices_connected = Gauge(
    'optiflow_devices_connected',
    'Number of connected devices',
    ['protocol', 'status']
)

tags_read_total = Counter(
    'optiflow_tags_read_total',
    'Total number of tag reads',
    ['device', 'protocol']
)

alarms_active = Gauge(
    'optiflow_alarms_active',
    'Number of active alarms',
    ['severity', 'type']
)

# InfluxDB Metrics
influxdb_points_written_total = Counter(
    'optiflow_influxdb_points_written_total',
    'Total points written to InfluxDB',
    ['measurement']
)

# System Metrics
system_cpu_usage_percent = Gauge(
    'optiflow_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage_bytes = Gauge(
    'optiflow_system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_memory_available_bytes = Gauge(
    'optiflow_system_memory_available_bytes',
    'System available memory in bytes'
)

tag_formulas_total = Gauge(
    'tag_formulas_total',
    'Total number of tag formulas'
)

tag_calculations_total = Counter(
    'tag_calculations_total',
    'Total tag formula calculations executed',
    ['formula_id', 'success']
)

# Gateway Metrics
gateway_tags_total = Gauge(
    'gateway_tags_total',
    'Total tags per gateway',
    ['gateway_id', 'gateway_name']
)

gateway_connection_status = Gauge(
    'gateway_connection_status',
    'Gateway connection status (1=connected, 0=disconnected)',
    ['gateway_id', 'gateway_name']
)

# AI Agent Metrics
ai_agent_interactions_total = Counter(
    'ai_agent_interactions_total',
    'Total AI agent interactions',
    ['agent_type', 'success']
)

ai_agent_response_duration_seconds = Histogram(
    'ai_agent_response_duration_seconds',
    'AI agent response latency',
    ['agent_type']
)

# Asset Metrics
assets_total = Gauge(
    'assets_total',
    'Total number of assets',
    ['asset_type']
)

# Alarm Metrics
active_alarms_total = Gauge(
    'active_alarms_total',
    'Total active alarms',
    ['priority', 'gateway_id']
)


# ========================================
# System Metrics Update Function
# ========================================
async def update_system_metrics():
    """Update system metrics (CPU, memory, etc.)"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage_percent.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)
        system_memory_available_bytes.set(memory.available)
        
        # Initialize database connections metric with default value
        try:
            db_connections_active.labels(database='postgres').set(1)
        except Exception:
            pass
        
        # Set initial values for user/connection metrics
        active_users.set(0)
        websocket_connections.set(0)
        
    except Exception as e:
        logger.warning(f"Failed to update system metrics: {e}")


async def metrics_updater():
    """Background task to update metrics periodically"""
    while True:
        try:
            await update_system_metrics()
            await asyncio.sleep(15)  # Update every 15 seconds
        except Exception as e:
            logger.error(f"Error in metrics updater: {e}")
            await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events with improved resilience
    """
    logger.info("🚀 Starting OptiFlow AI Platform...")

    # Initialize database with exponential backoff retry logic
    max_retries = 5
    base_delay = 2  # seconds
    max_delay = 30  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"📊 Attempting database connection (attempt {attempt}/{max_retries})...")

            # Try with timeout
            async with async_timeout.timeout(45):  # 45 second timeout for initialization
                await init_db()

            logger.info("✅ Database initialized successfully")

            # Verify connection health
            if await check_db_health():
                logger.info("✅ Database health check passed")
            else:
                logger.warning("⚠️  Database initialized but health check failed")

            break  # Success!

        except asyncio.TimeoutError:
            # Calculate exponential backoff delay
            retry_delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

            if attempt < max_retries:
                logger.warning(
                    f"⚠️  Database connection timeout (attempt {attempt}/{max_retries})"
                )
                logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"❌ Database initialization failed after {max_retries} timeout attempts"
                )
                raise Exception("Database initialization timeout - service cannot start")

        except Exception as e:
            # Calculate exponential backoff delay
            retry_delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

            if attempt < max_retries:
                logger.warning(
                    f"⚠️  Database connection attempt {attempt} failed: {e}"
                )
                logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"❌ Database initialization failed after {max_retries} attempts: {e}"
                )
                raise
    
    # Initialize autonomous AI agent
    # Re-enabled after session management refactoring
    try:
        await init_autonomous_agent()
        logger.info("✅ Autonomous AI Agent initialized and running")
    except Exception as e:
        logger.error(f"⚠️  Autonomous agent initialization failed: {e}")
        logger.warning("⚠️  System will continue without autonomous monitoring")
        # Don't raise - agent is optional, system works without it

    # Initialize Kafka producer for real-time streaming (event-driven architecture)
    try:
        await init_kafka_producer()
        logger.info("✅ Kafka producer initialized - event-driven architecture enabled")
    except Exception as e:
        logger.warning(f"⚠️  Kafka producer initialization failed: {e}")
        logger.warning("⚠️  System will continue without Kafka publishing")

    # Initialize Kafka consumer for time-series data to InfluxDB
    try:
        await start_timeseries_consumer()
        logger.info("✅ Kafka consumer initialized - consuming to InfluxDB")
    except Exception as e:
        logger.warning(f"⚠️  Kafka consumer initialization failed: {e}")
        logger.warning("⚠️  System will continue without Kafka consuming")
    #     # Don't raise - Kafka is optional, system works without it

    logger.info(f"🌐 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📊 API Version: {settings.API_V1_PREFIX}")
    
    # Start system metrics updater in background
    metrics_task = None
    try:
        await update_system_metrics()  # Initial update
        metrics_task = asyncio.create_task(metrics_updater())
        logger.info("✅ System metrics updater started")
    except Exception as e:
        logger.warning(f"⚠️  Failed to start metrics updater: {e}")

    yield

    # Shutdown
    logger.info("👋 Shutting down OptiFlow AI Platform...")
    
    # Stop metrics updater
    if metrics_task:
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass

    # Cleanup Kafka consumer
    try:
        await stop_timeseries_consumer()
        logger.info("✅ Kafka consumer cleaned up")
    except Exception as e:
        logger.warning(f"⚠️  Kafka consumer cleanup warning: {e}")

    # Cleanup Kafka producer
    try:
        await cleanup_kafka_producer()
        logger.info("✅ Kafka producer cleaned up")
    except Exception as e:
        logger.warning(f"⚠️  Kafka producer cleanup warning: {e}")


# ========================================
# Initialize Prometheus Metrics BEFORE app creation
# ========================================
# This must be done before middleware is added to ensure
# the singleton instance is available when middleware initializes
logger.info("🔧 Initializing Prometheus metrics system...")
init_metrics(
    app_name="optiflow",
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT
)
logger.info("✅ Prometheus metrics system initialized")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Industrial IoT Platform with AI-powered optimization",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - PRODUCTION CONFIGURATION
if settings.ENVIRONMENT == "production":
    # Production: Strict CORS
    allowed_origins = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://app.yourdomain.com",
    ]
    logger.info(f"🔒 CORS configured for PRODUCTION with origins: {allowed_origins}")
else:
    # Development: Permissive CORS
    allowed_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["http://localhost:3000", "http://localhost:3002", "http://localhost:5173"]
    logger.warning(f"⚠️  CORS configured for {settings.ENVIRONMENT.upper()} with origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timeout middleware - prevent indefinite hangs
app.add_middleware(TimeoutMiddleware, timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS)

# Circuit breaker middleware - handle cascading failures
app.add_middleware(CircuitBreakerMiddleware)

# Prometheus metrics middleware - must be added BEFORE routes are registered
app.add_middleware(PrometheusMiddleware)
logger.info("✅ Prometheus middleware added to FastAPI")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include Simulator router (no authentication required for demo)
app.include_router(simulator_router, prefix="/api/v1")

# Include Admin router (requires authentication)
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])

# Include AI Agent router for dashboard builder
app.include_router(ai_agent_router, prefix="/api/v1/agent", tags=["ai-agent"])

# Include WebSocket router for real-time streaming
app.include_router(websocket_router, prefix="/api/v1")

# Include metrics endpoint (Prometheus)
from app.api.v1.endpoints.metrics import router as metrics_router
app.include_router(metrics_router, tags=["monitoring"])
logger.info("✅ Metrics endpoint registered at /metrics")


@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with graceful degradation

    Returns 200 if application is running (even if database is down)
    Includes database status in response for monitoring
    """
    # Check database health (with timeout)
    db_healthy = False
    db_error = None

    try:
        db_healthy = await check_db_health()
    except Exception as e:
        db_error = str(e)
        logger.warning(f"Database health check failed: {e}")

    # Application is healthy if it's running, even if DB is down
    # This allows load balancers to keep routing traffic
    # and application can handle DB errors gracefully
    response_data = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "healthy",
            "database": "healthy" if db_healthy else "degraded",
        },
    }

    if not db_healthy:
        response_data["warnings"] = [
            "Database connection degraded - some features may be limited"
        ]
        if db_error:
            response_data["db_error"] = db_error

    # Return 200 even if DB is down - application can still serve some requests
    return JSONResponse(status_code=200, content=response_data)


@app.get("/metrics")
async def metrics(request: Request):
    """
    Prometheus metrics endpoint

    Exposes application metrics in Prometheus format for scraping.
    Includes HTTP requests, database operations, extended tags, gateway status,
    AI agent interactions, and custom OptiFlow metrics.
    """
    try:
        # Update database connection metrics
        from app.db.session import engine
        if hasattr(engine, 'pool'):
            pool = engine.pool
            db_connections_active.set(pool.checkedout())

        # Update extended tags metrics (PI AF)
        db_session = None
        try:
            from app.db.session import AsyncSessionLocal
            from app.models.extended_tags import GatewayTagExtended
            from sqlalchemy import select, func

            db_session = AsyncSessionLocal()

            # Count tags by type and gateway
            result = await db_session.execute(
                select(
                    GatewayTagExtended.tag_type,
                    GatewayTagExtended.gateway_id,
                    func.count(GatewayTagExtended.id)
                ).group_by(
                    GatewayTagExtended.tag_type,
                    GatewayTagExtended.gateway_id
                )
            )

            # Reset gauge before updating
            extended_tags_total._metrics.clear()

            for tag_type, gateway_id, count in result:
                extended_tags_total.labels(
                    tag_type=tag_type,
                    gateway_id=str(gateway_id)
                ).set(count)

            # Count archived tags by type
            result = await db_session.execute(
                select(
                    GatewayTagExtended.archive_type,
                    GatewayTagExtended.gateway_id,
                    func.count(GatewayTagExtended.id)
                ).where(
                    GatewayTagExtended.archive_enabled == True
                ).group_by(
                    GatewayTagExtended.archive_type,
                    GatewayTagExtended.gateway_id
                )
            )

            # Reset gauge before updating
            extended_tags_archived._metrics.clear()

            for archive_type, gateway_id, count in result:
                extended_tags_archived.labels(
                    archive_type=archive_type,
                    gateway_id=str(gateway_id)
                ).set(count)

            # Count formulas
            from app.models.extended_tags import TagFormula
            result = await db_session.execute(
                select(func.count(TagFormula.id))
            )
            formula_count = result.scalar() or 0
            tag_formulas_total.set(formula_count)

        except Exception as e:
            logger.warning(f"Could not update extended tags metrics: {e}")
        finally:
            if db_session:
                await db_session.close()

        # Generate metrics in Prometheus format
        metrics_output = generate_latest()

        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )

    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
