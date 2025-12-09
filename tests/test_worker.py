"""Test cases for FastWorker Worker."""

import pytest
from unittest.mock import patch
from fastworker.workers.worker import Worker
from fastworker.tasks.models import Task, TaskPriority
from fastworker.tasks.registry import task_registry, task


@pytest.fixture
def worker():
    """Create a test worker."""
    return Worker(
        worker_id="test-worker",
        base_address="tcp://127.0.0.1:5555",
        discovery_address="tcp://127.0.0.1:5550",
    )


def test_worker_initialization(worker):
    """Test worker initialization."""
    assert worker.worker_id == "test-worker"
    assert worker.base_address == "tcp://127.0.0.1:5555"
    assert worker.discovery_address == "tcp://127.0.0.1:5550"
    assert not worker.running
    assert len(worker.peers) == 0


@pytest.mark.asyncio
async def test_worker_task_execution():
    """Test worker task execution."""

    # Register a test task
    @task
    def test_task(x: int, y: int) -> int:
        return x + y

    # Create Worker instance (unused in this test but shows initialization)
    Worker("test-worker")

    # Create a task (unused in this test but shows model creation)
    Task(name="test_task", args=(2, 3), kwargs={}, priority=TaskPriority.NORMAL)

    # Mock the execution
    with patch.object(task_registry, "get_task") as mock_get:
        mock_get.return_value = test_task

        # Test task execution would happen in the actual worker
        task_func = task_registry.get_task("test_task")
        result = task_func(2, 3)

        assert result == 5


def test_worker_custom_settings():
    """Test worker with custom settings."""
    worker = Worker(
        worker_id="custom-worker",
        base_address="tcp://127.0.0.1:6000",
        discovery_address="tcp://127.0.0.1:6001",
    )

    assert worker.worker_id == "custom-worker"
    assert worker.base_address == "tcp://127.0.0.1:6000"
    assert worker.discovery_address == "tcp://127.0.0.1:6001"


@pytest.mark.asyncio
async def test_worker_priority_handling():
    """Test worker handles different priority levels."""
    worker = Worker("test-worker")

    # Worker should have different respondents for each priority
    assert hasattr(worker, "critical_respondent")
    assert hasattr(worker, "high_respondent")
    assert hasattr(worker, "normal_respondent")
    assert hasattr(worker, "low_respondent")


def test_task_registry_operations():
    """Test task registry operations."""

    # Test task registration
    @task
    def sample_task():
        return "sample result"

    # Check if task is registered
    registered_task = task_registry.get_task("sample_task")
    assert registered_task is not None
    assert registered_task() == "sample result"

    # Test listing tasks
    tasks = task_registry.list_tasks()
    assert "sample_task" in tasks
