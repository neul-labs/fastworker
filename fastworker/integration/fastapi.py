"""FastAPI-native integration for FastWorker.

Provides a FastWorker wrapper that feels like a built-in FastAPI feature.

Usage:
    from fastapi import FastAPI
    from fastworker.integration.fastapi import FastWorker

    app = FastAPI()
    fw = FastWorker(app)

    @app.post("/send")
    async def send_email(to: str):
        return {"task_id": await fw.delay("send_email", to)}
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastworker.clients.client import Client
from fastworker.tasks.models import TaskPriority, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class FastWorker:
    """FastAPI-native integration for FastWorker task queue.

    Handles Client lifecycle automatically via FastAPI's lifespan.
    Delegates all task operations to the internal Client.

    Usage:
        app = FastAPI()
        fw = FastWorker(app)
        task_id = await fw.delay("my_task", arg1, arg2)

    Advanced:
        fw = FastWorker(app, client_kwargs={"timeout": 60, "retries": 5})
        fw.client  # raw Client access for submit_batch/cancel_task
        fw.worker_count  # health check helper
    """

    def __init__(
        self,
        app: Any,
        *,
        client_kwargs: Optional[dict] = None,
    ):
        """Initialize FastWorker and attach to a FastAPI application.

        Args:
            app: FastAPI application instance.
            client_kwargs: Keyword arguments passed to Client() constructor.
        """
        self._app = app
        self.client = Client(**(client_kwargs or {}))
        self._register_lifespan()

    def _register_lifespan(self):
        """Register or wrap the FastAPI lifespan to manage Client lifecycle."""
        existing = self._app.router.lifespan_context

        client = self.client

        @asynccontextmanager
        async def combined_lifespan(app):
            if existing is not None:
                async with existing(app) as state:
                    await client.start()
                    try:
                        yield state
                    finally:
                        client.stop()
            else:
                await client.start()
                try:
                    yield
                finally:
                    client.stop()

        self._app.router.lifespan_context = combined_lifespan

    # -- Property helpers --

    @property
    def worker_count(self) -> int:
        """Number of discovered workers. Use for health checks."""
        return len(self.client.workers)

    # -- Delegated methods --

    async def delay(
        self,
        task_name: str,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        eta: Optional[Any] = None,
        countdown: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Submit a task non-blocking, return task ID immediately."""
        return await self.client.delay(
            task_name,
            *args,
            priority=priority,
            eta=eta,
            countdown=countdown,
            **kwargs,
        )

    async def submit_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        eta: Optional[Any] = None,
        countdown: Optional[float] = None,
    ) -> TaskResult:
        """Submit a task and wait for result (blocking)."""
        return await self.client.submit_task(
            task_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            eta=eta,
            countdown=countdown,
        )

    async def delay_with_callback(
        self,
        task_name: str,
        callback_address: str,
        *args,
        callback_data: Optional[dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        eta: Optional[Any] = None,
        countdown: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Submit a task with callback, non-blocking."""
        return await self.client.delay_with_callback(
            task_name,
            callback_address,
            *args,
            callback_data=callback_data,
            priority=priority,
            eta=eta,
            countdown=countdown,
            **kwargs,
        )

    async def submit_batch(
        self,
        tasks: list,
        default_priority: TaskPriority = TaskPriority.NORMAL,
    ) -> list[str]:
        """Submit multiple tasks atomically."""
        return await self.client.submit_batch(
            tasks,
            default_priority=default_priority,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID."""
        return await self.client.cancel_task(task_id)

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Query task result from control plane's result cache."""
        return await self.client.get_task_result(task_id)

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result from local cache."""
        return self.client.get_result(task_id)

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status by task ID."""
        return self.client.get_status(task_id)

    def __getattr__(self, name: str):
        """Fall through to client for unhandled attributes."""
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.client, name)
