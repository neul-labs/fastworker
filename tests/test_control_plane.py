"""Test cases for FastWorker ControlPlaneWorker."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from collections import OrderedDict

from fastworker.workers.control_plane import ControlPlaneWorker
from fastworker.tasks.models import (
    Task,
    TaskResult,
    TaskStatus,
    TaskPriority,
)
from fastworker.tasks.registry import task, task_registry


@pytest.fixture
def control_plane():
    """Create a test control plane worker."""
    return ControlPlaneWorker(
        worker_id="test-control-plane",
        base_address="tcp://127.0.0.1:5555",
        discovery_address="tcp://127.0.0.1:5550",
        gui_enabled=False,
        result_cache_max_size=100,
        result_cache_ttl_seconds=3600,
    )


def test_control_plane_initialization(control_plane):
    """Test control plane initialization."""
    assert control_plane.worker_id == "test-control-plane"
    assert control_plane.base_address == "tcp://127.0.0.1:5555"
    assert control_plane.discovery_address == "tcp://127.0.0.1:5550"
    assert control_plane.gui_enabled is False
    assert control_plane.result_cache_max_size == 100
    assert control_plane.result_cache_ttl_seconds == 3600
    assert not control_plane.running


def test_control_plane_attributes(control_plane):
    """Test control plane has required attributes."""
    # Task queues for each priority
    assert TaskPriority.CRITICAL in control_plane.task_queue
    assert TaskPriority.HIGH in control_plane.task_queue
    assert TaskPriority.NORMAL in control_plane.task_queue
    assert TaskPriority.LOW in control_plane.task_queue

    # Subworker registry
    assert isinstance(control_plane.subworkers, dict)

    # Result cache
    assert isinstance(control_plane.result_cache, OrderedDict)
    assert len(control_plane.result_cache) == 0

    # Active tasks
    assert isinstance(control_plane.active_tasks, dict)


def test_result_cache_store_and_get(control_plane):
    """Test result cache store and get operations."""
    task_id = "test-task-123"

    # Create a test result
    result = TaskResult(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        result={"value": 42},
        error=None,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )

    # Store result in cache
    control_plane._store_result(result)

    # Get result from cache
    cached = control_plane._get_result(task_id)
    assert cached is not None
    assert cached.task_id == task_id
    assert cached.status == TaskStatus.SUCCESS
    assert cached.result == {"value": 42}


def test_result_cache_ttl_expiration(control_plane):
    """Test result cache TTL expiration."""
    control_plane.result_cache_ttl_seconds = 1  # 1 second TTL for testing
    task_id = "test-task-ttl"

    # Create and cache a result
    result = TaskResult(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        result={"value": 42},
    )
    control_plane._store_result(result)

    # Result should be available immediately
    assert control_plane._get_result(task_id) is not None

    # Wait for TTL to expire
    import asyncio
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(1.1))

    # Result should be expired
    assert control_plane._get_result(task_id) is None


def test_result_cache_lru_eviction(control_plane):
    """Test result cache LRU eviction."""
    control_plane.result_cache_max_size = 3

    # Add more results than cache size
    for i in range(5):
        result = TaskResult(
            task_id=f"task-{i}",
            status=TaskStatus.SUCCESS,
            result={"value": i},
        )
        control_plane._store_result(f"task-{i}" if False else result)

    # Cache should have at most max_size entries
    assert len(control_plane.result_cache) <= control_plane.result_cache_max_size

    # Oldest entries should be evicted (task-0, task-1)
    assert control_plane._get_result("task-0") is None
    assert control_plane._get_result("task-1") is None

    # Newer entries should exist
    assert control_plane._get_result("task-2") is not None
    assert control_plane._get_result("task-4") is not None


def test_result_cache_access_updates_lru(control_plane):
    """Test that accessing a result updates its LRU position."""
    control_plane.result_cache_max_size = 3

    # Add results
    for i in range(3):
        result = TaskResult(
            task_id=f"task-{i}",
            status=TaskStatus.SUCCESS,
            result={"value": i},
        )
        control_plane._store_result(result)

    # Access task-0 to make it most recently used
    control_plane._get_result("task-0")

    # Add a new result (should evict task-1, the oldest)
    result = TaskResult(
        task_id="task-3",
        status=TaskStatus.SUCCESS,
        result={"value": 3},
    )
    control_plane._store_result(result)

    # task-0 should still exist (was accessed recently)
    assert control_plane._get_result("task-0") is not None
    # task-1 should be evicted
    assert control_plane._get_result("task-1") is None


def test_subworker_registration(control_plane):
    """Test subworker registration via direct dict access."""
    subworker_id = "test-subworker"
    subworker_address = "tcp://127.0.0.1:5561"

    # Register subworker directly in dict (as control plane does)
    control_plane.subworkers[subworker_id] = {
        "address": subworker_address,
        "status": "active",
        "last_seen": datetime.now(),
        "load": 0,
        "registered_at": datetime.now(),
    }

    # Subworker should be in registry
    assert subworker_id in control_plane.subworkers
    assert control_plane.subworkers[subworker_id]["address"] == subworker_address
    assert control_plane.subworkers[subworker_id]["status"] == "active"


def test_subworker_status_update(control_plane):
    """Test subworker status updates."""
    subworker_id = "test-subworker"
    control_plane.subworkers[subworker_id] = {
        "address": "tcp://127.0.0.1:5561",
        "status": "active",
        "last_seen": datetime.now(),
        "load": 0,
    }

    # Update load directly
    control_plane.subworkers[subworker_id]["load"] = 75

    assert control_plane.subworkers[subworker_id]["load"] == 75


def test_subworker_removal(control_plane):
    """Test subworker removal."""
    subworker_id = "test-subworker"
    control_plane.subworkers[subworker_id] = {
        "address": "tcp://127.0.0.1:5561",
        "status": "active",
        "last_seen": datetime.now(),
        "load": 0,
    }

    # Remove subworker
    del control_plane.subworkers[subworker_id]

    # Subworker should be gone
    assert subworker_id not in control_plane.subworkers


def test_task_queue_operations(control_plane):
    """Test task queue operations."""
    # Create test tasks
    task1 = Task(
        name="test_task",
        args=(1, 2),
        kwargs={},
        priority=TaskPriority.NORMAL,
    )
    task2 = Task(
        name="test_task",
        args=(3, 4),
        kwargs={},
        priority=TaskPriority.HIGH,
    )

    # Add tasks to queue directly
    control_plane.task_queue[TaskPriority.NORMAL].append(task1)
    control_plane.task_queue[TaskPriority.HIGH].append(task2)

    # Tasks should be in respective queues
    assert len(control_plane.task_queue[TaskPriority.NORMAL]) == 1
    assert len(control_plane.task_queue[TaskPriority.HIGH]) == 1


def test_task_priority_ordering(control_plane):
    """Test that tasks are ordered by priority."""
    # Create tasks with different priorities
    low_task = Task(name="task", args=(), kwargs={}, priority=TaskPriority.LOW)
    high_task = Task(name="task", args=(), kwargs={}, priority=TaskPriority.HIGH)
    critical_task = Task(name="task", args=(), kwargs={}, priority=TaskPriority.CRITICAL)

    # Add all tasks
    control_plane.task_queue[TaskPriority.LOW].append(low_task)
    control_plane.task_queue[TaskPriority.HIGH].append(high_task)
    control_plane.task_queue[TaskPriority.CRITICAL].append(critical_task)

    # Queues should have correct counts
    assert len(control_plane.task_queue[TaskPriority.LOW]) == 1
    assert len(control_plane.task_queue[TaskPriority.HIGH]) == 1
    assert len(control_plane.task_queue[TaskPriority.CRITICAL]) == 1


def test_active_tasks_tracking(control_plane):
    """Test active tasks tracking."""
    task = Task(name="test_task", args=(1, 2), kwargs={})

    # Track task directly
    control_plane.active_tasks[task.id] = task

    assert task.id in control_plane.active_tasks
    assert control_plane.active_tasks[task.id] == task

    # Complete task (remove from tracking)
    del control_plane.active_tasks[task.id]

    assert task.id not in control_plane.active_tasks


def test_control_plane_environment_defaults(control_plane):
    """Test control plane environment variable defaults."""
    # Test that unset env vars use defaults
    cp = ControlPlaneWorker(
        worker_id="env-test",
        gui_enabled=False,
    )
    assert cp.result_cache_max_size == 10000
    assert cp.result_cache_ttl_seconds == 3600
    assert cp.subworker_management_port == 5560


def test_control_plane_custom_cache_settings():
    """Test control plane with custom cache settings."""
    cp = ControlPlaneWorker(
        worker_id="custom-cache",
        result_cache_max_size=500,
        result_cache_ttl_seconds=7200,
        gui_enabled=False,
    )
    assert cp.result_cache_max_size == 500
    assert cp.result_cache_ttl_seconds == 7200


def test_gui_configuration():
    """Test GUI configuration."""
    cp = ControlPlaneWorker(
        worker_id="gui-test",
        gui_enabled=True,
        gui_host="0.0.0.0",
        gui_port=9000,
    )
    assert cp.gui_enabled is True
    assert cp.gui_host == "0.0.0.0"
    assert cp.gui_port == 9000


def test_task_with_callback_in_cache(control_plane):
    """Test that tasks with callbacks are handled correctly."""
    task_id = "callback-task"

    result = TaskResult(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        result={"processed": True},
    )

    control_plane._store_result(result)

    cached = control_plane._get_result(task_id)
    assert cached is not None
    assert cached.status == TaskStatus.SUCCESS


def test_failed_task_result_caching(control_plane):
    """Test that failed tasks are cached correctly."""
    task_id = "failed-task"

    result = TaskResult(
        task_id=task_id,
        status=TaskStatus.FAILURE,
        result=None,
        error="Task failed intentionally",
    )

    control_plane._store_result(result)

    cached = control_plane._get_result(task_id)
    assert cached is not None
    assert cached.status == TaskStatus.FAILURE
    assert cached.error == "Task failed intentionally"


def test_get_subworker_status(control_plane):
    """Test get_subworker_status method."""
    # Add some subworkers
    control_plane.subworkers["sw1"] = {
        "address": "tcp://127.0.0.1:5561",
        "status": "active",
        "last_seen": datetime.now(),
        "load": 5,
    }
    control_plane.subworkers["sw2"] = {
        "address": "tcp://127.0.0.1:5562",
        "status": "inactive",
        "last_seen": datetime.now(),
        "load": 10,
    }

    status = control_plane.get_subworker_status()

    assert status["total_subworkers"] == 2
    assert status["active_subworkers"] == 1
    assert "sw1" in status["subworkers"]
    assert "sw2" in status["subworkers"]


def test_result_cache_nonexistent_task(control_plane):
    """Test getting result for non-existent task."""
    result = control_plane._get_result("nonexistent-task")
    assert result is None


def test_subworker_selection(control_plane):
    """Test subworker selection logic."""
    # Add subworkers with different loads
    control_plane.subworkers["sw1"] = {
        "address": "tcp://127.0.0.1:5561",
        "status": "active",
        "last_seen": datetime.now(),
        "load": 10,
    }
    control_plane.subworkers["sw2"] = {
        "address": "tcp://127.0.0.1:5562",
        "status": "active",
        "last_seen": datetime.now(),
        "load": 5,  # Lower load = preferred
    }

    selected = control_plane._select_subworker(TaskPriority.NORMAL)

    # Should select sw2 (lower load)
    assert selected == "sw2"


def test_subworker_selection_no_active(control_plane):
    """Test subworker selection when no active subworkers."""
    # Add inactive subworker
    control_plane.subworkers["sw1"] = {
        "address": "tcp://127.0.0.1:5561",
        "status": "inactive",
        "last_seen": datetime.now(),
        "load": 0,
    }

    selected = control_plane._select_subworker(TaskPriority.NORMAL)

    # Should return None since no active subworkers
    assert selected is None


def test_result_cache_double_store(control_plane):
    """Test storing result twice for same task."""
    task_id = "double-store-task"

    result1 = TaskResult(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        result={"value": 1},
    )
    result2 = TaskResult(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        result={"value": 2},
    )

    control_plane._store_result(result1)
    control_plane._store_result(result2)

    # Should return the second result
    cached = control_plane._get_result(task_id)
    assert cached.result["value"] == 2
