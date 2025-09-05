"""Task registry for FastQueue."""
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class TaskRegistry:
    """Registry for task functions."""
    
    def __init__(self):
        self._tasks: Dict[str, Callable] = {}
    
    def register(self, func: Callable, name: Optional[str] = None) -> Callable:
        """Register a function as a task."""
        task_name = name or func.__name__
        
        if task_name in self._tasks:
            logger.warning(f"Task {task_name} is already registered. Overwriting.")
        
        self._tasks[task_name] = func
        logger.info(f"Registered task: {task_name}")
        return func
    
    def get_task(self, name: str) -> Optional[Callable]:
        """Get a registered task by name."""
        return self._tasks.get(name)
    
    def list_tasks(self) -> Dict[str, Callable]:
        """List all registered tasks."""
        return self._tasks.copy()

# Global task registry
task_registry = TaskRegistry()

def task(func_or_name=None):
    """Decorator to register a function as a task."""
    def decorator(func: Callable) -> Callable:
        task_name = func.__name__
        task_registry.register(func, task_name)
        return func
    
    # Check if called as @task or @task(name="...")
    if callable(func_or_name):
        # Called as @task
        return decorator(func_or_name)
    else:
        # Called as @task(name="...")
        def named_decorator(func: Callable) -> Callable:
            task_name = func_or_name or func.__name__
            task_registry.register(func, task_name)
            return func
        return named_decorator