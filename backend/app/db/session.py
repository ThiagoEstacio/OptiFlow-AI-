"""
Database session management with fault-tolerant connection pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator
import logging
import asyncio
from urllib.parse import urlparse, parse_qs
import async_timeout

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

# Parse DATABASE_URL to add connection timeout parameters
def get_database_url_with_timeouts() -> str:
    """Add timeout parameters to database URL for asyncpg"""
    url = settings.DATABASE_URL

    # For asyncpg, we can add timeout parameters
    if "asyncpg" in url:
        separator = "&" if "?" in url else "?"
        url += f"{separator}timeout={settings.DATABASE_CONNECT_TIMEOUT}"
        url += f"&command_timeout={settings.DATABASE_COMMAND_TIMEOUT}"

    return url

# Create async engine with comprehensive fault-tolerance configuration
engine = create_async_engine(
    get_database_url_with_timeouts(),
    echo=settings.DEBUG,

    # Connection Pool Configuration
    pool_size=settings.DATABASE_POOL_SIZE,  # Min connections to maintain
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Additional connections allowed
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Wait time for available connection
    pool_recycle=settings.DATABASE_POOL_RECYCLE,  # Recycle connections to prevent stale connections
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,  # Test connections before use

    # Connection Settings
    poolclass=QueuePool,  # Use QueuePool for better connection management

    # Additional resilience settings
    connect_args={
        "server_settings": {
            "application_name": "optiflow_backend",
            "jit": "off",  # Disable JIT for more predictable performance
        },
        "timeout": settings.DATABASE_CONNECT_TIMEOUT,
        "command_timeout": settings.DATABASE_COMMAND_TIMEOUT,
    },
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Initialize database - create all tables with retry logic
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            # Set a timeout for the entire operation
            async with async_timeout.timeout(30):
                async with engine.begin() as conn:
                    # Import all models here to ensure they are registered
                    from app.models import organization, user, device, tag, alarm, ml_model, chat, dashboard

                    # Create all tables
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created successfully")
                    return  # Success!

        except asyncio.TimeoutError:
            if attempt < max_retries:
                logger.warning(f"Database initialization timeout (attempt {attempt}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Database initialization failed after {max_retries} timeout attempts")
                raise

        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Database initialization error (attempt {attempt}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")
                raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with timeout protection

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session = None
    try:
        # Add timeout for session acquisition
        async with async_timeout.timeout(settings.DATABASE_POOL_TIMEOUT):
            session = AsyncSessionLocal()

        try:
            yield session
            # Commit with timeout protection
            async with async_timeout.timeout(settings.DATABASE_COMMAND_TIMEOUT):
                await session.commit()

        except asyncio.TimeoutError:
            logger.error("Database commit timeout - rolling back transaction")
            await session.rollback()
            raise TimeoutError("Database operation timed out")

        except Exception as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise

    except asyncio.TimeoutError:
        logger.error("Database session acquisition timeout")
        raise TimeoutError("Could not acquire database connection")

    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise

    finally:
        if session:
            await session.close()


async def check_db_health() -> bool:
    """
    Check database health - used for health checks
    Returns True if database is accessible, False otherwise
    """
    from sqlalchemy import text

    try:
        async with async_timeout.timeout(5):
            async with AsyncSessionLocal() as session:
                # Simple query to check connection - using text() for SQLAlchemy 2.0
                await session.execute(text("SELECT 1"))
                return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
