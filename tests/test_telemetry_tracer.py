"""Tests for OpenTelemetry tracing fallbacks."""

import pytest

from fastworker.telemetry.tracer import NoOpSpan, NoOpTracer, get_tracer, trace_operation


def test_noop_tracer_start_span_returns_noop_span():
    tracer = NoOpTracer()
    span = tracer.start_span("test")
    assert isinstance(span, NoOpSpan)


def test_noop_span_set_attribute_does_not_raise():
    span = NoOpSpan()
    span.set_attribute("key", "value")


def test_noop_span_end_does_not_raise():
    span = NoOpSpan()
    span.end()


def test_noop_span_set_status():
    span = NoOpSpan()
    span.set_status("OK")  # should not raise


def test_noop_span_record_exception():
    span = NoOpSpan()
    span.record_exception(ValueError("test"))  # should not raise


def test_noop_span_context_manager():
    span = NoOpSpan()
    with span:
        pass  # should not raise


def test_get_tracer_returns_tracer():
    tracer = get_tracer()
    assert tracer is not None


@pytest.mark.asyncio
async def test_trace_operation_nested():
    with trace_operation("test.operation", attributes={"key": "val"}):
        pass


def test_trace_operation_with_attributes():
    with trace_operation("test.op", attributes={"task.id": "abc", "count": 5}):
        pass
