# Client Usage

The `Client` class is used to submit tasks to the FastWorker control plane.

## Creating a Client

```python
from fastworker import Client

client = Client()
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `discovery_address` | str | `tcp://127.0.0.1:5550` | Discovery address for finding workers |
| `serialization_format` | SerializationFormat | `JSON` | Serialization format |
| `timeout` | int | `30` | Task timeout in seconds |
| `retries` | int | `3` | Number of retries |

```python
client = Client(
    discovery_address="tcp://10.0.0.1:5550",
    timeout=60,
    retries=5
)
```

## Starting and Stopping

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

### Non-Blocking (Recommended)

Returns task ID immediately:

```python
# Returns task ID immediately
task_id = await client.delay("task_name", arg1, arg2, priority="high")
print(f"Task ID: {task_id}")

# Check result later
result = await client.get_task_result(task_id)
if result:
    print(f"Result: {result.result}")
```

### Blocking

Waits for result:

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

## Querying Results

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

```python
from fastworker.tasks.models import TaskPriority

# Using enum
task_id = await client.delay("my_task", priority=TaskPriority.CRITICAL)
task_id = await client.delay("my_task", priority=TaskPriority.HIGH)
task_id = await client.delay("my_task", priority=TaskPriority.NORMAL)
task_id = await client.delay("my_task", priority=TaskPriority.LOW)

# Using string
task_id = await client.delay("my_task", priority="high")
```

## Task Callbacks

Submit tasks with callback notifications:

```python
# Submit with callback
task_id = await client.delay_with_callback(
    "process_data",
    callback_address="tcp://127.0.0.1:6000",
    data_arg,
    callback_data={"source": "my_app", "user_id": 123}
)
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

## Error Handling

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

## Result Caching

Task results are cached in the control plane:

- **Default TTL**: 1 hour
- **Default Size**: 10,000 results
- **LRU Eviction**: Least recently accessed results evicted when cache is full

## FastAPI Integration

```python
from fastapi import FastAPI
from fastworker import Client

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
