"""
OptiFlow AI Platform - Main FastAPI Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.routes.simulator import router as simulator_router
from app.api.routes.admin import router as admin_router
from app.api.routes.ai_agent import router as ai_agent_router
from app.api.v1.endpoints.websocket import router as websocket_router
from app.db.session import init_db, get_db
from app.services.autonomous_agent import init_autonomous_agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    logger.info("🚀 Starting OptiFlow AI Platform...")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize autonomous AI agent
    try:
        async for db in get_db():
            await init_autonomous_agent(db)
            break  # Only need one session for initialization
        logger.info("🤖 Autonomous AI Agent initialized successfully")
    except Exception as e:
        logger.error(f"⚠️  Autonomous agent initialization failed: {e}")
        # Don't raise - agent is optional

    logger.info(f"🌐 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📊 API Version: {settings.API_V1_PREFIX}")

    yield

    # Shutdown
    logger.info("👋 Shutting down OptiFlow AI Platform...")


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
    """Health check endpoint - No rate limit"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    return {"message": "Metrics endpoint - to be implemented with prometheus_client"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
