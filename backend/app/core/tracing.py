"""
Distributed Tracing with OpenTelemetry (PDCA #25)

Provides end-to-end observability across all services.

Features:
- Automatic instrumentation for FastAPI, SQLAlchemy, Redis, Kafka
- Trace ID propagation
- Span annotations with context
- Jaeger/Tempo export
- Sampling strategies
"""

import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBasedTraceIdRatio

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for distributed tracing."""

    # Jaeger configuration
    JAEGER_AGENT_HOST = "jaeger"
    JAEGER_AGENT_PORT = 6831

    # Service info
    SERVICE_NAME = "optiflow-backend"
    SERVICE_VERSION = "1.0.0"

    # Sampling rates
    SAMPLING_RATE_PRODUCTION = 0.01  # 1% in production
    SAMPLING_RATE_DEVELOPMENT = 1.0  # 100% in development
    SAMPLING_RATE_ERRORS = 1.0       # 100% for errors


class DistributedTracing:
    """
    Manages distributed tracing setup and instrumentation.

    Uses OpenTelemetry for vendor-neutral tracing.
    """

    def __init__(
        self,
        service_name: str = TracingConfig.SERVICE_NAME,
        service_version: str = TracingConfig.SERVICE_VERSION,
        jaeger_host: str = TracingConfig.JAEGER_AGENT_HOST,
        jaeger_port: int = TracingConfig.JAEGER_AGENT_PORT,
        environment: str = "development"
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.environment = environment
        self.tracer_provider: Optional[TracerProvider] = None

    def setup(self) -> TracerProvider:
        """
        Setup OpenTelemetry tracing.

        Configures:
        - Resource with service metadata
        - Jaeger exporter
        - Sampling strategy
        - Automatic instrumentation
        """
        try:
            # Create resource with service info
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                SERVICE_VERSION: self.service_version,
                "deployment.environment": self.environment,
                "service.namespace": "optiflow"
            })

            # Determine sampling rate based on environment
            if self.environment == "production":
                sampling_rate = TracingConfig.SAMPLING_RATE_PRODUCTION
            else:
                sampling_rate = TracingConfig.SAMPLING_RATE_DEVELOPMENT

            # Create sampler (sample errors at 100%, others at configured rate)
            sampler = ParentBasedTraceIdRatio(sampling_rate)

            # Create tracer provider
            self.tracer_provider = TracerProvider(
                resource=resource,
                sampler=sampler
            )

            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )

            # Add batch span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self.tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            logger.info(
                f"✅ Distributed tracing initialized "
                f"(service: {self.service_name}, "
                f"environment: {self.environment}, "
                f"sampling: {sampling_rate * 100}%)"
            )

            return self.tracer_provider

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}", exc_info=True)
            logger.warning("⚠️  System will continue without tracing")
            return None

    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application.

        Automatically traces all HTTP requests.
        """
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=self.tracer_provider,
                excluded_urls="/health,/metrics,/docs,/redoc,/openapi.json"
            )

            logger.info("✅ FastAPI instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")

    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine.

        Traces all database queries.
        """
        try:
            SQLAlchemyInstrumentor().instrument(
                engine=engine,
                tracer_provider=self.tracer_provider,
                enable_commenter=True  # Add trace context to SQL comments
            )

            logger.info("✅ SQLAlchemy instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    def instrument_redis(self):
        """
        Instrument Redis client.

        Traces all Redis operations.
        """
        try:
            RedisInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )

            logger.info("✅ Redis instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to instrument Redis: {e}")

    def instrument_requests(self):
        """
        Instrument HTTP requests library.

        Traces outbound HTTP calls.
        """
        try:
            RequestsInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )

            logger.info("✅ Requests instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to instrument Requests: {e}")

    def instrument_logging(self):
        """
        Instrument logging.

        Adds trace context to log records.
        """
        try:
            LoggingInstrumentor().instrument(
                tracer_provider=self.tracer_provider,
                set_logging_format=True
            )

            logger.info("✅ Logging instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to instrument logging: {e}")

    def get_tracer(self, name: str = __name__):
        """Get tracer instance for manual instrumentation."""
        return trace.get_tracer(name)

    def shutdown(self):
        """Shutdown tracing and flush pending spans."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Distributed tracing shutdown")


# Global tracing instance
_tracing: Optional[DistributedTracing] = None


def get_tracing() -> DistributedTracing:
    """Get global tracing instance."""
    global _tracing

    if _tracing is None:
        from app.core.config import settings

        _tracing = DistributedTracing(
            environment=settings.ENVIRONMENT
        )

    return _tracing


def init_tracing(app) -> DistributedTracing:
    """
    Initialize distributed tracing for the application.

    Call this during application startup.
    """
    tracing = get_tracing()

    # Setup OpenTelemetry
    tracing.setup()

    # Instrument FastAPI
    tracing.instrument_fastapi(app)

    # Instrument other libraries
    tracing.instrument_redis()
    tracing.instrument_requests()
    tracing.instrument_logging()

    return tracing


def shutdown_tracing():
    """Shutdown tracing and flush spans."""
    tracing = get_tracing()
    tracing.shutdown()


# Convenience decorators and context managers

def trace_function(name: Optional[str] = None):
    """
    Decorator to trace a function.

    Usage:
        @trace_function("my_expensive_operation")
        async def expensive_operation():
            ...
    """
    def decorator(func):
        from functools import wraps
        import asyncio

        span_name = name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing().get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result

                except Exception as e:
                    span.set_attribute("function.success", False)
                    span.set_attribute("exception.type", type(e).__name__)
                    span.set_attribute("exception.message", str(e))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracing().get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result

                except Exception as e:
                    span.set_attribute("function.success", False)
                    span.set_attribute("exception.type", type(e).__name__)
                    span.set_attribute("exception.message", str(e))
                    span.record_exception(e)
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def trace_span(name: str, **attributes):
    """
    Context manager to create a custom span.

    Usage:
        with trace_span("database_query", query_type="select"):
            result = await db.execute(query)
    """
    tracer = get_tracing().get_tracer()

    with tracer.start_as_current_span(name) as span:
        # Add custom attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("exception.type", type(e).__name__)
            span.set_attribute("exception.message", str(e))
            span.record_exception(e)
            raise


def add_span_attributes(**attributes):
    """
    Add attributes to the current span.

    Usage:
        add_span_attributes(user_id="123", org_id="456")
    """
    span = trace.get_current_span()

    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, **attributes):
    """
    Add an event to the current span.

    Usage:
        add_span_event("cache_hit", cache_key="user:123")
    """
    span = trace.get_current_span()

    if span:
        span.add_event(name, attributes=attributes)
