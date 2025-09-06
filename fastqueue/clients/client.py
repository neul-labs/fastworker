"""Client implementation for FastQueue."""
import asyncio
import logging
from typing import Any, Optional
from fastqueue.patterns.nng_patterns import SurveyorRespondentPattern, BusPattern
from fastqueue.tasks.models import Task, TaskPriority, TaskResult, TaskStatus, CallbackInfo
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat

logger = logging.getLogger(__name__)

class Client:
    """Client for submitting tasks to workers with built-in service discovery."""
    
    def __init__(self, 
                 discovery_address: str = "tcp://127.0.0.1:5550",
                 serialization_format: SerializationFormat = SerializationFormat.JSON,
                 timeout: int = 30,
                 retries: int = 3):
        self.discovery_address = discovery_address
        self.serialization_format = serialization_format
        self.timeout = timeout
        self.retries = retries
        self.running = False
        
        # Built-in service discovery bus
        self.discovery_bus = BusPattern(discovery_address, listen=False)
        self.workers = set()
        
    async def start(self):
        """Start the client with built-in service discovery."""
        logger.info("Starting client with built-in discovery")
        await self.discovery_bus.start()
        self.running = True
        
        # Start listening for worker announcements
        asyncio.create_task(self._listen_for_workers())
        
        # Give some time to discover workers
        await asyncio.sleep(0.1)
        
    async def _listen_for_workers(self):
        """Listen for worker announcements."""
        while self.running:
            try:
                data = await self.discovery_bus.recv()
                message = data.decode()
                
                if message.startswith("WORKER_ANNOUNCE:"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        worker_id = parts[1]
                        worker_address = parts[2]
                        self.workers.add((worker_id, worker_address))
                        logger.info(f"Discovered worker: {worker_id} at {worker_address}")
                        
            except Exception as e:
                logger.error(f"Error in worker discovery: {e}")
    
    async def submit_task(self, 
                         task_name: str,
                         args: tuple = (),
                         kwargs: dict = {},
                         priority: TaskPriority = TaskPriority.NORMAL) -> TaskResult:
        """Submit a task to workers."""
        # Create task
        task = Task(
            name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        # Check if we have available workers
        if not self.workers:
            # Try to discover workers
            await asyncio.sleep(0.1)
            if not self.workers:
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILURE,
                    error="No workers available"
                )
        
        # Use the first available worker
        worker_id, worker_address = next(iter(self.workers))
        priority_address = f"{worker_address}_{priority.value}"
        
        # Try to submit task with retries
        for attempt in range(self.retries + 1):
            try:
                # Create surveyor for this priority
                surveyor = SurveyorRespondentPattern(priority_address, is_surveyor=True)
                await surveyor.start()
                
                try:
                    # Serialize and send task
                    task_data = TaskSerializer.serialize(task.dict(), self.serialization_format)
                    await surveyor.send(task_data)
                    
                    # Receive result with timeout
                    result_data = await asyncio.wait_for(surveyor.recv(), timeout=self.timeout)
                    result_dict = TaskSerializer.deserialize(result_data, self.serialization_format)
                    result = TaskResult(**result_dict)
                    
                    return result
                finally:
                    surveyor.close()
                    
            except asyncio.TimeoutError:
                if attempt < self.retries:
                    logger.warning(f"Task submission timed out, retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Task submission failed after {self.retries} retries")
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=f"Task submission timed out after {self.retries} retries"
                    )
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                if attempt < self.retries:
                    logger.warning(f"Retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=str(e)
                    )
    
    async def delay(self, 
                   task_name: str,
                   *args,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   **kwargs) -> TaskResult:
        """Submit a task and return immediately."""
        return await self.submit_task(task_name, args, kwargs, priority)
    
    async def delay_with_callback(self,
                                 task_name: str,
                                 callback_address: str,
                                 *args,
                                 callback_data: dict = None,
                                 priority: TaskPriority = TaskPriority.NORMAL,
                                 **kwargs) -> TaskResult:
        """Submit a task with a callback and return immediately."""
        # Create task with callback information
        task = Task(
            name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            callback=CallbackInfo(address=callback_address, data=callback_data)
        )
        
        # Check if we have available workers
        if not self.workers:
            # Try to discover workers
            await asyncio.sleep(0.1)
            if not self.workers:
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILURE,
                    error="No workers available"
                )
        
        # Use the first available worker
        worker_id, worker_address = next(iter(self.workers))
        priority_address = f"{worker_address}_{priority.value}"
        
        # Try to submit task with retries
        for attempt in range(self.retries + 1):
            try:
                # Create surveyor for this priority
                surveyor = SurveyorRespondentPattern(priority_address, is_surveyor=True)
                await surveyor.start()
                
                try:
                    # Serialize and send task
                    task_data = TaskSerializer.serialize(task.dict(), self.serialization_format)
                    await surveyor.send(task_data)
                    
                    # Receive result with timeout
                    result_data = await asyncio.wait_for(surveyor.recv(), timeout=self.timeout)
                    result_dict = TaskSerializer.deserialize(result_data, self.serialization_format)
                    result = TaskResult(**result_dict)
                    
                    return result
                finally:
                    surveyor.close()
                    
            except asyncio.TimeoutError:
                if attempt < self.retries:
                    logger.warning(f"Task submission timed out, retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Task submission failed after {self.retries} retries")
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=f"Task submission timed out after {self.retries} retries"
                    )
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                if attempt < self.retries:
                    logger.warning(f"Retrying... (attempt {attempt + 1}/{self.retries})")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    return TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILURE,
                        error=str(e)
                    )
    
    def stop(self):
        """Stop the client."""
        logger.info("Stopping client")
        self.running = False
        self.discovery_bus.close()