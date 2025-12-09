"""Test cases for FastWorker models."""

import uuid
from datetime import datetime
from fastworker.tasks.models import (
    Task,
    TaskPriority,
    TaskStatus,
    TaskResult,
    CallbackInfo,
)


def test_task_priority_enum():
    """Test TaskPriority enum values."""
    assert TaskPriority.CRITICAL.value == "critical"
    assert TaskPriority.HIGH.value == "high"
    assert TaskPriority.NORMAL.value == "normal"
    assert TaskPriority.LOW.value == "low"


def test_task_status_enum():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.STARTED.value == "started"
    assert TaskStatus.SUCCESS.value == "success"
    assert TaskStatus.FAILURE.value == "failure"


def test_task_creation():
    """Test Task model creation."""
    task = Task(
        name="test_task",
        args=(1, 2, 3),
        kwargs={"key": "value"},
        priority=TaskPriority.HIGH,
    )

    assert task.name == "test_task"
    assert task.args == (1, 2, 3)
    assert task.kwargs == {"key": "value"}
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert isinstance(task.id, str)
    assert isinstance(task.created_at, datetime)


def test_task_with_callback():
    """Test Task creation with callback."""
    callback_info = CallbackInfo(address="tcp://127.0.0.1:5570", data={"test": "data"})

    task = Task(name="callback_task", args=(), kwargs={}, callback=callback_info)

    assert task.callback is not None
    assert task.callback.address == "tcp://127.0.0.1:5570"
    assert task.callback.data == {"test": "data"}


def test_task_result_success():
    """Test TaskResult for successful execution."""
    result = TaskResult(
        task_id="test-task-id",
        status=TaskStatus.SUCCESS,
        result="Task completed successfully",
    )

    assert result.task_id == "test-task-id"
    assert result.status == TaskStatus.SUCCESS
    assert result.result == "Task completed successfully"
    assert result.error is None
    # completed_at is optional and not set by default
    assert result.completed_at is None


def test_task_result_failure():
    """Test TaskResult for failed execution."""
    result = TaskResult(
        task_id="test-task-id", status=TaskStatus.FAILURE, error="Task execution failed"
    )

    assert result.task_id == "test-task-id"
    assert result.status == TaskStatus.FAILURE
    assert result.error == "Task execution failed"
    assert result.result is None


def test_callback_info():
    """Test CallbackInfo model."""
    callback = CallbackInfo(
        address="tcp://127.0.0.1:5570", data={"user_id": 123, "action": "notification"}
    )

    assert callback.address == "tcp://127.0.0.1:5570"
    assert callback.data == {"user_id": 123, "action": "notification"}


def test_task_defaults():
    """Test Task model with default values."""
    task = Task(name="simple_task")

    assert task.name == "simple_task"
    assert task.args == ()
    assert task.kwargs == {}
    assert task.priority == TaskPriority.NORMAL
    assert task.status == TaskStatus.PENDING
    assert task.callback is None
    # Task doesn't have retries field in the current model


def test_task_with_custom_id():
    """Test Task creation with custom ID."""
    custom_id = str(uuid.uuid4())
    task = Task(name="test_task", id=custom_id)

    assert task.id == custom_id


def test_task_serialization():
    """Test Task model can be converted to dict."""
    task = Task(
        name="serialize_task",
        args=(1, 2),
        kwargs={"key": "value"},
        priority=TaskPriority.HIGH,
    )

    task_dict = task.model_dump()

    assert isinstance(task_dict, dict)
    assert task_dict["name"] == "serialize_task"
    assert task_dict["args"] == (1, 2)
    assert task_dict["kwargs"] == {"key": "value"}
    assert task_dict["priority"] == TaskPriority.HIGH
