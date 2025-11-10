"""
Circuit breaker pattern implementation for database resilience
"""
import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for preventing cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        async with self._lock:
            # Check if circuit should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    # Still in OPEN state, reject request
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. "
                        f"Service unavailable for {self.recovery_timeout}s."
                    )

        # Execute the function
        try:
            result = await func(*args, **kwargs)

            # Record success
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.success_threshold:
                        logger.info(
                            "Circuit breaker transitioning to CLOSED state "
                            f"after {self.success_count} successful requests"
                        )
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.failure_count = 0

            return result

        except Exception as e:
            # Record failure
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.HALF_OPEN:
                    # Failed during recovery, go back to OPEN
                    logger.warning(
                        "Circuit breaker transitioning to OPEN state "
                        "after failure during recovery"
                    )
                    self.state = CircuitState.OPEN
                    self.success_count = 0

                elif (
                    self.state == CircuitState.CLOSED
                    and self.failure_count >= self.failure_threshold
                ):
                    # Too many failures, open the circuit
                    logger.error(
                        f"Circuit breaker OPENING after {self.failure_count} failures"
                    )
                    self.state = CircuitState.OPEN

            raise

    def get_state(self) -> Dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass


# Global circuit breaker instances for different services
_circuit_breakers: Dict[str, CircuitBreaker] = {
    "database": CircuitBreaker(
        failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        success_threshold=2,
    ),
}


def get_circuit_breaker(service: str = "database") -> CircuitBreaker:
    """Get circuit breaker for a service"""
    if service not in _circuit_breakers:
        _circuit_breakers[service] = CircuitBreaker()
    return _circuit_breakers[service]


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle circuit breaker errors gracefully
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle circuit breaker errors
        """
        try:
            response = await call_next(request)
            return response

        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, return 503 Service Unavailable
            logger.error(f"Circuit breaker open for {request.url.path}: {e}")

            return JSONResponse(
                status_code=503,
                content={
                    "detail": str(e),
                    "error": "service_unavailable",
                    "circuit_breaker": "open",
                    "message": "Service is temporarily unavailable. Please try again later.",
                },
            )

        except Exception:
            # Let other exceptions propagate
            raise
