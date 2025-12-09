"""OpenTelemetry metrics support for FastWorker."""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Check if OpenTelemetry is available
try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.sdk.resources import Resource

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.debug(
        "OpenTelemetry metrics not available. Install with: pip install fastworker[telemetry]"
    )


class NoOpMeter:
    """No-op meter when OpenTelemetry is not available or disabled."""

    def create_counter(self, name: str, unit: str = "", description: str = ""):
        """Create no-op counter."""
        return NoOpCounter()

    def create_histogram(self, name: str, unit: str = "", description: str = ""):
        """Create no-op histogram."""
        return NoOpHistogram()

    def create_up_down_counter(self, name: str, unit: str = "", description: str = ""):
        """Create no-op up-down counter."""
        return NoOpUpDownCounter()


class NoOpCounter:
    """No-op counter."""

    def add(self, amount: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        """No-op add."""
        pass


class NoOpHistogram:
    """No-op histogram."""

    def record(
        self, amount: float, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """No-op record."""
        pass


class NoOpUpDownCounter:
    """No-op up-down counter."""

    def add(self, amount: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        """No-op add."""
        pass


# Global meter instance
_meter: Optional[Any] = None
_telemetry_enabled = os.getenv("FASTWORKER_TELEMETRY_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Metric instruments
_task_submitted_counter: Optional[Any] = None
_task_completed_counter: Optional[Any] = None
_task_failed_counter: Optional[Any] = None
_task_duration_histogram: Optional[Any] = None
_worker_active_gauge: Optional[Any] = None
_queue_size_gauge: Optional[Any] = None


def _initialize_meter():
    """Initialize OpenTelemetry meter."""
    global _meter, _task_submitted_counter, _task_completed_counter, _task_failed_counter
    global _task_duration_histogram, _worker_active_gauge, _queue_size_gauge

    if not OTEL_AVAILABLE:
        logger.warning(
            "OpenTelemetry metrics not available. Install with: pip install fastworker[telemetry]"
        )
        _meter = NoOpMeter()
        _task_submitted_counter = NoOpCounter()
        _task_completed_counter = NoOpCounter()
        _task_failed_counter = NoOpCounter()
        _task_duration_histogram = NoOpHistogram()
        _worker_active_gauge = NoOpUpDownCounter()
        _queue_size_gauge = NoOpUpDownCounter()
        return

    if not _telemetry_enabled:
        logger.debug(
            "Telemetry disabled. Set FASTWORKER_TELEMETRY_ENABLED=true to enable."
        )
        _meter = NoOpMeter()
        _task_submitted_counter = NoOpCounter()
        _task_completed_counter = NoOpCounter()
        _task_failed_counter = NoOpCounter()
        _task_duration_histogram = NoOpHistogram()
        _worker_active_gauge = NoOpUpDownCounter()
        _queue_size_gauge = NoOpUpDownCounter()
        return

    try:
        # Get configuration from environment
        service_name = os.getenv("OTEL_SERVICE_NAME", "fastworker")
        otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )

        # Create resource with service name
        resource = Resource.create({"service.name": service_name})

        # Configure OTLP exporter
        otlp_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)

        # Create metric reader
        reader = PeriodicExportingMetricReader(
            otlp_exporter, export_interval_millis=60000
        )

        # Create meter provider
        provider = MeterProvider(resource=resource, metric_readers=[reader])

        # Set global meter provider
        metrics.set_meter_provider(provider)

        # Get meter
        _meter = metrics.get_meter(__name__)

        # Create metric instruments
        _task_submitted_counter = _meter.create_counter(
            name="fastworker.tasks.submitted",
            unit="1",
            description="Number of tasks submitted",
        )

        _task_completed_counter = _meter.create_counter(
            name="fastworker.tasks.completed",
            unit="1",
            description="Number of tasks completed successfully",
        )

        _task_failed_counter = _meter.create_counter(
            name="fastworker.tasks.failed",
            unit="1",
            description="Number of tasks that failed",
        )

        _task_duration_histogram = _meter.create_histogram(
            name="fastworker.tasks.duration",
            unit="ms",
            description="Task execution duration in milliseconds",
        )

        _worker_active_gauge = _meter.create_up_down_counter(
            name="fastworker.workers.active",
            unit="1",
            description="Number of active workers",
        )

        _queue_size_gauge = _meter.create_up_down_counter(
            name="fastworker.queue.size",
            unit="1",
            description="Number of tasks in queue",
        )

        logger.info(
            f"OpenTelemetry metrics initialized: service={service_name}, endpoint={otlp_endpoint}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry metrics: {e}")
        _meter = NoOpMeter()
        _task_submitted_counter = NoOpCounter()
        _task_completed_counter = NoOpCounter()
        _task_failed_counter = NoOpCounter()
        _task_duration_histogram = NoOpHistogram()
        _worker_active_gauge = NoOpUpDownCounter()
        _queue_size_gauge = NoOpUpDownCounter()


def get_meter():
    """Get the global meter instance.

    Returns:
        Meter instance (OpenTelemetry meter or NoOpMeter)
    """
    if _meter is None:
        _initialize_meter()
    return _meter


def record_task_metric(
    metric_type: str,
    task_name: str,
    priority: Optional[str] = None,
    worker_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
):
    """Record a task metric.

    Args:
        metric_type: Type of metric ('submitted', 'completed', 'failed')
        task_name: Name of the task
        priority: Task priority (optional)
        worker_id: Worker ID (optional)
        duration_ms: Task duration in milliseconds (for completed tasks)

    Example:
        record_task_metric("submitted", "process_data", priority="high")
        record_task_metric("completed", "process_data", worker_id="worker1", duration_ms=150.5)
        record_task_metric("failed", "process_data", worker_id="worker1")
    """
    if _meter is None:
        _initialize_meter()

    attributes = {"task.name": task_name}
    if priority:
        attributes["task.priority"] = priority
    if worker_id:
        attributes["worker.id"] = worker_id

    if metric_type == "submitted":
        _task_submitted_counter.add(1, attributes)
    elif metric_type == "completed":
        _task_completed_counter.add(1, attributes)
        if duration_ms is not None:
            _task_duration_histogram.record(duration_ms, attributes)
    elif metric_type == "failed":
        _task_failed_counter.add(1, attributes)


def record_worker_metric(metric_type: str, worker_id: str, count: int = 1):
    """Record a worker metric.

    Args:
        metric_type: Type of metric ('active', 'queue_size')
        worker_id: Worker ID
        count: Count to add (positive or negative)

    Example:
        record_worker_metric("active", "worker1", 1)  # Worker started
        record_worker_metric("active", "worker1", -1)  # Worker stopped
        record_worker_metric("queue_size", "control-plane", 5)  # 5 tasks added to queue
    """
    if _meter is None:
        _initialize_meter()

    attributes = {"worker.id": worker_id}

    if metric_type == "active":
        _worker_active_gauge.add(count, attributes)
    elif metric_type == "queue_size":
        _queue_size_gauge.add(count, attributes)


def record_queue_size(worker_id: str, priority: str, size: int):
    """Record current queue size for a specific priority.

    Args:
        worker_id: Worker ID (usually control plane)
        priority: Task priority level
        size: Current queue size

    Example:
        record_queue_size("control-plane", "high", 10)
    """
    if _meter is None:
        _initialize_meter()

    attributes = {"worker.id": worker_id, "queue.priority": priority}

    # This would ideally be an observable gauge, but we use up-down counter for simplicity
    # In a real implementation, you might want to use callbacks for observable gauges
    _queue_size_gauge.add(size, attributes)
