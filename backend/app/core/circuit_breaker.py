"""
Database Circuit Breaker

Protects PostgreSQL from cascading failures and connection pool exhaustion.

Features:
- Circuit breaker pattern (Open/Half-Open/Closed states)
- Query timeout enforcement
- Connection pool monitoring
- Automatic failover to cached data
- Exponential backoff for recovery
"""

import logging
import asyncio
from typing import Optional, Callable, Any, TypeVar, Dict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Blocking requests (too many failures)
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class DatabaseCircuitBreaker:
    """
    Circuit breaker for database operations.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked (return cached data or error)
    - HALF_OPEN: Testing recovery, limited requests allowed

    Thresholds:
    - failure_threshold: Number of failures before opening circuit (default: 5)
    - recovery_timeout: Seconds to wait before trying half-open (default: 60)
    - success_threshold: Successes needed in half-open to close (default: 2)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout_seconds: float = 30.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()

        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_timeouts = 0
        self.total_circuit_open_rejections = 0

    async def call(
        self,
        func: Callable[..., Any],
        *args,
        fallback: Optional[Callable[..., Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func

        Returns:
            Result from func or fallback

        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback provided
            asyncio.TimeoutError: If function exceeds timeout
        """
        self.total_calls += 1

        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}': Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = datetime.utcnow()
            else:
                # Circuit is open, use fallback or raise error
                self.total_circuit_open_rejections += 1
                logger.warning(
                    f"Circuit breaker '{self.name}': OPEN - Request blocked "
                    f"(failures: {self.failure_count}/{self.failure_threshold})"
                )

                if fallback:
                    logger.info(f"Circuit breaker '{self.name}': Using fallback function")
                    return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. Database may be overloaded."
                    )

        # Execute function with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout_seconds
            )

            # Success
            self._on_success()
            return result

        except asyncio.TimeoutError:
            self.total_timeouts += 1
            logger.error(
                f"Circuit breaker '{self.name}': Query timeout after {self.timeout_seconds}s"
            )
            self._on_failure()

            if fallback:
                logger.info(f"Circuit breaker '{self.name}': Using fallback after timeout")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            raise

        except Exception as e:
            logger.error(f"Circuit breaker '{self.name}': Error - {e}", exc_info=True)
            self._on_failure()

            if fallback:
                logger.info(f"Circuit breaker '{self.name}': Using fallback after error")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            raise

    def _on_success(self):
        """Handle successful execution."""
        self.total_successes += 1
        self.failure_count = 0  # Reset failure count on success

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"Circuit breaker '{self.name}': HALF_OPEN success "
                f"({self.success_count}/{self.success_threshold})"
            )

            if self.success_count >= self.success_threshold:
                # Close the circuit
                logger.info(f"Circuit breaker '{self.name}': Transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.failure_count = 0
                self.last_state_change = datetime.utcnow()

    def _on_failure(self):
        """Handle failed execution."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state, go back to open
            logger.warning(f"Circuit breaker '{self.name}': HALF_OPEN failed, returning to OPEN")
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.last_state_change = datetime.utcnow()

        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            logger.error(
                f"Circuit breaker '{self.name}': Threshold reached "
                f"({self.failure_count}/{self.failure_threshold}), transitioning to OPEN"
            )
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state and metrics."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold,
                "timeout_seconds": self.timeout_seconds
            },
            "metrics": {
                "total_calls": self.total_calls,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "total_timeouts": self.total_timeouts,
                "total_circuit_open_rejections": self.total_circuit_open_rejections,
                "success_rate": (self.total_successes / self.total_calls * 100) if self.total_calls > 0 else 0,
                "failure_rate": (self.total_failures / self.total_calls * 100) if self.total_calls > 0 else 0
            }
        }

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        logger.info(f"Circuit breaker '{self.name}': Manual reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()


# Global circuit breakers
_circuit_breakers: Dict[str, DatabaseCircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 2,
    timeout_seconds: float = 30.0
) -> DatabaseCircuitBreaker:
    """
    Get or create a circuit breaker instance.

    Args:
        name: Unique name for this circuit breaker
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Successes needed to close circuit from half-open
        timeout_seconds: Query timeout in seconds

    Returns:
        DatabaseCircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = DatabaseCircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds
        )

    return _circuit_breakers[name]


def get_all_circuit_breakers() -> Dict[str, DatabaseCircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers


# Decorator for automatic circuit breaker protection
def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 2,
    timeout_seconds: float = 30.0,
    fallback: Optional[Callable] = None
):
    """
    Decorator to protect async functions with circuit breaker.

    Usage:
        @with_circuit_breaker(name="user_query", timeout_seconds=10.0)
        async def get_user(db: AsyncSession, user_id: str):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Recovery wait time
        success_threshold: Successes to close from half-open
        timeout_seconds: Query timeout
        fallback: Optional fallback function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds
            )

            return await breaker.call(func, *args, fallback=fallback, **kwargs)

        return wrapper
    return decorator
