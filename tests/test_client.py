"""Test cases for FastWorker Client."""

import pytest
from unittest.mock import patch
from fastworker.clients.client import Client
from fastworker.tasks.models import TaskPriority, TaskStatus


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = Client()
    assert client.discovery_address == "tcp://127.0.0.1:5550"
    assert client.timeout == 30
    assert client.retries == 3
    assert not client.running
    assert len(client.workers) == 0


@pytest.mark.asyncio
async def test_client_start():
    """Test client start functionality."""
    with patch.object(Client, "_listen_for_workers") as mock_listen:
        client = Client()
        await client.start()

        assert client.running
        mock_listen.assert_called_once()


@pytest.mark.asyncio
async def test_client_stop():
    """Test client stop functionality."""
    client = Client()
    await client.start()
    client.stop()

    assert not client.running


@pytest.mark.asyncio
async def test_worker_discovery():
    """Test worker discovery functionality."""
    client = Client()

    # Simulate receiving worker announcement
    client.workers.add(("worker1", "tcp://127.0.0.1:5555"))

    assert len(client.workers) == 1
    assert ("worker1", "tcp://127.0.0.1:5555") in client.workers


@pytest.mark.asyncio
async def test_submit_task_no_workers():
    """Test submitting task when no workers are available - task is queued."""
    client = Client()
    # Don't start client - it would try to connect to discovery

    # Manually set running flag and empty workers
    client.running = True
    client.workers = set()

    # When no workers are available, task is queued and returned with PENDING status
    result = await client.submit_task("test_task", (), {}, TaskPriority.NORMAL)

    # Task should be pending (queued) when no workers are available
    assert result.status == TaskStatus.PENDING
    # The task should be in the pending tasks queue
    assert len(client.pending_tasks) == 1


@pytest.mark.asyncio
async def test_delay_method():
    """Test delay method interface."""
    client = Client()
    client.running = True
    client.workers.add(("worker1", "tcp://127.0.0.1:5555"))

    # delay() returns a task ID (string), not a TaskResult
    # It creates the task and submits it in the background
    task_id = await client.delay(
        "test_task", "arg1", "arg2", priority=TaskPriority.HIGH
    )

    # task_id should be a non-empty string
    assert isinstance(task_id, str)
    assert len(task_id) > 0

    # The result should be stored in task_results with PENDING status
    assert task_id in client.task_results
    result = client.task_results[task_id]
    assert result.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_custom_client_settings():
    """Test client with custom settings."""
    client = Client(discovery_address="tcp://127.0.0.1:6000", timeout=60, retries=5)

    assert client.discovery_address == "tcp://127.0.0.1:6000"
    assert client.timeout == 60
    assert client.retries == 5
