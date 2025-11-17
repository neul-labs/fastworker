"""Worker implementation for FastWorker."""
import asyncio
import logging
import signal
from typing import Dict, List, Optional, Callable
from datetime import datetime
from fastworker.patterns.nng_patterns import (
    SurveyorRespondentPattern,
    BusPattern,
    PairPattern
)
from fastworker.tasks.registry import task_registry
from fastworker.tasks.models import Task, TaskResult, TaskStatus, TaskPriority, CallbackInfo
from fastworker.tasks.serializer import TaskSerializer, SerializationFormat
from fastworker.telemetry.tracer import trace_operation
from fastworker.telemetry.metrics import record_task_metric, record_worker_metric
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Worker:
    """Worker that executes tasks using nng patterns with built-in service discovery."""
    
    def __init__(self, 
                 worker_id: str,
                 base_address: str = "tcp://127.0.0.1:5555",
                 discovery_address: str = "tcp://127.0.0.1:5550",
                 serialization_format: SerializationFormat = SerializationFormat.JSON):
        self.worker_id = worker_id
        self.base_address = base_address
        self.discovery_address = discovery_address
        self.serialization_format = serialization_format
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Parse base address to extract host and port
        parsed = urlparse(base_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"
        
        # Create addresses for different priorities using different ports
        # Use ports base_port, base_port+1, base_port+2, base_port+3
        priority_ports = {
            'critical': base_port,
            'high': base_port + 1,
            'normal': base_port + 2,
            'low': base_port + 3
        }
        
        # Create patterns for different priorities - workers LISTEN
        self.critical_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['critical']}", is_surveyor=False)
        self.high_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['high']}", is_surveyor=False)
        self.normal_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['normal']}", is_surveyor=False)
        self.low_respondent = SurveyorRespondentPattern(
            f"{scheme}://{host}:{priority_ports['low']}", is_surveyor=False)
        
        # Built-in service discovery bus
        self.discovery_bus = BusPattern(discovery_address, listen=True)
        self.peers = set()
        
    async def start(self):
        """Start the worker with built-in service discovery."""
        logger.info(f"Starting worker {self.worker_id}")
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)
        
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
        
        self.running = True
        
        logger.info(f"Worker {self.worker_id} started with built-in discovery")
        
        # Start processing tasks for each priority
        tasks = [
            asyncio.create_task(self._process_tasks(self.critical_respondent, TaskPriority.CRITICAL)),
            asyncio.create_task(self._process_tasks(self.high_respondent, TaskPriority.HIGH)),
            asyncio.create_task(self._process_tasks(self.normal_respondent, TaskPriority.NORMAL)),
            asyncio.create_task(self._process_tasks(self.low_respondent, TaskPriority.LOW))
        ]
        
        # Wait for shutdown
        await self.shutdown_event.wait()
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        self.stop()
    
    async def _announce_presence(self):
        """Announce worker presence to network."""
        announcement = {
            'type': 'worker_announce',
            'worker_id': self.worker_id,
            'base_address': self.base_address,
            'timestamp': asyncio.get_event_loop().time()
        }
        # In a real implementation, we would serialize this properly
        await self.discovery_bus.send(f"WORKER_ANNOUNCE:{self.worker_id}:{self.base_address}".encode())
    
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
                logger.error(f"Error in peer discovery: {e}")
    
    def _signal_handler(self, sig):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, shutting down worker {self.worker_id}")
        self.shutdown_event.set()
    
    async def _process_tasks(self, respondent, priority: TaskPriority):
        """Process tasks for a specific priority."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Receive task
                data = await respondent.recv()
                task_data = TaskSerializer.deserialize(data, self.serialization_format)
                
                # Create task object
                task = Task(**task_data)
                logger.info(f"Worker {self.worker_id} received {priority} task {task.id} ({task.name})")
                
                # Execute task
                result = await self._execute_task(task)
                
                # Send result back
                result_data = TaskSerializer.serialize(result.dict(), self.serialization_format)
                await respondent.send(result_data)
                
            except Exception as e:
                logger.error(f"Error processing {priority} task in worker {self.worker_id}: {e}")
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a task."""
        task.status = TaskStatus.STARTED
        task.started_at = datetime.now()

        with trace_operation(
            f"worker.execute_task",
            attributes={
                "task.id": task.id,
                "task.name": task.name,
                "task.priority": task.priority.value,
                "worker.id": self.worker_id
            }
        ):
            try:
                # Get the task function
                func = task_registry.get_task(task.name)
                if not func:
                    raise ValueError(f"Task {task.name} not found")

                # Execute the task
                if asyncio.iscoroutinefunction(func):
                    result = await func(*task.args, **task.kwargs)
                else:
                    result = func(*task.args, **task.kwargs)

                # Calculate duration
                completed_at = datetime.now()
                duration_ms = (completed_at - task.started_at).total_seconds() * 1000

                # Create success result
                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.SUCCESS,
                    result=result,
                    started_at=task.started_at,
                    completed_at=completed_at,
                    callback=task.callback
                )

                logger.info(f"Task {task.id} completed successfully in {duration_ms:.2f}ms")

                # Record telemetry
                record_task_metric(
                    "completed",
                    task.name,
                    priority=task.priority.value,
                    worker_id=self.worker_id,
                    duration_ms=duration_ms
                )

                # Send callback if specified
                if task.callback:
                    await self._send_callback(task_result)

                return task_result

            except Exception as e:
                # Calculate duration
                completed_at = datetime.now()

                # Create failure result
                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILURE,
                    error=str(e),
                    started_at=task.started_at,
                    completed_at=completed_at,
                    callback=task.callback
                )

                logger.error(f"Task {task.id} failed: {e}")

                # Record telemetry
                record_task_metric(
                    "failed",
                    task.name,
                    priority=task.priority.value,
                    worker_id=self.worker_id
                )

                # Send callback if specified
                if task.callback:
                    await self._send_callback(task_result)

                return task_result
    
    async def _send_callback(self, task_result: TaskResult):
        """Send callback notification when task is completed."""
        if not task_result.callback:
            return
            
        try:
            # Create a pair pattern to send the callback
            callback_socket = PairPattern(task_result.callback.address, is_server=False)
            await callback_socket.start()
            
            try:
                # Prepare callback data
                callback_data = {
                    "task_id": task_result.task_id,
                    "status": task_result.status.value,
                    "result": task_result.result,
                    "error": task_result.error,
                    "started_at": task_result.started_at.isoformat() if task_result.started_at else None,
                    "completed_at": task_result.completed_at.isoformat() if task_result.completed_at else None,
                    "callback_data": task_result.callback.data
                }
                
                # Serialize and send callback data
                serialized_data = TaskSerializer.serialize(callback_data, self.serialization_format)
                await callback_socket.send(serialized_data)
                
                logger.info(f"Callback sent for task {task_result.task_id} to {task_result.callback.address}")
            finally:
                callback_socket.close()
                
        except Exception as e:
            logger.error(f"Failed to send callback for task {task_result.task_id}: {e}")
    
    def stop(self):
        """Stop the worker."""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False
        self.shutdown_event.set()
        
        # Close all patterns
        self.critical_respondent.close()
        self.high_respondent.close()
        self.normal_respondent.close()
        self.low_respondent.close()
        self.discovery_bus.close()