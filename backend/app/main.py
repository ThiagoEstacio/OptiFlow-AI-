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
from app.api.routes.health import router as health_router
from app.api.v1.endpoints.websocket import router as websocket_router
from app.db.session import init_db, get_db, check_db_health
from app.services.autonomous_agent import init_autonomous_agent
from app.services.kafka_producer import init_kafka_producer, cleanup_kafka_producer
from app.services.timeseries_consumer import start_timeseries_consumer, stop_timeseries_consumer
from app.services.dlq_processor import start_dlq_processor, stop_dlq_processor
from app.services.gateway_service import get_gateway
from app.services.cache_service import cache_service

# Import service modules to register their Prometheus metrics
import app.services.gateway_service
import app.services.timeseries_consumer
import app.services.dlq_processor
from app.middleware.timeout import TimeoutMiddleware
from app.middleware.circuit_breaker import CircuitBreakerMiddleware
from app.middleware.prometheus_middleware import PrometheusMiddleware
from app.services.prometheus_metrics import init_metrics, get_metrics
from app.core.security_layer import init_security, audit_logger
from app.services.mat_view_refresher import start_mat_view_refresher, stop_mat_view_refresher

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security: Admin API Key (will be generated on startup)
ADMIN_API_KEY = None

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
            await update_ml_agent_metrics()
            await asyncio.sleep(15)  # Update every 15 seconds
        except Exception as e:
            logger.warning(f"Metrics updater error: {e}")
            await asyncio.sleep(15)


async def update_ml_agent_metrics():
    """Update ML/AI specific metrics"""
    try:
        import httpx
        
        # Check Ollama health
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://ollama:11434/api/tags")
                if response.status_code == 200:
                    optiflow_ollama_health.set(1)
                else:
                    optiflow_ollama_health.set(0)
        except Exception:
            optiflow_ollama_health.set(0)
        
        # Check Agent health
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:8000/api/v1/agent/health")
                if response.status_code == 200:
                    data = response.json()
                    optiflow_agent_status.set(1 if data.get("status") == "healthy" else 0)
                else:
                    optiflow_agent_status.set(0)
        except Exception:
            optiflow_agent_status.set(0)
        
        # Check MLflow experiments (if accessible)
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try to get experiment count from MLflow
                response = await client.get("http://mlflow:5000/api/2.0/mlflow/experiments/search")
                if response.status_code == 200:
                    data = response.json()
                    experiments = data.get("experiments", [])
                    optiflow_mlflow_experiments.set(len(experiments))
        except Exception:
            # MLflow not accessible or no experiments
            pass
            
    except Exception as e:
        logger.debug(f"ML/Agent metrics update error: {e}")


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

    # Initialize Cache Service (Redis)
    try:
        await cache_service.connect()
        logger.info("✅ Cache service initialized and connected to Redis")
    except Exception as e:
        logger.warning(f"⚠️  Cache service initialization failed: {e}")
        logger.warning("⚠️  System will continue without caching")

    # Initialize Security Layer (API Keys, Rate Limiting, Audit)
    global ADMIN_API_KEY
    try:
        ADMIN_API_KEY = init_security()
        logger.info("✅ Security layer initialized")
        logger.info(f"🔑 Admin API Key: {ADMIN_API_KEY}")
        logger.info("⚠️  IMPORTANT: Store this key securely! It will not be shown again.")
        audit_logger.log_security_event('system_startup', 'Security layer initialized')
    except Exception as e:
        logger.warning(f"⚠️  Security layer initialization failed: {e}")
        logger.warning("⚠️  System will continue without advanced security features")

    # Initialize Kafka producer for real-time streaming (event-driven architecture)
    try:
        await init_kafka_producer()
        logger.info("✅ Kafka producer initialized - event-driven architecture enabled")
    except Exception as e:
        logger.warning(f"⚠️  Kafka producer initialization failed: {e}")
        logger.warning("⚠️  System will continue without Kafka publishing")

    # Initialize Alarm Monitoring Service
    try:
        from app.services.alarm_monitor_service import get_alarm_monitor_service
        from app.services.alarm_initializer import initialize_default_alarms
        from app.db.session import AsyncSessionLocal

        # Initialize default alarm definitions if needed
        await initialize_default_alarms()

        # Start alarm monitoring
        alarm_monitor = get_alarm_monitor_service()
        async with AsyncSessionLocal() as db:
            await alarm_monitor.start(db)
        logger.info("✅ Alarm monitoring service initialized and running")
    except Exception as e:
        logger.warning(f"⚠️  Alarm monitoring initialization failed: {e}")
        logger.warning("⚠️  System will continue without automatic alarm monitoring")

    # Initialize Kafka consumer for time-series data to InfluxDB
    try:
        await start_timeseries_consumer()
        logger.info("✅ Kafka consumer initialized - consuming to InfluxDB")
    except Exception as e:
        logger.warning(f"⚠️  Kafka consumer initialization failed: {e}")
        logger.warning("⚠️  System will continue without Kafka consuming")
    
    # Initialize DLQ processor for failed messages
    try:
        await start_dlq_processor()
        logger.info("✅ DLQ processor initialized - handling failed messages")
    except Exception as e:
        logger.warning(f"⚠️  DLQ processor initialization failed: {e}")
        logger.warning("⚠️  System will continue without DLQ processing")
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

    # Start materialized view auto-refresher
    mat_view_task = None
    try:
        mat_view_task = asyncio.create_task(start_mat_view_refresher())
        logger.info("✅ Materialized view auto-refresher started")
    except Exception as e:
        logger.warning(f"⚠️  Failed to start mat view refresher: {e}")

    # Auto-start simulator for demo/development
    logger.info("🔧 Attempting to auto-start simulator...")
    try:
        from app.services.lightweight_simulator import get_simulator
        simulator = get_simulator()
        logger.info(f"🔧 Simulator instance obtained, running={simulator.running}")
        if not simulator.running:
            simulator.start()
            logger.info("✅ Simulator auto-started for demo mode")
        else:
            logger.info("ℹ️  Simulator already running")
    except Exception as e:
        logger.warning(f"⚠️  Failed to auto-start simulator: {e}", exc_info=True)

    # Auto-start Gateway Service for PLC → Kafka bridge
    logger.info("🔧 Attempting to auto-start Gateway Service...")
    try:
        from app.services.gateway_service import get_gateway
        gateway = get_gateway()
        logger.info(f"🔧 Gateway instance obtained, running={gateway.running}")
        if not gateway.running:
            await gateway.start()
            logger.info("✅ Gateway Service auto-started (PLC → Kafka bridge)")
        else:
            logger.info("ℹ️  Gateway Service already running")
    except Exception as e:
        logger.warning(f"⚠️  Failed to auto-start Gateway Service: {e}", exc_info=True)

    yield

    # Shutdown
    logger.info("👋 Shutting down OptiFlow AI Platform...")

    # Stop Alarm Monitoring Service
    try:
        from app.services.alarm_monitor_service import get_alarm_monitor_service
        alarm_monitor = get_alarm_monitor_service()
        if alarm_monitor.is_running:
            await alarm_monitor.stop()
            logger.info("✅ Alarm monitoring service stopped")
    except Exception as e:
        logger.warning(f"⚠️  Failed to stop alarm monitoring: {e}")

    # Stop Gateway Service
    try:
        from app.services.gateway_service import get_gateway
        gateway = get_gateway()
        if gateway.running:
            await gateway.stop()
            logger.info("✅ Gateway Service stopped")
    except Exception as e:
        logger.warning(f"⚠️  Failed to stop Gateway Service: {e}")
    
    # Stop mat view refresher
    if mat_view_task:
        try:
            await stop_mat_view_refresher()
        except Exception as e:
            logger.warning(f"⚠️  Mat view refresher cleanup warning: {e}")
    
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
    
    # Cleanup DLQ processor
    try:
        await stop_dlq_processor()
        logger.info("✅ DLQ processor cleaned up")
    except Exception as e:
        logger.warning(f"⚠️  DLQ processor cleanup warning: {e}")

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

# Add ML/AI specific metrics to the Prometheus registry
logger.info("🤖 Adding ML/AI metrics...")

# Get the prometheus metrics singleton and its registry
_metrics = get_metrics()
_registry = _metrics.registry

# Register ML/AI metrics in module scope for access by updater
optiflow_ollama_health = Gauge(
    'optiflow_ollama_health',
    'Ollama service health status (1=healthy, 0=unhealthy)',
    registry=_registry
)
optiflow_agent_status = Gauge(
    'optiflow_agent_status',
    'Autonomous agent status (1=healthy, 0=unhealthy)',
    registry=_registry
)
optiflow_agent_insights_total = Counter(
    'optiflow_agent_insights_total',
    'Total number of insights generated by autonomous agent',
    registry=_registry
)
optiflow_agent_cycle_duration = Histogram(
    'optiflow_agent_cycle_duration_seconds',
    'Duration of autonomous agent monitoring cycles',
    buckets=[1, 5, 10, 30, 60, 120, 300],
    registry=_registry
)

# MLflow metrics
optiflow_mlflow_experiments = Gauge(
    'optiflow_mlflow_experiments_total',
    'Total number of MLflow experiments',
    registry=_registry
)
optiflow_mlflow_runs = Gauge(
    'optiflow_mlflow_runs_total',
    'Total number of MLflow runs',
    registry=_registry
)

# ML Model metrics
optiflow_ml_predictions_total = Counter(
    'optiflow_ml_predictions_total',
    'Total number of ML predictions made',
    ['model_type', 'status'],
    registry=_registry
)
optiflow_ml_training_duration = Histogram(
    'optiflow_ml_training_duration_seconds',
    'Duration of ML model training',
    ['model_type'],
    buckets=[1, 10, 30, 60, 300, 600, 1800, 3600],
    registry=_registry
)
optiflow_ml_model_accuracy = Gauge(
    'optiflow_ml_model_accuracy',
    'ML model accuracy score',
    ['model_type', 'metric'],
    registry=_registry
)

logger.info("✅ ML/AI metrics registered")


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
    # Development: Allow all origins
    allowed_origins = ["*"]
    logger.warning(f"⚠️  CORS configured for {settings.ENVIRONMENT.upper()} - ALLOWING ALL ORIGINS")

app.add_middleware(
    # If allowed_origins is a wildcard ("[\"*\"]" in settings), enable a permissive
    # CORS policy that accepts any origin. Using allow_origin_regex=".*" allows
    # credentials to be used while still permitting all origins.
    CORSMiddleware,
    **(
        {
            "allow_origin_regex": ".*",
            "allow_credentials": True,
        }
        if allowed_origins == ["*"]
        else {
            "allow_origins": allowed_origins,
            "allow_credentials": settings.CORS_CREDENTIALS,
        }
    ),
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

# Include Gateway router for industrial protocol bridge
from app.api.routes.gateway import router as gateway_router
app.include_router(gateway_router, prefix="/api/v1")
logger.info("✅ Gateway endpoint registered at /api/v1/gateway")

# Include health check router
app.include_router(health_router)
logger.info("✅ Health endpoints registered at /api/health and /api/readiness")

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


@app.get("/health/deep")
async def deep_health_check():
    """
    Comprehensive health check for all system dependencies
    
    Returns detailed status of:
    - PostgreSQL database
    - Redis cache
    - InfluxDB (time-series data)
    - Kafka (event streaming)
    - Materialized views freshness
    
    Returns 503 if any critical service is down
    """
    from datetime import datetime, timedelta
    from app.services.influxdb import influxdb_service
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "services": {}
    }
    
    all_healthy = True
    warnings = []
    
    # 1. PostgreSQL Check
    try:
        db_healthy = await check_db_health()
        health_status["services"]["postgresql"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "details": "Connected" if db_healthy else "Connection failed"
        }
        if not db_healthy:
            all_healthy = False
    except Exception as e:
        health_status["services"]["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # 2. Redis Cache Check
    try:
        from app.services.redis_cache import redis_cache_service
        
        if redis_cache_service and redis_cache_service.available:
            # Try ping
            redis_cache_service.client.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "details": "Connected"
            }
        else:
            health_status["services"]["redis"] = {
                "status": "degraded",
                "details": "Cache disabled"
            }
            warnings.append("Redis cache is disabled")
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        warnings.append("Redis unavailable - caching disabled")
    
    # 3. InfluxDB Check
    try:
        from app.services.influxdb import influxdb_service
        
        # Try a simple operation to verify InfluxDB
        if influxdb_service and influxdb_service.client:
            health_status["services"]["influxdb"] = {
                "status": "healthy",
                "details": "Client initialized"
            }
        else:
            health_status["services"]["influxdb"] = {
                "status": "degraded",
                "details": "Client not initialized"
            }
            warnings.append("InfluxDB client not initialized")
    except Exception as e:
        health_status["services"]["influxdb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        warnings.append("InfluxDB check failed")
    
    # 4. Kafka Check (non-blocking)
    try:
        from app.services.kafka_producer import get_kafka_producer
        kafka_prod = get_kafka_producer()
        kafka_status = "healthy" if kafka_prod and kafka_prod._producer else "degraded"
        health_status["services"]["kafka"] = {
            "status": kafka_status,
            "details": "Producer active" if kafka_status == "healthy" else "Producer not initialized"
        }
        if kafka_status != "healthy":
            warnings.append("Kafka unavailable - event streaming disabled")
    except Exception as e:
        health_status["services"]["kafka"] = {
            "status": "degraded",
            "details": "Producer not available"
        }
        warnings.append("Kafka unavailable - event streaming disabled")
    
    # 5. Materialized Views Freshness Check
    try:
        from app.services.mat_view_refresher import REFRESH_SCHEDULES
        from app.db.session import AsyncSessionLocal
        
        mat_views_status = {}
        now = datetime.now()
        
        async with AsyncSessionLocal() as session:
            for view_name, interval in REFRESH_SCHEDULES.items():
                # Check last refresh time from pg_stat_statements or estimate
                # For now, we'll mark as healthy if view exists
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {view_name}")
                )
                row_count = result.scalar()
                
                mat_views_status[view_name] = {
                    "status": "healthy",
                    "row_count": row_count,
                    "refresh_interval": f"{interval}s"
                }
        
        health_status["services"]["materialized_views"] = {
            "status": "healthy",
            "views": mat_views_status
        }
        
    except Exception as e:
        health_status["services"]["materialized_views"] = {
            "status": "degraded",
            "error": str(e)
        }
        warnings.append("Materialized views check failed")
    
    # Add warnings if any
    if warnings:
        health_status["warnings"] = warnings
    
    # Set overall status
    if not all_healthy:
        health_status["status"] = "degraded"
    
    # Return 503 if critical services are down, otherwise 200
    status_code = 503 if not all_healthy else 200
    
    return JSONResponse(status_code=status_code, content=health_status)


@app.get("/metrics")
async def metrics(request: Request):
    """
    Prometheus metrics endpoint

    Exposes application metrics in Prometheus format for scraping.
    Includes HTTP requests, database operations, extended tags, gateway status,
    AI agent interactions, and custom OptiFlow metrics.
    """
    try:
        # Ensure Gateway, Consumer, and DLQ metrics are registered
        # by importing the metric variables (triggers module execution)
        try:
            from app.services.gateway_service import (
                gateway_messages_published_total,
                gateway_publish_latency_seconds,
                gateway_buffer_size,
                gateway_circuit_breaker_state,
                gateway_tags_discovered,
                gateway_transformations_applied
            )
            from app.services.timeseries_consumer import (
                consumer_messages_consumed_total,
                consumer_messages_written_total,
                consumer_batch_size,
                consumer_write_latency_seconds,
                consumer_dedup_hits_total,
                consumer_dlq_sent_total
            )
            from app.services.dlq_processor import (
                dlq_messages_processed_total,
                dlq_retry_attempts_total,
                dlq_queue_size
            )
        except Exception as e:
            logger.warning(f"Could not import service metrics: {e}")
        
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
