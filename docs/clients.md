# Client Guide

## Creating a Client

Clients are used to submit tasks to the control plane:

```python
from fastqueue import Client

client = Client()
```

### Constructor Parameters

- `discovery_address` (optional): Discovery address (default: `tcp://127.0.0.1:5550`)
- `serialization_format` (optional): Serialization format (default: `SerializationFormat.JSON`)
- `timeout` (optional): Task timeout in seconds (default: 30)
- `retries` (optional): Number of retries (default: 3)

## Starting and Stopping the Client

```python
import asyncio

async def main():
    client = Client()
    
    # Start the client
    await client.start()
    
    # Use the client...
    
    # Stop the client
    client.stop()

asyncio.run(main())
```

## Submitting Tasks

### Non-Blocking Submission (Recommended)

Submit a task and get task ID immediately:

```python
# Returns task ID immediately
task_id = await client.delay("task_name", arg1, arg2, priority="high")
print(f"Task ID: {task_id}")

# Check result later
result = await client.get_task_result(task_id)
if result:
    print(f"Result: {result.result}")
```

### Blocking Submission

Submit a task and wait for result:

```python
result = await client.submit_task(
    task_name="task_name",
    args=(arg1, arg2),
    kwargs={"keyword_arg": value},
    priority=TaskPriority.HIGH
)

if result.status == TaskStatus.SUCCESS:
    print(f"Result: {result.result}")
else:
    print(f"Error: {result.error}")
```

## Querying Task Results

### From Control Plane

Query results from the control plane's result cache:

```python
result = await client.get_task_result(task_id)

if result:
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
else:
    print("Result not found or expired")
```

### From Local Cache

Get result from client's local cache (only if client submitted the task):

```python
result = client.get_result(task_id)
status = client.get_status(task_id)
```

## Task Priority

Tasks can be submitted with different priorities:

```python
from fastqueue.tasks.models import TaskPriority

# Submit with different priorities
task_id1 = await client.delay("my_task", priority=TaskPriority.CRITICAL)
task_id2 = await client.delay("my_task", priority=TaskPriority.HIGH)
task_id3 = await client.delay("my_task", priority=TaskPriority.NORMAL)
task_id4 = await client.delay("my_task", priority=TaskPriority.LOW)
```

Or using string values:

```python
task_id = await client.delay("my_task", priority="high")
```

## Error Handling

The client handles various error scenarios:

```python
try:
    task_id = await client.delay("my_task")
    result = await client.get_task_result(task_id)
    
    if result and result.status == TaskStatus.FAILURE:
        print(f"Task failed: {result.error}")
    elif result:
        print(f"Task succeeded: {result.result}")
    else:
        print("Task result not available")
        
except Exception as e:
    print(f"Client error: {e}")
```

## Task Callbacks

Submit tasks with callback notifications to receive updates when tasks complete.

### Submitting Tasks with Callbacks

```python
from fastqueue.patterns.nng_patterns import PairPattern
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat

async def main():
    client = Client()
    await client.start()

    # Create unique callback address
    callback_address = "tcp://127.0.0.1:6000"

    # Submit task with callback
    result = await client.delay_with_callback(
        "process_data",
        callback_address,
        data_arg,
        callback_data={"source": "my_app", "user_id": 123}
    )

    print(f"Task submitted: {result.task_id}")
    client.stop()

asyncio.run(main())
```

### Receiving Callback Notifications

Create a listener to receive callback notifications when tasks complete:

```python
async def listen_for_callback(callback_address: str):
    """Listen for task completion callbacks."""
    # Create callback listener
    callback_listener = PairPattern(callback_address, is_server=True)
    await callback_listener.start()

    try:
        # Wait for callback notification
        data = await callback_listener.recv()
        callback_data = TaskSerializer.deserialize(data, SerializationFormat.JSON)

        # Process the callback
        print(f"Task completed: {callback_data['task_id']}")
        print(f"Status: {callback_data['status']}")
        print(f"Result: {callback_data['result']}")
        print(f"Custom data: {callback_data['callback_data']}")

    finally:
        callback_listener.close()

# Start listener in background
asyncio.create_task(listen_for_callback("tcp://127.0.0.1:6000"))
```

### Callback Data Structure

When a task completes, the callback receives:

```python
{
    "task_id": "unique-task-id",
    "status": "success|failure",
    "result": "task result (if successful)",
    "error": "error message (if failed)",
    "started_at": "ISO timestamp",
    "completed_at": "ISO timestamp",
    "callback_data": {"source": "my_app", "user_id": 123}
}
```

### Use Cases for Callbacks

1. **Real-time Updates**: Send WebSocket notifications to users when tasks complete
2. **Workflow Orchestration**: Trigger subsequent tasks based on completion
3. **Monitoring**: Track task completion metrics in real-time
4. **Error Handling**: Respond immediately to task failures

For more details, see the [FastAPI Integration](fastapi.md#task-completion-callbacks) guide.

## Retry Mechanism

The client automatically retries failed task submissions:

1. Default: 3 retries with exponential backoff
2. Configurable through the `retries` parameter
3. Retry delay increases with each attempt

## Service Discovery

Clients automatically discover the control plane:

1. Clients listen for control plane announcements
2. Control plane is automatically added to available pool
3. Automatic reconnection if control plane restarts

## Timeout Handling

Tasks can timeout if the control plane doesn't respond:

```python
# Set custom timeout (in seconds)
client = Client(timeout=60)  # 60 second timeout
```

## Result Caching

Task results are cached in the control plane:

- **Default TTL**: 1 hour
- **Default Size**: 10,000 results
- **LRU Eviction**: Least recently accessed results evicted when cache is full

Query results using:

```python
result = await client.get_task_result(task_id)
```

## FastAPI Integration

For FastAPI applications, create a single client instance:

```python
from fastapi import FastAPI
from fastqueue import Client

app = FastAPI()
client = Client()

@app.on_event("startup")
async def startup_event():
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    client.stop()

@app.post("/process/")
async def process_endpoint(data: dict):
    # Non-blocking submission
    task_id = await client.delay("process_data", data)
    return {"task_id": task_id}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = await client.get_task_result(task_id)
    if result:
        return {"status": result.status.value, "result": result.result}
    return {"error": "Result not found"}
```

## Best Practices

1. **Reuse Client Instances**: Create one client instance per application
2. **Use Non-Blocking Submission**: Use `delay()` for better performance
3. **Query Results Asynchronously**: Check results when needed, not immediately
4. **Handle Errors Gracefully**: Always check task results for failures
5. **Set Appropriate Timeouts**: Adjust timeouts based on task complexity
6. **Monitor Control Plane**: Ensure control plane is running and healthy