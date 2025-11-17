"""Test cases for FastWorker Client."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastworker.clients.client import Client
from fastworker.tasks.models import Task, TaskPriority, TaskResult, TaskStatus


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
    with patch.object(Client, '_listen_for_workers') as mock_listen:
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
    """Test submitting task when no workers are available."""
    client = Client()
    await client.start()

    result = await client.submit_task("test_task", (), {}, TaskPriority.NORMAL)

    assert result.status == TaskStatus.FAILURE
    assert "No workers available" in result.error

    client.stop()


@pytest.mark.asyncio
async def test_delay_method():
    """Test delay method interface."""
    client = Client()
    client.workers.add(("worker1", "tcp://127.0.0.1:5555"))

    with patch.object(client, 'submit_task') as mock_submit:
        mock_submit.return_value = TaskResult(
            task_id="test-id",
            status=TaskStatus.SUCCESS,
            result="success"
        )

        result = await client.delay("test_task", "arg1", "arg2", priority=TaskPriority.HIGH)

        mock_submit.assert_called_once_with(
            "test_task",
            ("arg1", "arg2"),
            {},
            TaskPriority.HIGH
        )
        assert result.status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_custom_client_settings():
    """Test client with custom settings."""
    client = Client(
        discovery_address="tcp://127.0.0.1:6000",
        timeout=60,
        retries=5
    )

    assert client.discovery_address == "tcp://127.0.0.1:6000"
    assert client.timeout == 60
    assert client.retries == 5