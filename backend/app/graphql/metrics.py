"""
GraphQL Metrics & Monitoring (PDCA #27 + #25 + #26)

Integration with:
- PDCA #25: Distributed Tracing (OpenTelemetry)
- PDCA #26: Advanced Cache (metrics)
- Prometheus metrics for GraphQL operations
"""

import time
import logging
from typing import Any, Callable
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge
from app.core.tracing import trace_function, trace_span

logger = logging.getLogger(__name__)


# ========================================
# Prometheus Metrics for GraphQL
# ========================================

graphql_requests_total = Counter(
    'graphql_requests_total',
    'Total GraphQL requests',
    ['operation_type', 'operation_name', 'status']
)

graphql_request_duration_seconds = Histogram(
    'graphql_request_duration_seconds',
    'GraphQL request duration',
    ['operation_type', 'operation_name'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

graphql_resolver_duration_seconds = Histogram(
    'graphql_resolver_duration_seconds',
    'GraphQL resolver duration',
    ['resolver_name'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

graphql_cache_hits_total = Counter(
    'graphql_cache_hits_total',
    'GraphQL cache hits (PDCA #26)',
    ['resolver_name', 'cache_layer']
)

graphql_cache_misses_total = Counter(
    'graphql_cache_misses_total',
    'GraphQL cache misses (PDCA #26)',
    ['resolver_name']
)

graphql_active_requests = Gauge(
    'graphql_active_requests',
    'Number of active GraphQL requests',
    ['operation_type']
)

graphql_errors_total = Counter(
    'graphql_errors_total',
    'Total GraphQL errors',
    ['operation_type', 'operation_name', 'error_type']
)


# ========================================
# Decorators for Monitoring
# ========================================

def monitor_graphql_operation(operation_type: str = "query"):
    """
    Decorator to monitor GraphQL operations.

    Integrates:
    - Prometheus metrics
    - Distributed tracing (PDCA #25)
    - Performance logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @trace_function(f"graphql_{operation_type}_{func.__name__}")
        async def wrapper(*args, **kwargs):
            operation_name = func.__name__
            start_time = time.time()

            # Track active requests
            graphql_active_requests.labels(operation_type=operation_type).inc()

            try:
                # Execute resolver
                result = await func(*args, **kwargs)

                # Record success
                duration = time.time() - start_time
                graphql_requests_total.labels(
                    operation_type=operation_type,
                    operation_name=operation_name,
                    status='success'
                ).inc()

                graphql_request_duration_seconds.labels(
                    operation_type=operation_type,
                    operation_name=operation_name
                ).observe(duration)

                graphql_resolver_duration_seconds.labels(
                    resolver_name=operation_name
                ).observe(duration)

                # Log slow queries
                if duration > 1.0:
                    logger.warning(
                        f"Slow GraphQL {operation_type}: {operation_name} "
                        f"took {duration:.2f}s"
                    )

                return result

            except Exception as e:
                # Record error
                duration = time.time() - start_time
                error_type = type(e).__name__

                graphql_requests_total.labels(
                    operation_type=operation_type,
                    operation_name=operation_name,
                    status='error'
                ).inc()

                graphql_errors_total.labels(
                    operation_type=operation_type,
                    operation_name=operation_name,
                    error_type=error_type
                ).inc()

                logger.error(
                    f"GraphQL {operation_type} error: {operation_name} "
                    f"failed after {duration:.2f}s: {e}",
                    exc_info=True
                )

                raise

            finally:
                # Decrement active requests
                graphql_active_requests.labels(operation_type=operation_type).dec()

        return wrapper
    return decorator


def monitor_resolver(resolver_name: str):
    """
    Decorator specifically for GraphQL resolvers.

    Usage:
        @monitor_resolver("site")
        async def resolve_site(self, info, id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            with trace_span(f"resolver_{resolver_name}"):
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time

                    graphql_resolver_duration_seconds.labels(
                        resolver_name=resolver_name
                    ).observe(duration)

                    return result

                except Exception as e:
                    logger.error(
                        f"Resolver {resolver_name} failed: {e}",
                        exc_info=True
                    )
                    raise

        return wrapper
    return decorator


# ========================================
# Cache Metrics Integration (PDCA #26)
# ========================================

def record_cache_hit(resolver_name: str, cache_layer: str = "L1"):
    """Record cache hit for GraphQL resolver."""
    graphql_cache_hits_total.labels(
        resolver_name=resolver_name,
        cache_layer=cache_layer
    ).inc()


def record_cache_miss(resolver_name: str):
    """Record cache miss for GraphQL resolver."""
    graphql_cache_misses_total.labels(
        resolver_name=resolver_name
    ).inc()


# ========================================
# Performance Helpers
# ========================================

class GraphQLPerformanceMonitor:
    """
    Context manager for monitoring GraphQL performance.

    Example:
        async with GraphQLPerformanceMonitor("site_query") as monitor:
            # Query execution
            result = await execute_query()

            # Add custom attributes
            monitor.add_attribute("items_returned", len(result))
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.span = None

    async def __aenter__(self):
        self.start_time = time.time()
        self.span = trace_span(f"graphql_{self.operation_name}")
        self.span.__enter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        # Record duration
        graphql_resolver_duration_seconds.labels(
            resolver_name=self.operation_name
        ).observe(duration)

        # End trace span
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)

        # Log if slow
        if duration > 1.0:
            logger.warning(
                f"Slow GraphQL operation: {self.operation_name} "
                f"took {duration:.2f}s"
            )

    def add_attribute(self, key: str, value: Any):
        """Add custom attribute to trace span."""
        if self.span:
            try:
                self.span.set_attribute(key, value)
            except Exception as e:
                logger.debug(f"Failed to set span attribute: {e}")


# ========================================
# GraphQL Query Complexity Analysis
# ========================================

def analyze_query_complexity(query_string: str) -> int:
    """
    Analyze GraphQL query complexity.

    Simple heuristic based on:
    - Number of fields requested
    - Nesting depth
    - List fields

    Returns complexity score (higher = more complex)
    """
    complexity = 0

    # Count fields (rough estimate)
    complexity += query_string.count('\n')

    # Penalize nested queries
    depth = query_string.count('{')
    complexity += depth * 2

    # Penalize list operations
    if 'assets' in query_string:
        complexity += 5
    if 'alarms' in query_string:
        complexity += 5

    return complexity


def check_query_complexity_limit(query_string: str, max_complexity: int = 100):
    """
    Check if query exceeds complexity limit.

    Raises exception if too complex.
    """
    complexity = analyze_query_complexity(query_string)

    if complexity > max_complexity:
        logger.warning(
            f"Query complexity {complexity} exceeds limit {max_complexity}"
        )
        raise Exception(
            f"Query too complex (complexity: {complexity}, max: {max_complexity}). "
            f"Please simplify your query or split into multiple requests."
        )

    return complexity
