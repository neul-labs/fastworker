"""Worker implementation for FastWorker."""

import asyncio
import logging
import os
import signal
from datetime import datetime
from urllib.parse import urlparse

from fastworker.patterns.nng_patterns import (
    BusPattern,
    PairPattern,
    SurveyorRespondentPattern,
)
from fastworker.tasks.models import (
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
)
from fastworker.tasks.registry import task_registry
from fastworker.tasks.serializer import SerializationFormat, TaskSerializer
from fastworker.telemetry.metrics import record_task_metric
from fastworker.telemetry.tracer import trace_operation
from fastworker.workers.state import WorkerState, WorkerStateMachine

logger = logging.getLogger(__name__)

DEFAULT_TASK_TIMEOUT = 300.0  # 5 minutes
DEFAULT_SHUTDOWN_TIMEOUT = 30.0  # 30 seconds for graceful drain


class Worker:
    """Worker that executes tasks using nng patterns with built-in service discovery."""

    def __init__(
        self,
        worker_id: str,
        base_address: str = "tcp://127.0.0.1:5555",
        discovery_address: str = "tcp://127.0.0.1:5550",
        serialization_format: SerializationFormat = SerializationFormat.JSON,
        task_timeout: float = DEFAULT_TASK_TIMEOUT,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
        concurrency: int = 1,
    ):
        self.worker_id = worker_id
        self.base_address = base_address
        self.discovery_address = discovery_address
        self.serialization_format = serialization_format
        self.task_timeout = task_timeout
        self.shutdown_timeout = shutdown_timeout
        self.concurrency = concurrency or int(os.getenv("FASTWORKER_WORKER_CONCURRENCY", "1"))
        self.shutdown_event = asyncio.Event()

        # Worker lifecycle state machine
        self.lifecycle = WorkerStateMachine()

        # Concurrency limiter
        self._concurrency_semaphore = asyncio.Semaphore(self.concurrency)

        # Track in-flight tasks for graceful shutdown
        self._active_tasks: set[asyncio.Task] = set()

        # Parse base address to extract host and port
        parsed = urlparse(base_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"

        # Create addresses for different priorities using different ports
        priority_ports = {
            "critical": base_port,
            "high": base_port + 1,
            "normal": base_port + 2,
            "low": base_port + 3,
        }

        # Create patterns for different priorities - workers LISTEN
        self.critical_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['critical']}", is_surveyor=False
        )
        self.high_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['high']}", is_surveyor=False
        )
        self.normal_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['normal']}", is_surveyor=False
        )
        self.low_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['low']}", is_surveyor=False
        )

        # Built-in service discovery bus
        self.discovery_bus = BusPattern(discovery_address, listen=True)
        self.peers = set()

    @property
    def running(self) -> bool:
        """Backward-compat: True when worker is RUNNING or DRAINING."""
        return self.lifecycle.state in (WorkerState.RUNNING, WorkerState.DRAINING)

    async def start(self):
        """Start the worker with built-in service discovery."""
        logger.info(f"Starting worker {self.worker_id}")

        # Transition INIT → STARTING
        if not await self.lifecycle.start():
            logger.error(f"Worker {self.worker_id} failed to transition from INIT")
            return

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)

        try:
            # Start service discovery bus
            await self.discovery_bus.start()

            # Announce self to network
            await self._announce_presence()

            # Start listening for peer announcements
            asyncio.create_task(self._listen_for_peers())

            # Start all respondents
            await self.critical_respondent.start()
            await self.high_respondent.start()
            await self.normal_respondent.start()
            await self.low_respondent.start()

        except Exception as e:
            logger.error(f"Failed to start worker {self.worker_id}: {e}")
            await self.lifecycle.fail_start()
            await self._do_force_stop()
            return

        # Transition STARTING → RUNNING
        if not await self.lifecycle.ready():
            logger.error(f"Worker {self.worker_id} failed to become ready")
            await self._do_force_stop()
            return

        logger.info(f"Worker {self.worker_id} started with built-in discovery")

        # Start processing tasks for each priority
        task_runners = [
            asyncio.create_task(
                self._process_tasks(self.critical_respondent, TaskPriority.CRITICAL)
            ),
            asyncio.create_task(self._process_tasks(self.high_respondent, TaskPriority.HIGH)),
            asyncio.create_task(self._process_tasks(self.normal_respondent, TaskPriority.NORMAL)),
            asyncio.create_task(self._process_tasks(self.low_respondent, TaskPriority.LOW)),
        ]

        # Wait for shutdown signal
        await self.shutdown_event.wait()

        # Begin graceful shutdown: RUNNING → DRAINING
        logger.info(f"Worker {self.worker_id} draining — finishing in-flight tasks")
        await self.lifecycle.drain()

        # Wait for active tasks to complete (with timeout)
        if self._active_tasks:
            logger.info(
                f"Waiting up to {self.shutdown_timeout}s for "
                f"{len(self._active_tasks)} in-flight tasks"
            )
            done, pending = await asyncio.wait(self._active_tasks, timeout=self.shutdown_timeout)
            for t in pending:
                logger.warning("Cancelling in-flight task during shutdown")
                t.cancel()

        # Cancel the task runner loops
        for t in task_runners:
            t.cancel()

        await self._do_force_stop()

    async def _do_force_stop(self):
        """Close all sockets and transition to STOPPED."""
        await self.lifecycle.force_stop()
        self._close_sockets()
        await self.lifecycle.complete_stop()
        logger.info(f"Worker {self.worker_id} stopped")

    def _close_sockets(self):
        """Close all socket patterns."""
        self.critical_respondent.close()
        self.high_respondent.close()
        self.normal_respondent.close()
        self.low_respondent.close()
        self.discovery_bus.close()

    async def _announce_presence(self):
        """Announce worker presence to network."""
        await self.discovery_bus.send(
            f"WORKER_ANNOUNCE:{self.worker_id}:{self.base_address}".encode()
        )

    async def _listen_for_peers(self):
        """Listen for peer announcements."""
        while self.running:
            try:
                data = await self.discovery_bus.recv()
                message = data.decode()

                if message.startswith("WORKER_ANNOUNCE:"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        peer_id = parts[1]
                        peer_address = parts[2]
                        self.peers.add((peer_id, peer_address))
                        logger.info(f"Discovered peer worker: {peer_id} at {peer_address}")

            except Exception as e:
                if self.running:
                    logger.error(f"Error in peer discovery: {e}")

    def _signal_handler(self, sig):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, shutting down worker {self.worker_id}")
        self.shutdown_event.set()

    async def _process_tasks(self, respondent, priority: TaskPriority):
        """Process tasks for a specific priority."""
        while self.lifecycle.state == WorkerState.RUNNING:
            try:
                # Receive task
                data = await respondent.recv()
                task_data = TaskSerializer.deserialize(data, self.serialization_format)

                # Create task object
                task = Task(**task_data)
                logger.info(
                    f"Worker {self.worker_id} received {priority} task {task.id} ({task.name})"
                )

                # Spawn execution as a tracked task
                exec_task = asyncio.create_task(self._execute_and_respond(task, respondent))
                self._active_tasks.add(exec_task)
                exec_task.add_done_callback(self._active_tasks.discard)

            except Exception as e:
                if self.lifecycle.state == WorkerState.RUNNING:
                    logger.error(
                        f"Error processing {priority} task in worker {self.worker_id}: {e}"
                    )

    async def _execute_and_respond(self, task: Task, respondent) -> None:
        """Execute a task and send the result back."""
        async with self._concurrency_semaphore:
            result = await self._execute_task(task)
        result_data = TaskSerializer.serialize(result.model_dump(), self.serialization_format)
        await respondent.send(result_data)

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a task with timeout and cancellation enforcement."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        timeout = task.timeout or self.task_timeout

        with trace_operation(
            "worker.execute_task",
            attributes={
                "task.id": task.id,
                "task.name": task.name,
                "task.priority": task.priority.value,
                "worker.id": self.worker_id,
            },
        ):
            try:
                task_info = task_registry.get_task_info(task.name)
                if not task_info:
                    raise ValueError(f"Task {task.name} not found")

                func = task_info.func

                # Check cancellation before execution
                cancel_event = getattr(task, "_cancel_event", None)
                if cancel_event and cancel_event.is_set():
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.CANCELLED,
                        error="Task cancelled before execution",
                        started_at=task.started_at,
                        completed_at=datetime.now(),
                    )

                # Run before hook
                if task_info.before:
                    if asyncio.iscoroutinefunction(task_info.before):
                        await task_info.before(task)
                    else:
                        task_info.before(task)

                # Execute with timeout
                if asyncio.iscoroutinefunction(func):
                    result_value = await asyncio.wait_for(
                        func(*task.args, **task.kwargs), timeout=timeout
                    )
                else:
                    result_value = await asyncio.wait_for(
                        asyncio.to_thread(func, *task.args, **task.kwargs),
                        timeout=timeout,
                    )

                # Run after hook
                if task_info.after:
                    if asyncio.iscoroutinefunction(task_info.after):
                        await task_info.after(task)
                    else:
                        task_info.after(task)

                # Check cancellation after execution
                if cancel_event and cancel_event.is_set():
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.CANCELLED,
                        error="Task cancelled after execution",
                        started_at=task.started_at,
                        completed_at=datetime.now(),
                    )

                completed_at = datetime.now()
                duration_ms = (completed_at - task.started_at).total_seconds() * 1000

                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.SUCCESS,
                    result=result_value,
                    started_at=task.started_at,
                    completed_at=completed_at,
                    callback=task.callback,
                )

                logger.info(f"Task {task.id} completed successfully in {duration_ms:.2f}ms")

                record_task_metric(
                    "completed",
                    task.name,
                    priority=task.priority.value,
                    worker_id=self.worker_id,
                    duration_ms=duration_ms,
                )

                if task.callback:
                    await self._send_callback(task_result)

                return task_result

            except asyncio.TimeoutError:
                completed_at = datetime.now()
                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILURE,
                    error=f"Task timed out after {timeout}s",
                    started_at=task.started_at,
                    completed_at=completed_at,
                    callback=task.callback,
                )
                logger.error(f"Task {task.id} timed out after {timeout}s")
                record_task_metric(
                    "failed",
                    task.name,
                    priority=task.priority.value,
                    worker_id=self.worker_id,
                )
                return task_result

            except Exception as e:
                completed_at = datetime.now()
                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILURE,
                    error=str(e),
                    started_at=task.started_at,
                    completed_at=completed_at,
                    callback=task.callback,
                )
                logger.error(f"Task {task.id} failed: {e}")

                record_task_metric(
                    "failed",
                    task.name,
                    priority=task.priority.value,
                    worker_id=self.worker_id,
                )

                if task.callback:
                    await self._send_callback(task_result)

                return task_result

    async def _send_callback(self, task_result: TaskResult):
        """Send callback notification when task is completed."""
        if not task_result.callback:
            return

        try:
            callback_socket = PairPattern(task_result.callback.address, is_server=False)
            await callback_socket.start()

            try:
                callback_data = {
                    "task_id": task_result.task_id,
                    "status": task_result.status.value,
                    "result": task_result.result,
                    "error": task_result.error,
                    "started_at": (
                        task_result.started_at.isoformat() if task_result.started_at else None
                    ),
                    "completed_at": (
                        task_result.completed_at.isoformat() if task_result.completed_at else None
                    ),
                    "callback_data": task_result.callback.data,
                }

                serialized_data = TaskSerializer.serialize(callback_data, self.serialization_format)
                await callback_socket.send(serialized_data)

                logger.info(
                    f"Callback sent for task {task_result.task_id} "
                    f"to {task_result.callback.address}"
                )
            finally:
                callback_socket.close()

        except Exception as e:
            logger.error(f"Failed to send callback for task {task_result.task_id}: {e}")

    def stop(self):
        """Stop the worker — initiates drain then force stop."""
        logger.info(f"Stopping worker {self.worker_id}")
        self.shutdown_event.set()
