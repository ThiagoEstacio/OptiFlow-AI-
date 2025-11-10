"""
Database utility functions with fault-tolerance
"""
import asyncio
import async_timeout
import logging
from typing import TypeVar, Callable, Any
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_db_resilience(timeout: int = None):
    """
    Decorator to add timeout and circuit breaker protection to database operations

    Usage:
        @with_db_resilience(timeout=10)
        async def get_user(db: AsyncSession, user_id: int):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            operation_timeout = timeout or settings.DATABASE_COMMAND_TIMEOUT
            circuit_breaker = get_circuit_breaker("database")

            try:
                # Execute with circuit breaker and timeout protection
                async def execute():
                    async with async_timeout.timeout(operation_timeout):
                        return await func(*args, **kwargs)

                result = await circuit_breaker.call(execute)
                return result

            except asyncio.TimeoutError:
                logger.error(f"Database operation timeout: {func.__name__}")
                raise TimeoutError(
                    f"Database operation '{func.__name__}' exceeded {operation_timeout}s timeout"
                )

            except CircuitBreakerOpenError:
                logger.error(f"Circuit breaker open for: {func.__name__}")
                raise

            except Exception as e:
                logger.error(f"Database operation failed: {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


async def execute_with_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    **kwargs,
) -> T:
    """
    Execute a function with exponential backoff retry logic

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from func

    Raises:
        Exception: If all retries fail
    """
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    f"Retry {attempt}/{max_retries} for {func.__name__} "
                    f"failed: {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {max_retries} retry attempts failed for {func.__name__}: {e}"
                )

    # All retries exhausted
    raise last_exception


async def safe_db_operation(
    db: AsyncSession,
    operation: Callable[[AsyncSession], Any],
    default_value: Any = None,
    log_errors: bool = True,
) -> Any:
    """
    Execute a database operation with error handling and optional default value

    Args:
        db: Database session
        operation: Function that takes db session and returns result
        default_value: Value to return if operation fails
        log_errors: Whether to log errors

    Returns:
        Result from operation or default_value on error
    """
    try:
        result = await operation(db)
        return result
    except Exception as e:
        if log_errors:
            logger.error(f"Database operation failed: {e}")
        return default_value
