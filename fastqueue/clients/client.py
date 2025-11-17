"""Client implementation for FastQueue."""
import asyncio
import logging
import os
from typing import Any, Optional, Dict
from fastqueue.patterns.nng_patterns import SurveyorRespondentPattern, BusPattern, ReqRepPattern
from fastqueue.tasks.models import Task, TaskPriority, TaskResult, TaskStatus, CallbackInfo
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat
from fastqueue.telemetry.tracer import trace_operation
from fastqueue.telemetry.metrics import record_task_metric
import re
from urllib.parse import urlparse
from collections import deque

logger = logging.getLogger(__name__)

class Client:
    """Client for submitting tasks to workers with built-in service discovery.

    Configuration can be provided via environment variables:
    - FASTQUEUE_DISCOVERY_ADDRESS: Discovery address (default: tcp://127.0.0.1:5550)
    - FASTQUEUE_SERIALIZATION_FORMAT: Serialization format - JSON or PICKLE (default: JSON)
    - FASTQUEUE_TIMEOUT: Task timeout in seconds (default: 30)
    - FASTQUEUE_RETRIES: Number of retries for failed submissions (default: 3)
    """

    def __init__(self,
                 discovery_address: Optional[str] = None,
                 serialization_format: Optional[SerializationFormat] = None,
                 timeout: Optional[int] = None,
                 retries: Optional[int] = None):
        # Load from environment variables with fallback to defaults
        self.discovery_address = discovery_address or os.getenv(
            "FASTQUEUE_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550"
        )

        # Parse serialization format from string if needed
        if serialization_format is None:
            format_str = os.getenv("FASTQUEUE_SERIALIZATION_FORMAT", "JSON").upper()
            self.serialization_format = (
                SerializationFormat.PICKLE if format_str == "PICKLE"
                else SerializationFormat.JSON
            )
        else:
            self.serialization_format = serialization_format

        self.timeout = timeout or int(os.getenv("FASTQUEUE_TIMEOUT", "30"))
        self.retries = retries or int(os.getenv("FASTQUEUE_RETRIES", "3"))
        self.running = False

        # Built-in service discovery bus
        self.discovery_bus = BusPattern(self.discovery_address, listen=False)
        self.workers = set()
        
        # Task queue for pending tasks (when no workers available)
        self.pending_tasks: deque = deque()
        
        # Task results storage (task_id -> TaskResult)
        self.task_results: Dict[str, TaskResult] = {}
        
        # Background task processor
        self._task_processor_task = None
        
    async def start(self):
        """Start the client with built-in service discovery."""
        logger.info("Starting client with built-in discovery")
        logger.info(f"Discovery address: {self.discovery_address}")
        await self.discovery_bus.start()
        logger.info("Discovery bus started")
        self.running = True
        
        # Start listening for worker announcements
        asyncio.create_task(self._listen_for_workers())
        
        # Start background task processor
        self._task_processor_task = asyncio.create_task(self._process_pending_tasks())
        
        # Give more time to discover workers (especially if control plane starts after client)
        logger.info("Waiting for worker discovery...")
        await asyncio.sleep(2.0)  # Increased from 0.5 to 2.0 seconds
        logger.info(f"Client started. Discovered {len(self.workers)} workers: {list(self.workers)}")
        
    async def _listen_for_workers(self):
        """Listen for worker announcements."""
        logger.info("Started listening for worker announcements...")
        while self.running:
            try:
                data = await self.discovery_bus.recv()
                message = data.decode()
                logger.debug(f"Received discovery message: {message}")
                
                if message.startswith("WORKER_ANNOUNCE:"):
                    # Parse: WORKER_ANNOUNCE:worker_id:address
                    # Address may contain colons (e.g., tcp://127.0.0.1:5555)
                    parts = message.split(":", 2)  # Split into max 3 parts
                    if len(parts) >= 3:
                        worker_id = parts[1]
                        worker_address = parts[2]  # This is the full address
                        self.workers.add((worker_id, worker_address))
                        logger.info(f"Discovered worker: {worker_id} at {worker_address}")
                    else:
                        logger.warning(f"Invalid WORKER_ANNOUNCE format: {message}")
                        
            except (OSError, RuntimeError, ValueError) as e:
                # Handle closed socket or other errors gracefully
                if self.running:
                    logger.error(f"Error in worker discovery: {e}")
                # If we're shutting down, break the loop
                if not self.running:
                    break
            except Exception as e:
                if self.running:
                    logger.error(f"Unexpected error in worker discovery: {e}", exc_info=True)
                if not self.running:
                    break
    
    async def _process_pending_tasks(self):
        """Process pending tasks when workers become available."""
        while self.running:
            try:
                # If we have workers and pending tasks, process them
                if self.workers and self.pending_tasks:
                    task = self.pending_tasks.popleft()
                    # Submit task in background (don't await, fire and forget)
                    asyncio.create_task(self._submit_task_internal(task))
                else:
                    # Wait a bit before checking again
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing pending tasks: {e}")
                await asyncio.sleep(0.1)
    
    async def _submit_task_internal(self, task: Task) -> TaskResult:
        """Internal method to submit a task to workers."""
        # If no workers available, queue the task
        if not self.workers:
            logger.debug(f"No workers available, queuing task {task.id}")
            self.pending_tasks.append(task)
            # Return pending result
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.PENDING,
                result=None,
                error=None,
                started_at=None,
                completed_at=None
            )
            self.task_results[task.id] = result
            return result

        # Use the first available worker
        worker_id, worker_address = next(iter(self.workers))
        
        # Parse worker address and create priority-specific address
        parsed = urlparse(worker_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"
        
        # Map priority to port offset
        priority_ports = {
            'critical': base_port,
            'high': base_port + 1,
            'normal': base_port + 2,
            'low': base_port + 3
        }
        
        priority_address = f"{scheme}://{host}:{priority_ports[task.priority.value]}"

        # Try to submit task with retries
        for attempt in range(self.retries + 1):
            try:
                # Create requester for this priority (client dials to control plane)
                requester = ReqRepPattern(priority_address, is_server=False)
                await requester.start()

                try:
                    # Serialize and send task
                    task_data = TaskSerializer.serialize(task.model_dump(), self.serialization_format)
                    await requester.send(task_data)

                    # Receive result with timeout
                    result_data = await asyncio.wait_for(requester.recv(), timeout=self.timeout)
                    result_dict = TaskSerializer.deserialize(result_data, self.serialization_format)
                    result = TaskResult(**result_dict)
                    
                    # Store result
                    self.task_results[task.id] = result

                    return result
                finally:
                    requester.close()

            except asyncio.TimeoutError:
                if attempt < self.retries:
                    logger.warning(f"Task submission timed out, retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Task submission failed after {self.retries} retries")
                    result = TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=f"Task submission timed out after {self.retries} retries"
                    )
                    self.task_results[task.id] = result
                    return result
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                if attempt < self.retries:
                    logger.warning(f"Retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    result = TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=str(e)
                    )
                    self.task_results[task.id] = result
                    return result

    async def submit_task(self,
                         task_name: str,
                         args: tuple = (),
                         kwargs: dict = {},
                         priority: TaskPriority = TaskPriority.NORMAL) -> TaskResult:
        """Submit a task to workers and wait for result."""
        # Create task
        task = Task(
            name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority
        )

        return await self._submit_task_internal(task)
    
    async def delay(self,
              task_name: str,
              *args,
              priority: TaskPriority = TaskPriority.NORMAL,
              **kwargs) -> str:
        """Submit a task and return immediately with task ID (non-blocking)."""
        with trace_operation(
            "client.submit_task",
            attributes={
                "task.name": task_name,
                "task.priority": priority.value if hasattr(priority, 'value') else str(priority)
            }
        ):
            # Create task
            task = Task(
                name=task_name,
                args=args,
                kwargs=kwargs,
                priority=priority
            )

            # Record metric
            record_task_metric("submitted", task_name, priority=task.priority.value)

            # Initialize pending result
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.PENDING,
                result=None,
                error=None,
                started_at=None,
                completed_at=None
            )
            self.task_results[task.id] = result
        
        # Submit task in background (non-blocking) - use create_task to ensure it runs
        asyncio.create_task(self._submit_task_internal_with_error_handling(task))
        
        # Return task ID immediately
        return task.id
    
    async def _submit_task_internal_with_error_handling(self, task: Task):
        """Wrapper to handle errors in task submission."""
        try:
            await self._submit_task_internal(task)
        except Exception as e:
            logger.error(f"Error submitting task {task.id}: {e}")
            # Update result with error
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILURE,
                error=str(e),
                started_at=None,
                completed_at=None
            )
            self.task_results[task.id] = result
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result by task ID."""
        return self.task_results.get(task_id)
    
    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status by task ID."""
        result = self.task_results.get(task_id)
        return result.status if result else None
    
    async def delay_with_callback(self,
                                 task_name: str,
                                 callback_address: str,
                                 *args,
                                 callback_data: dict = None,
                                 priority: TaskPriority = TaskPriority.NORMAL,
                                 **kwargs) -> str:
        """Submit a task with a callback and return immediately with task ID (non-blocking)."""
        # Create task with callback information
        task = Task(
            name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            callback=CallbackInfo(address=callback_address, data=callback_data)
        )
        
        # Initialize pending result
        result = TaskResult(
            task_id=task.id,
            status=TaskStatus.PENDING,
            result=None,
            error=None,
            started_at=None,
            completed_at=None
        )
        self.task_results[task.id] = result
        
        # Submit task in background (non-blocking)
        asyncio.create_task(self._submit_task_internal_with_error_handling(task))
        
        # Return task ID immediately
        return task.id
    
    def stop(self):
        """Stop the client."""
        logger.info("Stopping client")
        self.running = False
        if self._task_processor_task:
            self._task_processor_task.cancel()
        self.discovery_bus.close()

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Query task result from control plane."""
        if not self.workers:
            logger.warning("No workers discovered, cannot query result")
            return None
        
        # Use the first available worker (control plane)
        worker_id, worker_address = next(iter(self.workers))
        
        # Parse worker address to get result query port (base_port + 4)
        parsed = urlparse(worker_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"
        result_query_port = base_port + 4
        
        result_query_address = f"{scheme}://{host}:{result_query_port}"
        
        try:
            # Create requester to query result
            requester = ReqRepPattern(result_query_address, is_server=False)
            await requester.start()
            
            try:
                # Send query
                query = {'task_id': task_id}
                query_data = TaskSerializer.serialize(query, self.serialization_format)
                await requester.send(query_data)
                
                # Receive response
                response_data = await requester.recv()
                response = TaskSerializer.deserialize(response_data, self.serialization_format)
                
                if response.get('found'):
                    result_dict = response.get('result')
                    return TaskResult(**result_dict)
                else:
                    logger.debug(f"Result not found for task {task_id}: {response.get('error')}")
                    return None
                    
            finally:
                requester.close()
                
        except Exception as e:
            logger.error(f"Error querying result for task {task_id}: {e}")
            return None