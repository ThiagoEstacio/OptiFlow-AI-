"""
Circuit Breaker Pattern Implementation

Prevents cascade failures by stopping requests to a failing service,
giving it time to recover before retrying.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked
- HALF_OPEN: Testing if service has recovered

Usage:
    breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    if breaker.call(risky_operation, arg1, arg2):
        # Success
    else:
        # Failed or circuit open
"""
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Blocking requests
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 2          # Successes before closing from half-open
    timeout: int = 60                   # Seconds before attempting recovery
    half_open_max_calls: int = 3        # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit Breaker for protecting against cascading failures

    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Wrap risky operations
        result = breaker.call(write_to_influxdb, data)
        if result is None:
            # Circuit is open or operation failed
            logger.error("InfluxDB unavailable, buffering data")
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        half_open_max_calls: int = 3,
        name: str = "default"
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            success_threshold: Number of successes needed to close circuit from half-open
            timeout: Seconds to wait before attempting recovery (OPEN -> HALF_OPEN)
            half_open_max_calls: Maximum calls allowed in half-open state
            name: Identifier for this circuit breaker (for logging)
        """
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            half_open_max_calls=half_open_max_calls
        )
        self.name = name

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0

        # Statistics
        self.total_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        self.last_state_change: Optional[datetime] = None

        logger.info(
            f"🔌 Circuit breaker '{self.name}' initialized: "
            f"failure_threshold={failure_threshold}, timeout={timeout}s"
        )

    def call(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result on success, None if circuit is open or function fails
        """
        self.total_calls += 1

        # Check if circuit should transition from OPEN -> HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                logger.warning(
                    f"⚡ Circuit breaker '{self.name}' is OPEN - "
                    f"blocking call (failed {self.failure_count} times)"
                )
                return None

        # In HALF_OPEN, limit number of test calls
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                logger.warning(
                    f"⚡ Circuit breaker '{self.name}' HALF_OPEN - "
                    f"max test calls reached ({self.half_open_calls})"
                )
                return None
            self.half_open_calls += 1

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            return None

    async def call_async(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Execute async function through circuit breaker

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result on success, None if circuit is open or function fails
        """
        self.total_calls += 1

        # Check if circuit should transition from OPEN -> HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                logger.warning(
                    f"⚡ Circuit breaker '{self.name}' is OPEN - "
                    f"blocking async call (failed {self.failure_count} times)"
                )
                return None

        # In HALF_OPEN, limit number of test calls
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                logger.warning(
                    f"⚡ Circuit breaker '{self.name}' HALF_OPEN - "
                    f"max test calls reached ({self.half_open_calls})"
                )
                return None
            self.half_open_calls += 1

        # Execute the async function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            return None

    def _on_success(self):
        """Handle successful operation"""
        self.total_successes += 1
        self.failure_count = 0  # Reset failure count

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"✅ Circuit breaker '{self.name}' HALF_OPEN success "
                f"({self.success_count}/{self.config.success_threshold})"
            )

            # Close circuit after enough successes
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()

    def _on_failure(self, exception: Exception):
        """Handle failed operation"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.error(
            f"❌ Circuit breaker '{self.name}' failure "
            f"({self.failure_count}/{self.config.failure_threshold}): {exception}"
        )

        # Open circuit after too many failures
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()

        # If failing in HALF_OPEN, reopen circuit
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"⚡ Circuit breaker '{self.name}' failed in HALF_OPEN - "
                f"reopening circuit"
            )
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        logger.error(
            f"⚡ Circuit breaker '{self.name}' -> OPEN "
            f"(threshold reached: {self.failure_count} failures)"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        self.last_state_change = datetime.now()
        logger.info(
            f"🔄 Circuit breaker '{self.name}' -> HALF_OPEN "
            f"(attempting recovery after {self.config.timeout}s)"
        )

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_state_change = datetime.now()
        logger.info(
            f"✅ Circuit breaker '{self.name}' -> CLOSED "
            f"(service recovered)"
        )

    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        logger.info(f"🔄 Manually resetting circuit breaker '{self.name}'")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking calls)"""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self.state == CircuitState.HALF_OPEN

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        success_rate = (
            (self.total_successes / self.total_calls * 100)
            if self.total_calls > 0
            else 0
        )

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": f"{success_rate:.1f}%",
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }
        }

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
            f"failures={self.failure_count}, total_calls={self.total_calls})"
        )
