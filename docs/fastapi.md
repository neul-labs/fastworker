# FastAPI Integration

FastQueue integrates seamlessly with FastAPI applications, providing a brokerless alternative to Celery.

## Basic Integration

### 1. Define Tasks

```python
# tasks.py
from fastqueue import task

@task
def process_user_registration(user_id: int, email: str) -> dict:
    """Process user registration."""
    # Simulate some work
    return {"user_id": user_id, "status": "registered"}

@task
def send_notification(user_id: int, message: str) -> dict:
    """Send notification to user."""
    # Simulate sending notification
    return {"user_id": user_id, "notification_sent": True}
```

### 2. Configure FastAPI Application

```python
# main.py
from fastapi import FastAPI
from fastqueue import Client

app = FastAPI(title="My FastAPI App")
client = Client()

@app.on_event("startup")
async def startup_event():
    """Initialize FastQueue client on startup."""
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up FastQueue client on shutdown."""
    client.stop()

@app.post("/register/")
async def register_user(user_id: int, email: str):
    """Register a new user."""
    result = await client.delay("process_user_registration", user_id, email)
    if result.status == "success":
        return {"message": "User registered", "result": result.result}
    else:
        raise HTTPException(status_code=500, detail=result.error)
```

### 3. Start Workers

In separate terminals, start workers to process tasks:

```bash
fastqueue worker --worker-id worker1 --task-modules tasks
fastqueue worker --worker-id worker2 --task-modules tasks
```

## Advanced Integration Patterns

### Background Task Processing

For non-critical tasks that can be processed asynchronously:

```python
from fastapi import BackgroundTasks

@app.post("/notify/")
async def send_notification_async(user_id: int, message: str, background_tasks: BackgroundTasks):
    """Send notification asynchronously."""
    # For simple background tasks, use FastAPI's BackgroundTasks
    background_tasks.add_task(send_notification_task, user_id, message)
    
    # For complex distributed processing, use FastQueue
    # await client.delay("send_notification", user_id, message)
    
    return {"message": "Notification queued"}

def send_notification_task(user_id: int, message: str):
    """Simple background task."""
    # This runs in a thread pool
    print(f"Sending notification to {user_id}: {message}")
```

### Error Handling and Fallbacks

```python
@app.post("/process/")
async def process_with_fallback(data: dict):
    """Process data with fallback mechanism."""
    # Try to process with FastQueue
    result = await client.delay("process_data", data)
    
    if result.status == "failure":
        if "No workers available" in result.error:
            # Fallback to synchronous processing
            sync_result = process_data_sync(data)  # Direct function call
            return {"message": "Processed synchronously", "result": sync_result}
        else:
            # Other error
            raise HTTPException(status_code=500, detail=result.error)
    
    return {"message": "Processed asynchronously", "result": result.result}
```

### Health Checks

```python
@app.get("/health/")
async def health_check():
    """Health check endpoint."""
    worker_count = len(client.workers) if hasattr(client, 'workers') else 0
    if worker_count > 0:
        return {"status": "healthy", "workers_online": worker_count}
    else:
        return {"status": "degraded", "workers_online": 0}
```

### Task Status Tracking

```python
from fastqueue.tasks.models import TaskStatus

# Store task IDs for status tracking
task_storage = {}

@app.post("/process-with-tracking/")
async def process_with_tracking(data: dict):
    """Process data with status tracking."""
    result = await client.delay("process_data", data)
    task_storage[result.task_id] = result
    return {"task_id": result.task_id, "message": "Processing started"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    if task_id in task_storage:
        result = task_storage[task_id]
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.status == "success" else None,
            "error": result.error if result.status == "failure" else None
        }
    else:
        raise HTTPException(status_code=404, detail="Task not found")
```

## Configuration

### Environment-Based Configuration

```python
import os
from fastqueue import Client

# Configure based on environment
DISCOVERY_ADDRESS = os.getenv("FASTQUEUE_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550")
TIMEOUT = int(os.getenv("FASTQUEUE_TIMEOUT", "30"))
RETRIES = int(os.getenv("FASTQUEUE_RETRIES", "3"))

client = Client(
    discovery_address=DISCOVERY_ADDRESS,
    timeout=TIMEOUT,
    retries=RETRIES
)
```

### Dependency Injection

```python
from fastapi import Depends

async def get_fastqueue_client():
    """Dependency to get FastQueue client."""
    # In a real implementation, you might want to manage a singleton
    client = Client()
    await client.start()
    try:
        yield client
    finally:
        client.stop()

@app.post("/process/")
async def process_data(data: dict, client: Client = Depends(get_fastqueue_client)):
    """Process data with injected client."""
    result = await client.delay("process_data", data)
    if result.status == "success":
        return {"result": result.result}
    else:
        raise HTTPException(status_code=500, detail=result.error)
```

## Production Considerations

### Multiple Worker Types

```python
# cpu_intensive_tasks.py
@task
def cpu_intensive_task(data: dict) -> dict:
    """CPU intensive task."""
    # Process data
    return {"result": "processed"}

# io_intensive_tasks.py
@task
async def io_intensive_task(data: dict) -> dict:
    """I/O intensive task."""
    # Async I/O operations
    return {"result": "processed"}
```

Start specialized workers:

```bash
# CPU intensive workers
fastqueue worker --worker-id cpu-worker-1 --task-modules cpu_intensive_tasks
fastqueue worker --worker-id cpu-worker-2 --task-modules cpu_intensive_tasks

# I/O intensive workers
fastqueue worker --worker-id io-worker-1 --task-modules io_intensive_tasks
fastqueue worker --worker-id io-worker-2 --task-modules io_intensive_tasks
```

### Monitoring and Metrics

```python
from fastapi import FastAPI
import time

app = FastAPI()
task_metrics = {"total_tasks": 0, "failed_tasks": 0, "avg_processing_time": 0}

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.post("/process/")
async def process_data(data: dict):
    start_time = time.time()
    result = await client.delay("process_data", data)
    process_time = time.time() - start_time
    
    # Update metrics
    task_metrics["total_tasks"] += 1
    if result.status == "failure":
        task_metrics["failed_tasks"] += 1
    # Update average processing time...
    
    if result.status == "success":
        return {"result": result.result}
    else:
        raise HTTPException(status_code=500, detail=result.error)
```

## Task Completion Callbacks

FastQueue supports task completion callbacks using NNG messaging patterns. This allows your FastAPI application to receive notifications when tasks are completed, enabling more responsive and interactive applications.

### Using Callbacks

To submit a task with a callback, use the `delay_with_callback` method:

```python
@app.post("/process-with-callback/")
async def process_with_callback(data: dict, callback_address: str):
    """Process data with a callback when finished."""
    result = await client.delay_with_callback(
        "process_data", 
        callback_address, 
        data,
        callback_data={"source": "fastapi_endpoint"}
    )
    
    if result.status == "success":
        return {"message": "Task submitted", "task_id": result.task_id}
    else:
        raise HTTPException(status_code=500, detail=result.error)
```

### Receiving Callbacks

To receive callbacks in your FastAPI application, you can create a listener endpoint:

```python
from fastqueue.patterns.nng_patterns import PairPattern
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat

@app.post("/start-processing-with-internal-callback/")
async def start_processing_with_internal_callback(data: dict):
    """Start processing with an internal callback listener."""
    # Create a unique callback address
    callback_address = f"tcp://127.0.0.1:{5000 + hash(str(data)) % 1000}"
    
    # Start callback listener in the background
    asyncio.create_task(listen_for_callback(callback_address))
    
    # Submit task with callback
    result = await client.delay_with_callback(
        "process_data", 
        callback_address, 
        data,
        callback_data={"endpoint": "/task-completed/"}
    )
    
    return {"task_id": result.task_id, "callback_address": callback_address}

async def listen_for_callback(callback_address: str):
    """Listen for task completion callbacks."""
    try:
        # Create a pair pattern to receive callbacks
        callback_listener = PairPattern(callback_address, is_server=True)
        await callback_listener.start()
        
        # Listen for one callback
        data = await callback_listener.recv()
        callback_data = TaskSerializer.deserialize(data, SerializationFormat.JSON)
        
        # Process the callback (e.g., update database, send WebSocket message, etc.)
        await handle_task_completion(callback_data)
        
        callback_listener.close()
    except Exception as e:
        print(f"Error in callback listener: {e}")

async def handle_task_completion(callback_data: dict):
    """Handle task completion notification."""
    print(f"Task completed: {callback_data}")
    # Update database, send WebSocket message, trigger another task, etc.
```

### Callback Data Structure

When a task completes, the callback will receive a dictionary with the following structure:

```python
{
    "task_id": "unique-task-id",
    "status": "success|failure",
    "result": "task result data (if successful)",
    "error": "error message (if failed)",
    "started_at": "ISO timestamp",
    "completed_at": "ISO timestamp",
    "callback_data": "additional data provided when task was submitted"
}
```

## Best Practices

1. **Initialize Client Once**: Create a single client instance per application
2. **Handle Worker Unavailability**: Implement fallback strategies for when no workers are available
3. **Monitor Task Performance**: Track task execution times and failure rates
4. **Use Appropriate Priorities**: Submit tasks with appropriate priority levels
5. **Implement Health Checks**: Monitor worker availability and system health
6. **Configure Timeouts**: Set appropriate timeouts based on task complexity
7. **Log Important Events**: Log task submissions, completions, and failures
8. **Handle Callbacks Gracefully**: Implement proper error handling for callback listeners
9. **Use Unique Callback Addresses**: Ensure callback addresses are unique to avoid conflicts