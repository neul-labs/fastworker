"""Task registry for FastWorker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from fastworker.tasks.schedules import ScheduleConfig

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """Metadata about a registered task."""

    func: Callable
    name: str
    module: str = ""
    schedule: Optional[ScheduleConfig] = None
    before: Optional[Callable] = None
    after: Optional[Callable] = None


class TaskRegistry:
    """Registry for task functions."""

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        schedule: Optional[ScheduleConfig] = None,
        before: Optional[Callable] = None,
        after: Optional[Callable] = None,
    ) -> Callable:
        """Register a function as a task."""
        task_name = name or func.__name__

        if task_name in self._tasks:
            logger.warning(f"Task {task_name} is already registered. Overwriting.")

        self._tasks[task_name] = TaskInfo(
            func=func,
            name=task_name,
            module=func.__module__,
            schedule=schedule,
            before=before,
            after=after,
        )
        logger.info(f"Registered task: {task_name}")
        return func

    def get_task(self, name: str) -> Optional[Callable]:
        """Get a registered task function by name."""
        info = self._tasks.get(name)
        return info.func if info else None

    def get_task_info(self, name: str) -> Optional[TaskInfo]:
        """Get full TaskInfo for a registered task."""
        return self._tasks.get(name)

    def list_tasks(self) -> Dict[str, Callable]:
        """List all registered tasks (func only, backward compat)."""
        return {name: info.func for name, info in self._tasks.items()}

    def list_task_infos(self) -> Dict[str, TaskInfo]:
        """List all registered tasks with full metadata."""
        return self._tasks.copy()

    def get_periodic_tasks(self) -> Dict[str, TaskInfo]:
        """Get tasks that have a schedule configured."""
        return {name: info for name, info in self._tasks.items() if info.schedule is not None}


# Global task registry
task_registry = TaskRegistry()


def task(
    func_or_name=None,
    *,
    repeat_interval: Optional[float] = None,
    cron: Optional[str] = None,
    repeat_count: Optional[int] = None,
    repeat_until: Optional[str] = None,
    before: Optional[Callable] = None,
    after: Optional[Callable] = None,
):
    """Decorator to register a function as a task.

    Args:
        repeat_interval: Seconds between periodic executions.
        cron: 5-field cron expression for scheduling.
        repeat_count: Max number of executions (None = unlimited).
        repeat_until: ISO datetime string to stop repeating after.
        before: Hook called before task execution.
        after: Hook called after task execution.
    """
    from datetime import datetime as dt

    schedule = None
    if repeat_interval or cron:
        schedule = ScheduleConfig(
            repeat_interval=repeat_interval,
            cron_expression=cron,
            repeat_count=repeat_count,
            repeat_until=dt.fromisoformat(repeat_until) if repeat_until else None,
        )

    def decorator(f: Callable) -> Callable:
        task_name = f.__name__
        task_registry.register(
            f,
            task_name,
            schedule=schedule,
            before=before,
            after=after,
        )
        return f

    # Check if called as @task or @task(...)
    if callable(func_or_name):
        return decorator(func_or_name)
    else:

        def named_decorator(f: Callable) -> Callable:
            task_name = func_or_name or f.__name__
            task_registry.register(
                f,
                task_name,
                schedule=schedule,
                before=before,
                after=after,
            )
            return f

        if func_or_name is not None:
            return named_decorator
        return decorator
