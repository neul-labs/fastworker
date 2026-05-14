"""Task hooks and middleware protocol for extending FastWorker."""

from __future__ import annotations

from typing import Any, Optional, Protocol


class TaskContext:
    """Context passed to task hooks with task metadata."""

    def __init__(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: dict,
        worker_id: Optional[str] = None,
    ):
        self.task_id = task_id
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.worker_id = worker_id
        self.started_at: Optional[Any] = None
        self.completed_at: Optional[Any] = None
        self.status: Optional[str] = None
        self.result: Any = None
        self.error: Optional[str] = None


class TaskHook(Protocol):
    """Protocol for task hooks — before/after/on_error callbacks."""

    async def before(self, ctx: TaskContext) -> None: ...

    async def after(self, ctx: TaskContext) -> None: ...

    async def on_error(self, ctx: TaskContext, error: Exception) -> None: ...
