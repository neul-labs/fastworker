"""Tests for OpenTelemetry metrics fallbacks."""

import pytest
from fastworker.telemetry.metrics import (
    NoOpMeter,
    NoOpCounter,
    NoOpHistogram,
    NoOpUpDownCounter,
    get_meter,
    record_task_metric,
    record_worker_metric,
    record_queue_size,
)


def test_noop_counter_add():
    c = NoOpCounter()
    c.add(1, {"key": "val"})  # should not raise


def test_noop_histogram_record():
    h = NoOpHistogram()
    h.record(42.0, {"key": "val"})  # should not raise


def test_noop_updowncounter_add():
    u = NoOpUpDownCounter()
    u.add(1, {"key": "val"})  # should not raise


def test_noop_meter_create_counter():
    m = NoOpMeter()
    c = m.create_counter("test.counter")
    assert isinstance(c, NoOpCounter)


def test_noop_meter_create_histogram():
    m = NoOpMeter()
    h = m.create_histogram("test.histogram")
    assert isinstance(h, NoOpHistogram)


def test_noop_meter_create_updowncounter():
    m = NoOpMeter()
    u = m.create_up_down_counter("test.updown")
    assert isinstance(u, NoOpUpDownCounter)


def test_get_meter_returns_meter():
    meter = get_meter()
    assert meter is not None


def test_record_task_metric_does_not_raise():
    record_task_metric("completed", "add", priority="normal", worker_id="w1", duration_ms=100.0)
    record_task_metric("failed", "add", priority="high", worker_id="w2")


def test_record_worker_metric_does_not_raise():
    record_worker_metric("worker_count", "w1", count=1)
    record_worker_metric("queue_size", "w2", count=5)


def test_record_queue_size_does_not_raise():
    record_queue_size(worker_id="w1", priority="normal", size=10)
    record_queue_size(worker_id="w1", priority="high", size=0)
