"""OpenTelemetry tracing support for FastWorker."""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Any, Dict
from functools import wraps

logger = logging.getLogger(__name__)

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.debug(
        "OpenTelemetry not available. Install with: pip install fastworker[telemetry]"
    )


class NoOpTracer:
    """No-op tracer when OpenTelemetry is not available or disabled."""

    @contextmanager
    def start_as_current_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ):
        """No-op context manager."""
        yield None

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """No-op span."""
        return NoOpSpan()


class NoOpSpan:
    """No-op span when OpenTelemetry is not available or disabled."""

    def set_attribute(self, key: str, value: Any) -> None:
        """No-op set attribute."""
        pass

    def set_status(self, status) -> None:
        """No-op set status."""
        pass

    def record_exception(self, exception: Exception) -> None:
        """No-op record exception."""
        pass

    def end(self) -> None:
        """No-op end."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Global tracer instance
_tracer: Optional[Any] = None
_telemetry_enabled = os.getenv("FASTWORKER_TELEMETRY_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)


def _initialize_tracer():
    """Initialize OpenTelemetry tracer."""
    global _tracer

    if not OTEL_AVAILABLE:
        logger.warning(
            "OpenTelemetry not available. Install with: pip install fastworker[telemetry]"
        )
        _tracer = NoOpTracer()
        return

    if not _telemetry_enabled:
        logger.debug(
            "Telemetry disabled. Set FASTWORKER_TELEMETRY_ENABLED=true to enable."
        )
        _tracer = NoOpTracer()
        return

    try:
        # Get configuration from environment
        service_name = os.getenv("OTEL_SERVICE_NAME", "fastworker")
        otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )

        # Create resource with service name
        resource = Resource.create({"service.name": service_name})

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

        # Add span processor
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(
            f"OpenTelemetry tracer initialized: service={service_name}, endpoint={otlp_endpoint}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracer: {e}")
        _tracer = NoOpTracer()


def get_tracer():
    """Get the global tracer instance.

    Returns:
        Tracer instance (OpenTelemetry tracer or NoOpTracer)
    """
    if _tracer is None:
        _initialize_tracer()
    return _tracer


@contextmanager
def trace_operation(operation_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for tracing operations.

    Args:
        operation_name: Name of the operation
        attributes: Optional attributes to add to the span

    Example:
        with trace_operation("submit_task", {"task_name": "process_data"}):
            # Your code here
            pass
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name, attributes=attributes) as span:
        try:
            yield span
        except Exception as e:
            if span and OTEL_AVAILABLE and _telemetry_enabled:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
            raise


def trace_task(func):
    """Decorator for tracing task execution.

    Args:
        func: Task function to trace

    Example:
        @task
        @trace_task
        def my_task(x: int) -> int:
            return x * 2
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        task_name = func.__name__
        tracer = get_tracer()

        with tracer.start_as_current_span(f"task.{task_name}") as span:
            if span and OTEL_AVAILABLE and _telemetry_enabled:
                span.set_attribute("task.name", task_name)
                span.set_attribute("task.args_count", len(args))
                span.set_attribute("task.kwargs_count", len(kwargs))

            try:
                result = await func(*args, **kwargs)
                if span and OTEL_AVAILABLE and _telemetry_enabled:
                    span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                if span and OTEL_AVAILABLE and _telemetry_enabled:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        task_name = func.__name__
        tracer = get_tracer()

        with tracer.start_as_current_span(f"task.{task_name}") as span:
            if span and OTEL_AVAILABLE and _telemetry_enabled:
                span.set_attribute("task.name", task_name)
                span.set_attribute("task.args_count", len(args))
                span.set_attribute("task.kwargs_count", len(kwargs))

            try:
                result = func(*args, **kwargs)
                if span and OTEL_AVAILABLE and _telemetry_enabled:
                    span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                if span and OTEL_AVAILABLE and _telemetry_enabled:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                raise

    # Return appropriate wrapper based on function type
    import asyncio as aio

    if aio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
