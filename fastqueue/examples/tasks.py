"""Example tasks for FastQueue."""
import asyncio
import time
from fastqueue.tasks.registry import task

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

@task
def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y

@task
async def async_add(x: int, y: int) -> int:
    """Async add two numbers."""
    await asyncio.sleep(0.1)  # Simulate async work
    return x + y

@task
def slow_task(seconds: int) -> str:
    """A slow task."""
    time.sleep(seconds)
    return f"Slept for {seconds} seconds"

@task
def divide(x: int, y: int) -> float:
    """Divide two numbers."""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y