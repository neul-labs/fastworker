"""Tests for the Management GUI server."""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from collections import OrderedDict

from fastworker.tasks.models import TaskResult, TaskStatus


class FakeHandler:
    """Minimal fake for ManagementRequestHandler to test endpoint dispatch."""

    def __init__(self, control_plane):
        self.control_plane = control_plane
        self._status = 200
        self._response_data = None
        self._headers = {}

    def send_response(self, code):
        self._status = code

    def send_header(self, key, value):
        self._headers[key] = value

    def end_headers(self):
        pass

    def send_json_response(self, data, status=200):
        self._status = status
        self._response_data = data

    def send_error_response(self, message, status=500):
        self._status = status
        self._response_data = {"error": message}

    def _handle_status(self):
        cp = self.control_plane
        self.send_json_response({
            "worker_id": cp.worker_id,
            "active_workers": 1,
            "queued_tasks": 0,
            "active_tasks": 0,
            "cached_results": 0,
            "uptime_seconds": None,
        })

    def _handle_workers(self):
        cp = self.control_plane
        self.send_json_response({
            "total_workers": 1,
            "workers": [{"id": cp.worker_id, "address": cp.base_address, "status": "active"}],
        })

    def _handle_tasks(self):
        self.send_json_response({
            "tasks": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
        })

    def _handle_cache_stats(self):
        self.send_json_response({
            "max_size": 10000,
            "current_size": 0,
            "ttl_seconds": 3600,
        })

    def _handle_queue_stats(self):
        self.send_json_response({
            "queues": {
                "critical": {"size": 0, "next_tasks": []},
                "high": {"size": 0, "next_tasks": []},
                "normal": {"size": 0, "next_tasks": []},
                "low": {"size": 0, "next_tasks": []},
            }
        })

    def _handle_registered_tasks(self):
        self.send_json_response({"tasks": []})


class MockControlPlane:
    worker_id = "test-cp"
    base_address = "tcp://127.0.0.1:5555"
    result_cache = OrderedDict()
    result_cache_max_size = 10000
    result_cache_ttl_seconds = 3600
    subworkers = {}
    task_queue = {}
    task_registry = MagicMock()


def test_status_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_status()
    assert h._status == 200
    assert h._response_data["worker_id"] == "test-cp"


def test_workers_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_workers()
    assert h._status == 200
    assert h._response_data["total_workers"] == 1


def test_tasks_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_tasks()
    assert h._status == 200
    assert h._response_data["total"] == 0


def test_cache_stats_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_cache_stats()
    assert h._status == 200
    assert h._response_data["max_size"] == 10000


def test_queue_stats_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_queue_stats()
    assert h._status == 200
    assert "critical" in h._response_data["queues"]


def test_registered_tasks_endpoint():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h._handle_registered_tasks()
    assert h._status == 200
    assert h._response_data["tasks"] == []


def test_send_error_response():
    cp = MockControlPlane()
    h = FakeHandler(cp)
    h.send_error_response("something broke", 503)
    assert h._status == 503
    assert h._response_data["error"] == "something broke"
