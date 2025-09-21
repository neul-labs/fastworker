"""Test cases for FastQueue."""
import pytest
from fastqueue.tasks.registry import task_registry, task
from fastqueue.tasks.models import Task, TaskPriority

@pytest.fixture
def sample_task_obj():
    """Create a sample task object."""
    return Task(
        name="sample_task",
        args=(2, 3),
        kwargs={},
        priority=TaskPriority.NORMAL
    )

def test_task_registry():
    """Test task registry functionality."""
    # Register a task
    @task
    def test_func():
        return "test"
    
    # Check if task is registered
    registered_func = task_registry.get_task("test_func")
    assert registered_func is not None
    assert registered_func() == "test"

def test_task_model(sample_task_obj):
    """Test task model."""
    assert sample_task_obj.name == "sample_task"
    assert sample_task_obj.args == (2, 3)
    assert sample_task_obj.priority == TaskPriority.NORMAL
    assert sample_task_obj.id is not None