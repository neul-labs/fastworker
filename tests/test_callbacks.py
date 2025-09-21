"""Test cases for FastQueue callbacks."""
import asyncio
import pytest
from fastqueue.tasks.models import Task, TaskPriority, CallbackInfo
from fastqueue.clients.client import Client
from fastqueue.workers.worker import Worker
from fastqueue.patterns.nng_patterns import PairPattern
from fastqueue.tasks.registry import task
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat

# Define a test task
@task
def echo_task(message: str) -> str:
    """Echo a message."""
    return f"Echo: {message}"

@pytest.mark.asyncio
async def test_callback_model():
    """Test callback model creation."""
    callback_info = CallbackInfo(
        address="tcp://127.0.0.1:5570",
        data={"test": "data"}
    )
    
    assert callback_info.address == "tcp://127.0.0.1:5570"
    assert callback_info.data == {"test": "data"}

def test_task_with_callback():
    """Test task creation with callback."""
    callback_info = CallbackInfo(
        address="tcp://127.0.0.1:5570",
        data={"test": "data"}
    )
    
    task = Task(
        name="echo_task",
        args=("Hello",),
        callback=callback_info
    )
    
    assert task.name == "echo_task"
    assert task.args == ("Hello",)
    assert task.callback is not None
    assert task.callback.address == "tcp://127.0.0.1:5570"
    assert task.callback.data == {"test": "data"}