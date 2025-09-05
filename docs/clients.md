# Client Guide

## Creating a Client

Clients are used to submit tasks to workers:

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

### Using `delay()` (Recommended)

Submit a task and return immediately:

```python
result = await client.delay("task_name", arg1, arg2, keyword_arg=value, priority="high")
```

### Using `submit_task()`

Submit a task with more control:

```python
result = await client.submit_task(
    task_name="task_name",
    args=(arg1, arg2),
    kwargs={"keyword_arg": value},
    priority=TaskPriority.HIGH
)
```

## Handling Results

The client returns a `TaskResult` object:

```python
result = await client.delay("add", 2, 3)

if result.status == "success":
    print(f"Task succeeded with result: {result.result}")
else:
    print(f"Task failed with error: {result.error}")
```

## Task Priority

Tasks can be submitted with different priorities:

```python
from fastqueue.tasks.models import TaskPriority

# Submit with different priorities
result1 = await client.delay("my_task", priority=TaskPriority.CRITICAL)
result2 = await client.delay("my_task", priority=TaskPriority.HIGH)
result3 = await client.delay("my_task", priority=TaskPriority.NORMAL)
result4 = await client.delay("my_task", priority=TaskPriority.LOW)
```

Or using string values:

```python
result = await client.delay("my_task", priority="high")
```

## Error Handling

The client handles various error scenarios:

```python
try:
    result = await client.delay("my_task")
    
    if result.status == "failure":
        if "No workers available" in result.error:
            print("No workers are currently available")
        else:
            print(f"Task failed: {result.error}")
    else:
        print(f"Task succeeded: {result.result}")
        
except Exception as e:
    print(f"Client error: {e}")
```

## Retry Mechanism

The client automatically retries failed tasks:

1. Default: 3 retries with exponential backoff
2. Configurable through the `retries` parameter
3. Retry delay increases with each attempt

## Service Discovery

Clients automatically discover available workers:

1. Clients listen for worker announcements
2. Workers are automatically added to the available pool
3. Offline workers are automatically removed

## Timeout Handling

Tasks can timeout if workers don't respond:

```python
# Set custom timeout (in seconds)
client = Client(timeout=60)  # 60 second timeout

# Or set timeout per task
result = await client.delay("slow_task", timeout=120)  # 120 second timeout
```

## Serialization

The client supports different serialization formats:

```python
from fastqueue.tasks.serializer import SerializationFormat

client = Client(serialization_format=SerializationFormat.PICKLE)
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
    result = await client.delay("process_data", data)
    return {"result": result.result}
```

## Best Practices

1. **Reuse Client Instances**: Create one client instance per application
2. **Handle Errors Gracefully**: Always check task results for failures
3. **Use Appropriate Timeouts**: Set timeouts based on task complexity
4. **Set Retry Limits**: Adjust retries based on task criticality
5. **Monitor Worker Availability**: Check worker status in production