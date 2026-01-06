"""Control Plane Worker implementation for FastWorker."""

import asyncio
import logging
import os
import signal
from typing import Dict, Optional, TYPE_CHECKING
from datetime import datetime
from collections import deque, OrderedDict
from urllib.parse import urlparse

from fastworker.patterns.nng_patterns import ReqRepPattern
from fastworker.tasks.models import (
    Task,
    TaskResult,
    TaskStatus,
    TaskPriority,
)
from fastworker.tasks.serializer import TaskSerializer, SerializationFormat
from fastworker.workers.worker import Worker

if TYPE_CHECKING:
    from fastworker.gui.server import ManagementServer

logger = logging.getLogger(__name__)


class ControlPlaneWorker(Worker):
    """Control plane worker that manages subworkers and also processes tasks.

    Configuration can be provided via environment variables:
    - FASTWORKER_WORKER_ID: Worker ID (default: control-plane)
    - FASTWORKER_BASE_ADDRESS: Base address (default: tcp://127.0.0.1:5555)
    - FASTWORKER_DISCOVERY_ADDRESS: Discovery address (default: tcp://..:5550)
    - FASTWORKER_SERIALIZATION_FORMAT: Serialization format (JSON or PICKLE)
    - FASTWORKER_SUBWORKER_PORT: Subworker management port (default: 5560)
    - FASTWORKER_RESULT_CACHE_SIZE: Maximum cached results (default: 10000)
    - FASTWORKER_RESULT_CACHE_TTL: Cache TTL in seconds (default: 3600)
    - FASTWORKER_GUI_ENABLED: Enable management GUI (default: true)
    - FASTWORKER_GUI_HOST: GUI server host (default: 127.0.0.1)
    - FASTWORKER_GUI_PORT: GUI server port (default: 8080)
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        base_address: Optional[str] = None,
        discovery_address: Optional[str] = None,
        serialization_format: Optional[SerializationFormat] = None,
        subworker_management_port: Optional[int] = None,
        result_cache_max_size: Optional[int] = None,
        result_cache_ttl_seconds: Optional[int] = None,
        gui_enabled: Optional[bool] = None,
        gui_host: Optional[str] = None,
        gui_port: Optional[int] = None,
    ):
        # Load from environment variables with fallback to defaults
        worker_id = worker_id or os.getenv("FASTWORKER_WORKER_ID", "control-plane")
        base_address = base_address or os.getenv(
            "FASTWORKER_BASE_ADDRESS", "tcp://127.0.0.1:5555"
        )
        discovery_address = discovery_address or os.getenv(
            "FASTWORKER_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550"
        )

        # Parse serialization format from string if needed
        if serialization_format is None:
            format_str = os.getenv("FASTWORKER_SERIALIZATION_FORMAT", "JSON").upper()
            serialization_format = (
                SerializationFormat.PICKLE
                if format_str == "PICKLE"
                else SerializationFormat.JSON
            )

        subworker_management_port = subworker_management_port or int(
            os.getenv("FASTWORKER_SUBWORKER_PORT", "5560")
        )
        result_cache_max_size = result_cache_max_size or int(
            os.getenv("FASTWORKER_RESULT_CACHE_SIZE", "10000")
        )
        result_cache_ttl_seconds = result_cache_ttl_seconds or int(
            os.getenv("FASTWORKER_RESULT_CACHE_TTL", "3600")
        )

        # GUI configuration
        if gui_enabled is None:
            gui_enabled = os.getenv("FASTWORKER_GUI_ENABLED", "true").lower() in (
                "true",
                "1",
                "yes",
            )
        self.gui_enabled = gui_enabled
        self.gui_host = gui_host or os.getenv("FASTWORKER_GUI_HOST", "127.0.0.1")
        self.gui_port = gui_port or int(os.getenv("FASTWORKER_GUI_PORT", "8080"))
        self._management_server: Optional["ManagementServer"] = None

        # Initialize base worker
        super().__init__(
            worker_id, base_address, discovery_address, serialization_format
        )

        # Override patterns to use ReqRepPattern instead of SurveyorRespondentPattern.
        # Clients use ReqRepPattern, so control plane must match.
        parsed = urlparse(base_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"

        priority_ports = {
            "critical": base_port,
            "high": base_port + 1,
            "normal": base_port + 2,
            "low": base_port + 3,
        }

        # Replace SurveyorRespondentPattern with ReqRepPattern (is_server=True means listen)
        self.critical_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['critical']}", is_server=True
        )
        self.high_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['high']}", is_server=True
        )
        self.normal_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['normal']}", is_server=True
        )
        self.low_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['low']}", is_server=True
        )

        # Control plane specific attributes
        self.subworker_management_port = subworker_management_port
        self.subworkers: Dict[str, Dict] = (
            {}
        )  # subworker_id -> {address, status, last_seen, load}
        self.task_queue: Dict[TaskPriority, deque] = {
            TaskPriority.CRITICAL: deque(),
            TaskPriority.HIGH: deque(),
            TaskPriority.NORMAL: deque(),
            TaskPriority.LOW: deque(),
        }
        self.active_tasks: Dict[str, Task] = {}  # task_id -> Task

        # Result cache with expiration and memory limits
        self.result_cache_max_size = result_cache_max_size
        self.result_cache_ttl_seconds = result_cache_ttl_seconds
        # OrderedDict for LRU eviction (most recently accessed at end)
        self.result_cache: OrderedDict[str, Dict] = OrderedDict()
        # task_id -> {result: TaskResult, stored_at: datetime, last_accessed: datetime}

        # Result query endpoint (for clients to query task results)
        result_query_port = base_port + 4  # Use port 5559
        self.result_query_server = ReqRepPattern(
            f"{scheme}://{host}:{result_query_port}", is_server=True
        )

        # Subworker management socket (for subworkers to register)
        self.subworker_registry = ReqRepPattern(
            f"{scheme}://{host}:{subworker_management_port}", is_server=True
        )

    async def start(self):
        """Start the control plane worker."""
        logger.info(f"Starting control plane worker {self.worker_id}")

        # Start management GUI if enabled
        if self.gui_enabled:
            try:
                from fastworker.gui.server import ManagementServer

                self._management_server = ManagementServer(
                    control_plane=self, host=self.gui_host, port=self.gui_port
                )
                self._management_server.start()
            except Exception as e:
                logger.warning(f"Failed to start management GUI: {e}")
                self._management_server = None

        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)

        # Start service discovery bus
        await self.discovery_bus.start()
        logger.info(f"Discovery bus started on {self.discovery_address}")

        # Start subworker registry
        await self.subworker_registry.start()
        logger.info(
            f"Subworker registry started on port {self.subworker_management_port}"
        )

        # Start result query server
        await self.result_query_server.start()
        logger.info(
            f"Result query server started on port {self.result_query_server.address}"
        )

        # Announce self to network
        await self._announce_presence()
        logger.info(
            f"Control plane announced itself: {self.worker_id} at {self.base_address}"
        )

        # Start periodic announcements (every 2 seconds)
        asyncio.create_task(self._periodic_announcements())

        # Start listening for subworker registrations
        asyncio.create_task(self._handle_subworker_registrations())

        # Start listening for result queries
        asyncio.create_task(self._handle_result_queries())

        # Start listening for peer announcements
        asyncio.create_task(self._listen_for_peers())

        # Start all task processing respondents (from base class)
        logger.info("Starting task processing respondents...")
        await self.critical_respondent.start()
        logger.info("Critical priority listener started")
        await self.high_respondent.start()
        logger.info("High priority listener started")
        await self.normal_respondent.start()
        logger.info("Normal priority listener started")
        await self.low_respondent.start()
        logger.info("Low priority listener started")

        self.running = True

        logger.info(
            f"Control plane worker {self.worker_id} started and ready to receive tasks"
        )
        logger.info(f"Subworker management port: {self.subworker_management_port}")
        logger.info(
            f"Result cache: max_size={self.result_cache_max_size}, "
            f"ttl={self.result_cache_ttl_seconds}s"
        )

        # Start task processing (control plane processes tasks too)
        tasks = [
            asyncio.create_task(
                self._process_tasks(self.critical_respondent, TaskPriority.CRITICAL)
            ),
            asyncio.create_task(
                self._process_tasks(self.high_respondent, TaskPriority.HIGH)
            ),
            asyncio.create_task(
                self._process_tasks(self.normal_respondent, TaskPriority.NORMAL)
            ),
            asyncio.create_task(
                self._process_tasks(self.low_respondent, TaskPriority.LOW)
            ),
            # Control plane specific tasks
            asyncio.create_task(self._distribute_queued_tasks()),
            asyncio.create_task(self._monitor_subworkers()),
            asyncio.create_task(self._cleanup_result_cache()),
        ]

        # Wait for shutdown
        await self.shutdown_event.wait()

        # Cancel all tasks
        for task in tasks:
            task.cancel()

        self.stop()

    async def _periodic_announcements(self):
        """Periodically re-announce control plane presence."""
        while self.running and not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(2.0)  # Re-announce every 2 seconds
                if self.running and not self.shutdown_event.is_set():
                    await self._announce_presence()
                    logger.debug(
                        f"Control plane {self.worker_id} re-announced presence"
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic announcements: {e}")

    async def _handle_subworker_registrations(self):
        """Handle subworker registration requests."""
        while self.running:
            try:
                # Receive registration request
                data = await self.subworker_registry.recv()
                registration = TaskSerializer.deserialize(
                    data, self.serialization_format
                )

                subworker_id = registration.get("subworker_id")
                subworker_address = registration.get("address")
                status = registration.get("status", "active")
                # Note: heartbeat field is parsed but not currently used
                # is_heartbeat = registration.get("heartbeat", False)

                if subworker_id and subworker_address:
                    # Update last_seen timestamp
                    if subworker_id in self.subworkers:
                        self.subworkers[subworker_id]["last_seen"] = datetime.now()
                        self.subworkers[subworker_id]["status"] = status
                    else:
                        # New registration
                        self.subworkers[subworker_id] = {
                            "address": subworker_address,
                            "status": status,
                            "last_seen": datetime.now(),
                            "load": 0,
                            "registered_at": datetime.now(),
                        }
                        logger.info(
                            f"Registered subworker: {subworker_id} at {subworker_address}"
                        )

                    # Send acknowledgment
                    ack = {"status": "registered", "subworker_id": subworker_id}
                    ack_data = TaskSerializer.serialize(ack, self.serialization_format)
                    await self.subworker_registry.send(ack_data)

            except Exception as e:
                logger.error(f"Error handling subworker registration: {e}")

    async def _handle_result_queries(self):
        """Handle result queries from clients."""
        while self.running:
            try:
                # Receive query request
                data = await self.result_query_server.recv()
                query = TaskSerializer.deserialize(data, self.serialization_format)

                task_id = query.get("task_id")
                if not task_id:
                    # Invalid query
                    response = {"error": "Missing task_id"}
                    response_data = TaskSerializer.serialize(
                        response, self.serialization_format
                    )
                    await self.result_query_server.send(response_data)
                    continue

                # Get result from cache
                result = self._get_result(task_id)

                if result:
                    # Return result
                    response = {"found": True, "result": result.model_dump()}
                    logger.debug(f"Returned result for task {task_id} to query")
                else:
                    # Result not found or expired
                    response = {
                        "found": False,
                        "error": f"Task {task_id} not found in cache or expired",
                    }
                    logger.debug(f"Result for task {task_id} not found in cache")

                response_data = TaskSerializer.serialize(
                    response, self.serialization_format
                )
                await self.result_query_server.send(response_data)

            except Exception as e:
                logger.error(f"Error handling result query: {e}")

    async def _process_tasks(self, respondent, priority: TaskPriority):
        """Process tasks for a specific priority - override to add distribution logic."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Receive task
                data = await respondent.recv()
                task_data = TaskSerializer.deserialize(data, self.serialization_format)

                # Create task object
                task = Task(**task_data)
                logger.info(
                    f"Control plane {self.worker_id} received {priority} task "
                    f"{task.id} ({task.name})"
                )

                try:
                    # Decide: process locally or queue for distribution
                    subworker = self._select_subworker(priority)

                    if subworker:
                        # Distribute to subworker
                        await self._send_task_to_subworker(task, subworker, respondent)
                    else:
                        # Process locally (control plane acts as worker)
                        result = await self._execute_task(task)

                        # Store result in cache
                        self._store_result(result)

                        # Send result back
                        result_data = TaskSerializer.serialize(
                            result.dict(), self.serialization_format
                        )
                        await respondent.send(result_data)
                        logger.info(f"Control plane sent result for task {task.id}")

                except Exception as e:
                    # If processing fails, send error result back to client
                    logger.error(f"Error processing task {task.id}: {e}", exc_info=True)
                    error_result = TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=str(e),
                        started_at=None,
                        completed_at=datetime.now(),
                    )
                    # Store error result in cache too
                    self._store_result(error_result)
                    try:
                        error_data = TaskSerializer.serialize(
                            error_result.dict(), self.serialization_format
                        )
                        await respondent.send(error_data)
                    except Exception as send_error:
                        logger.error(
                            f"Failed to send error result for task {task.id}: {send_error}"
                        )

            except Exception as e:
                logger.error(
                    f"Error in task processing loop for {priority} in control plane "
                    f"{self.worker_id}: {e}",
                    exc_info=True,
                )
                # Continue the loop - don't break on outer exceptions

    async def _distribute_queued_tasks(self):
        """Distribute queued tasks to subworkers or process locally."""
        while self.running:
            try:
                # Check each priority queue
                for priority in [
                    TaskPriority.CRITICAL,
                    TaskPriority.HIGH,
                    TaskPriority.NORMAL,
                    TaskPriority.LOW,
                ]:
                    if self.task_queue[priority]:
                        task = self.task_queue[priority].popleft()

                        # Decide: process locally or distribute to subworker
                        subworker = self._select_subworker(priority)

                        if subworker:
                            # Distribute to subworker (we'll need a way to send result back)
                            # For now, process locally
                            asyncio.create_task(self._execute_task(task))
                        else:
                            # Process locally (control plane acts as worker)
                            asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(0.1)  # Small delay to avoid busy waiting

            except Exception as e:
                logger.error(f"Error distributing tasks: {e}")
                await asyncio.sleep(0.1)

    def _select_subworker(self, priority: TaskPriority) -> Optional[str]:
        """Select best subworker for a task based on load and priority."""
        # Filter active subworkers
        active_subworkers = {
            sid: info
            for sid, info in self.subworkers.items()
            if info["status"] == "active"
        }

        if not active_subworkers:
            return None

        # Select subworker with lowest load
        best_subworker = min(active_subworkers.items(), key=lambda x: x[1]["load"])
        return best_subworker[0] if best_subworker else None

    async def _send_task_to_subworker(
        self, task: Task, subworker_id: str, original_respondent
    ):
        """Send a task to a subworker and forward the result back."""
        try:
            subworker_info = self.subworkers[subworker_id]
            subworker_address = subworker_info["address"]

            # Parse address and create connection
            parsed = urlparse(subworker_address)
            host = parsed.hostname or "127.0.0.1"
            base_port = parsed.port or 5555
            scheme = parsed.scheme or "tcp"

            priority_ports = {
                "critical": base_port,
                "high": base_port + 1,
                "normal": base_port + 2,
                "low": base_port + 3,
            }

            priority_address = (
                f"{scheme}://{host}:{priority_ports[task.priority.value]}"
            )

            # Create requester to send task
            requester = ReqRepPattern(priority_address, is_server=False)
            await requester.start()

            try:
                # Send task
                task_data = TaskSerializer.serialize(
                    task.model_dump(), self.serialization_format
                )
                await requester.send(task_data)

                # Update subworker load
                self.subworkers[subworker_id]["load"] += 1

                # Receive result
                result_data = await requester.recv()
                result_dict = TaskSerializer.deserialize(
                    result_data, self.serialization_format
                )
                result = TaskResult(**result_dict)

                # Store result in cache
                self._store_result(result)

                # Update subworker load
                self.subworkers[subworker_id]["load"] = max(
                    0, self.subworkers[subworker_id]["load"] - 1
                )

                # Forward result back to original client
                await original_respondent.send(result_data)

                logger.info(f"Task {task.id} completed by subworker {subworker_id}")

            except Exception as e:
                logger.error(f"Error sending task to subworker {subworker_id}: {e}")
                # Update subworker load
                self.subworkers[subworker_id]["load"] = max(
                    0, self.subworkers[subworker_id]["load"] - 1
                )
                # Re-queue task or process locally
                self.task_queue[task.priority].appendleft(task)
                requester.close()

        except Exception as e:
            logger.error(f"Error in _send_task_to_subworker: {e}")
            # Re-queue task
            self.task_queue[task.priority].appendleft(task)

    async def _monitor_subworkers(self):
        """Monitor subworker health and status."""
        while self.running:
            try:
                current_time = datetime.now()
                # Check for stale subworkers (haven't been seen in 30 seconds)
                stale_threshold = 30.0

                for subworker_id, info in list(self.subworkers.items()):
                    time_since_seen = (current_time - info["last_seen"]).total_seconds()
                    if time_since_seen > stale_threshold:
                        logger.warning(
                            f"Subworker {subworker_id} appears stale, marking inactive"
                        )
                        info["status"] = "inactive"

                await asyncio.sleep(5.0)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error monitoring subworkers: {e}")
                await asyncio.sleep(5.0)

    def _store_result(self, result: TaskResult):
        """Store a task result in the cache with LRU eviction."""
        task_id = result.task_id
        now = datetime.now()

        # Remove old entry if it exists (to update access time)
        if task_id in self.result_cache:
            del self.result_cache[task_id]

        # Check if we need to evict (LRU - remove oldest accessed)
        while len(self.result_cache) >= self.result_cache_max_size:
            # Remove least recently accessed (first item in OrderedDict)
            oldest_task_id = next(iter(self.result_cache))
            del self.result_cache[oldest_task_id]
            logger.debug(
                f"Evicted result for task {oldest_task_id} due to cache size limit"
            )

        # Store new result
        self.result_cache[task_id] = {
            "result": result,
            "stored_at": now,
            "last_accessed": now,
        }
        logger.debug(
            f"Stored result for task {task_id} in cache (cache size: {len(self.result_cache)})"
        )

    def _get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get a task result from cache, updating access time."""
        if task_id not in self.result_cache:
            return None

        cache_entry = self.result_cache[task_id]

        # Check expiration
        age = (datetime.now() - cache_entry["stored_at"]).total_seconds()
        if age > self.result_cache_ttl_seconds:
            # Expired - remove it
            del self.result_cache[task_id]
            logger.debug(f"Result for task {task_id} expired (age: {age}s)")
            return None

        # Update last accessed time and move to end (LRU)
        cache_entry["last_accessed"] = datetime.now()
        # Move to end of OrderedDict (most recently accessed)
        self.result_cache.move_to_end(task_id)

        return cache_entry["result"]

    async def _cleanup_result_cache(self):
        """Periodically clean up expired results from cache."""
        while self.running:
            try:
                await asyncio.sleep(60.0)  # Check every minute

                now = datetime.now()
                expired_tasks = []

                for task_id, cache_entry in list(self.result_cache.items()):
                    age = (now - cache_entry["stored_at"]).total_seconds()
                    if age > self.result_cache_ttl_seconds:
                        expired_tasks.append(task_id)

                # Remove expired entries
                for task_id in expired_tasks:
                    del self.result_cache[task_id]

                if expired_tasks:
                    logger.info(
                        f"Cleaned up {len(expired_tasks)} expired results from cache"
                    )
                    logger.debug(f"Cache size after cleanup: {len(self.result_cache)}")

            except Exception as e:
                logger.error(f"Error cleaning up result cache: {e}")

    def stop(self):
        """Stop the control plane worker."""
        logger.info(f"Stopping control plane worker {self.worker_id}")

        # Stop management GUI
        if self._management_server:
            self._management_server.stop()
            self._management_server = None

        super().stop()  # Call base class stop
        if hasattr(self, "subworker_registry"):
            self.subworker_registry.close()
        if hasattr(self, "result_query_server"):
            self.result_query_server.close()

    def get_subworker_status(self) -> Dict:
        """Get status of all subworkers."""
        return {
            "total_subworkers": len(self.subworkers),
            "active_subworkers": len(
                [s for s in self.subworkers.values() if s["status"] == "active"]
            ),
            "subworkers": {
                sid: {
                    "address": info["address"],
                    "status": info["status"],
                    "load": info["load"],
                    "last_seen": (
                        info["last_seen"].isoformat()
                        if isinstance(info["last_seen"], datetime)
                        else str(info["last_seen"])
                    ),
                }
                for sid, info in self.subworkers.items()
            },
        }
