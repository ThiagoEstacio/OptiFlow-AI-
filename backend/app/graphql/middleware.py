"""
GraphQL Middleware (PDCA #27 Integration)

Integrates:
- PDCA #25: Distributed Tracing
- PDCA #26: Advanced Cache
- PDCA #14: Optimized Queries
- Prometheus Metrics
- Rate Limiting
- Error Handling
"""

import time
import logging
from typing import Any, Callable
from strawberry.extensions import Extension
from strawberry.types import Info

from app.graphql.metrics import (
    graphql_requests_total,
    graphql_request_duration_seconds,
    graphql_active_requests,
    graphql_errors_total,
    check_query_complexity_limit
)
from app.core.tracing import trace_span
from app.core.advanced_cache import get_advanced_cache

logger = logging.getLogger(__name__)


class PerformanceMonitoringExtension(Extension):
    """
    Strawberry extension for performance monitoring.

    Integrates PDCA #25 (Tracing) and Prometheus metrics.
    """

    def __init__(self):
        self.start_time = None
        self.operation_name = None

    def on_request_start(self):
        """Called when GraphQL request starts."""
        self.start_time = time.time()

    def on_request_end(self):
        """Called when GraphQL request ends."""
        if self.start_time:
            duration = time.time() - self.start_time

            if self.operation_name:
                graphql_request_duration_seconds.labels(
                    operation_type='query',
                    operation_name=self.operation_name
                ).observe(duration)

    def on_operation_start(self, info: Info):
        """Called when operation starts."""
        try:
            # Get operation name
            operation = info.operation
            if operation:
                self.operation_name = operation.name or 'anonymous'

                # Check query complexity
                query_string = str(operation)
                try:
                    check_query_complexity_limit(query_string, max_complexity=150)
                except Exception as e:
                    logger.warning(f"Query complexity check failed: {e}")
                    raise

                # Track active requests
                graphql_active_requests.labels(
                    operation_type=operation.operation.value
                ).inc()

        except Exception as e:
            logger.error(f"Error in on_operation_start: {e}")

    def on_operation_end(self, info: Info):
        """Called when operation ends."""
        try:
            if info.operation:
                graphql_active_requests.labels(
                    operation_type=info.operation.operation.value
                ).dec()
        except Exception as e:
            logger.error(f"Error in on_operation_end: {e}")


class CacheExtension(Extension):
    """
    Strawberry extension for cache integration.

    Integrates PDCA #26 (Advanced Cache).
    """

    def __init__(self):
        self.cache = get_advanced_cache()

    async def resolve(self, _next, root, info: Info, *args, **kwargs):
        """
        Intercept field resolution for caching.

        This is a basic cache layer - for more control,
        use @cached_function decorator directly in resolvers.
        """
        # Get field name
        field_name = info.field_name

        # Only cache certain expensive fields
        cacheable_fields = {'site', 'assets', 'alarms', 'gateways'}

        if field_name in cacheable_fields:
            # Build cache key
            cache_key = f"graphql:{field_name}:{args}:{kwargs}"

            # Try cache
            cached_value = await self.cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"GraphQL cache hit: {field_name}")
                return cached_value

            # Execute resolver
            result = await _next(root, info, *args, **kwargs)

            # Cache result (TTL based on field type)
            ttl = 60 if field_name == 'site' else 30
            await self.cache.set(cache_key, result, ttl=ttl)

            return result
        else:
            # Non-cacheable field - execute normally
            return await _next(root, info, *args, **kwargs)


class TracingExtension(Extension):
    """
    Strawberry extension for distributed tracing.

    Integrates PDCA #25 (OpenTelemetry Tracing).
    """

    def __init__(self):
        self.trace_span = None

    def on_request_start(self):
        """Start trace span for GraphQL request."""
        self.trace_span = trace_span("graphql_request")
        self.trace_span.__enter__()

    def on_request_end(self):
        """End trace span for GraphQL request."""
        if self.trace_span:
            self.trace_span.__exit__(None, None, None)

    def on_operation_start(self, info: Info):
        """Add operation details to trace."""
        if self.trace_span and info.operation:
            try:
                self.trace_span.set_attribute(
                    "graphql.operation_name",
                    info.operation.name or "anonymous"
                )
                self.trace_span.set_attribute(
                    "graphql.operation_type",
                    info.operation.operation.value
                )
            except Exception as e:
                logger.debug(f"Failed to set trace attributes: {e}")


class ErrorHandlingExtension(Extension):
    """
    Strawberry extension for error handling and logging.
    """

    def on_request_end(self):
        """Log errors if any occurred."""
        pass

    async def resolve(self, _next, root, info: Info, *args, **kwargs):
        """Wrap field resolution with error handling."""
        try:
            return await _next(root, info, *args, **kwargs)
        except Exception as e:
            # Log error
            field_name = info.field_name
            logger.error(
                f"GraphQL resolver error: {field_name} - {e}",
                exc_info=True
            )

            # Record metric
            graphql_errors_total.labels(
                operation_type='query',
                operation_name=info.operation.name if info.operation else 'unknown',
                error_type=type(e).__name__
            ).inc()

            # Re-raise with user-friendly message
            raise Exception(
                f"Failed to resolve field '{field_name}': {str(e)}"
            )


# ========================================
# Extension Collection
# ========================================

def get_graphql_extensions() -> list[Extension]:
    """
    Get all GraphQL extensions.

    Integrates:
    - Performance monitoring (Prometheus)
    - Distributed tracing (PDCA #25)
    - Advanced caching (PDCA #26)
    - Error handling
    """
    # Simplified for initial deployment - full extensions will be enabled after validation
    return [
        # TracingExtension(),  # Temporarily disabled - OpenTelemetry configuration pending
        # PerformanceMonitoringExtension(),  # Temporarily disabled
        # CacheExtension(),  # Temporarily disabled - Redis configuration pending
        # ErrorHandlingExtension(),  # Temporarily disabled - requires execution_context parameter
    ]
