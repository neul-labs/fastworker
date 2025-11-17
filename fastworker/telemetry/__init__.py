"""OpenTelemetry integration for FastWorker.

This module provides optional OpenTelemetry instrumentation for tracing and metrics.
To enable telemetry, install the optional dependencies:

    pip install fastworker[telemetry]

Or manually:

    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

Configuration via environment variables:
- FASTWORKER_TELEMETRY_ENABLED: Enable telemetry (default: false)
- OTEL_SERVICE_NAME: Service name (default: fastworker)
- OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
"""

from .tracer import get_tracer, trace_task, trace_operation
from .metrics import get_meter, record_task_metric, record_worker_metric

__all__ = [
    "get_tracer",
    "trace_task",
    "trace_operation",
    "get_meter",
    "record_task_metric",
    "record_worker_metric",
]
