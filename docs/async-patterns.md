# Async Patterns: Blocking vs Non-Blocking

FastQueue provides both **blocking** and **non-blocking** task submission patterns. Understanding the difference is crucial for building responsive applications.

## Quick Comparison

| Method | Behavior | Returns | Use Case |
|--------|----------|---------|----------|
| `submit_task()` | **Blocking** - Waits for result | `TaskResult` | When you need the result immediately |
| `delay()` | **Non-blocking** - Returns immediately | `task_id` (str) | Background tasks, fire-and-forget |
| `delay_with_callback()` | **Non-blocking** - Returns immediately | `task_id` (str) | Reactive workflows with notifications |

---

## Blocking: `submit_task()`

Submits a task and **waits** for the result before continuing.

### Usage

```python
from fastqueue import Client
from fastqueue.tasks.models import TaskPriority

client = Client()
await client.start()

# BLOCKS until task completes
result = await client.submit_task(
    task_name="process_data",
    args=(data,),
    priority=TaskPriority.HIGH
)

# Result is available immediately
if result.status == "success":
    print(f"Result: {result.result}")
else:
    print(f"Error: {result.error}")
```

### When to Use

✅ **Use blocking when:**
- You need the result immediately
- The calling code depends on the task result
- You're okay waiting for task completion
- Tasks complete quickly (< 1 second)

❌ **Don't use blocking when:**
- Handling web requests (causes slow response times)
- Task takes a long time to complete
- You don't need the result immediately
- You're processing multiple tasks in parallel

### Example: Synchronous Processing

```python
@app.post("/process-sync/")
async def process_sync(data: dict):
    """Blocking - waits for result."""
    # WARNING: This blocks the request handler!
    result = await client.submit_task(
        task_name="process_data",
        args=(data,)
    )

    return {"result": result.result}  # Result available immediately
```

**Problem:** Web request is slow because it waits for task completion.

---

## Non-Blocking: `delay()`

Submits a task and **returns immediately** with a task ID. The task executes in the background.

### Usage

```python
from fastqueue import Client

client = Client()
await client.start()

# Returns IMMEDIATELY with task ID
task_id = await client.delay("process_data", data, priority="high")
print(f"Task submitted: {task_id}")

# Task is processing in background...
# You can continue doing other work here

# Check result later
await asyncio.sleep(2)  # Simulate doing other work
result = await client.get_task_result(task_id)
if result:
    print(f"Result: {result.result}")
```

### When to Use

✅ **Use non-blocking when:**
- Handling web requests (fast response times)
- Task takes time to complete
- You don't need the result immediately
- Fire-and-forget scenarios
- Processing multiple tasks in parallel

❌ **Don't use non-blocking when:**
- You need the result immediately
- Next steps depend on task result
- Task completes very quickly and you need the value

### Example: Fast Web Response

```python
@app.post("/process-async/")
async def process_async(data: dict):
    """Non-blocking - returns immediately."""
    # Returns immediately with task ID
    task_id = await client.delay("process_data", data, priority="high")

    # Response is instant!
    return {"task_id": task_id, "status": "processing"}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Check result later."""
    result = await client.get_task_result(task_id)
    if result:
        return {"status": result.status, "result": result.result}
    return {"status": "pending"}
```

**Benefit:** Web request returns instantly, task processes in background.

---

## How `delay()` Works Internally

The `delay()` method is implemented as:

```python
async def delay(self, task_name: str, *args, **kwargs) -> str:
    """Submit a task and return immediately with task ID (non-blocking)."""
    # 1. Create task object (fast, synchronous)
    task = Task(name=task_name, args=args, kwargs=kwargs, ...)

    # 2. Store pending result (fast, synchronous)
    self.task_results[task.id] = TaskResult(
        task_id=task.id,
        status=TaskStatus.PENDING,
        ...
    )

    # 3. Schedule submission in background (does NOT await!)
    asyncio.create_task(self._submit_task_internal(task))

    # 4. Return immediately (non-blocking!)
    return task.id
```

**Key:** Uses `asyncio.create_task()` without `await`, so it schedules the task but doesn't wait for it.

---

## Retrieving Results

### Option 1: Poll for Results

```python
# Submit task (non-blocking)
task_id = await client.delay("long_task", data)

# Poll periodically
while True:
    result = await client.get_task_result(task_id)
    if result and result.status != TaskStatus.PENDING:
        break
    await asyncio.sleep(0.5)  # Wait before polling again

# Result is ready
print(f"Result: {result.result}")
```

### Option 2: Check Once Later

```python
# Submit task
task_id = await client.delay("long_task", data)

# Do other work...
await do_other_work()

# Check if ready
result = await client.get_task_result(task_id)
if result and result.status == TaskStatus.SUCCESS:
    print(f"Result: {result.result}")
else:
    print("Still processing or failed")
```

### Option 3: Use Callbacks (Reactive)

```python
# Submit with callback
task_id = await client.delay_with_callback(
    "long_task",
    callback_address="tcp://localhost:6000",
    data,
    callback_data={"request_id": 123}
)

# Callback listener will be notified when complete
# (See callback documentation for details)
```

---

## Performance Comparison

### Blocking Pattern Performance

```python
# Blocking: Sequential processing
start = time.time()
results = []
for item in items:  # 100 items
    result = await client.submit_task("process", item)  # Waits each time
    results.append(result)
duration = time.time() - start
# Duration: ~50 seconds (if each task takes 0.5s)
```

**Problem:** Processes one at a time. Total time = sum of all task times.

### Non-Blocking Pattern Performance

```python
# Non-blocking: Parallel processing
start = time.time()
task_ids = []
for item in items:  # 100 items
    task_id = await client.delay("process", item)  # Returns immediately
    task_ids.append(task_id)

# All tasks submitted in < 1 second!
print(f"All tasks submitted in {time.time() - start:.2f}s")

# Wait for all results
await asyncio.sleep(5)  # Give tasks time to complete
results = []
for task_id in task_ids:
    result = await client.get_task_result(task_id)
    results.append(result)

duration = time.time() - start
# Duration: ~5 seconds (all tasks run in parallel)
```

**Benefit:** Submits all tasks immediately, processes in parallel. Total time = max task time.

---

## Real-World Patterns

### Pattern 1: Web API Background Processing

```python
from fastapi import FastAPI, BackgroundTasks
from fastqueue import Client

app = FastAPI()
client = Client()

@app.on_event("startup")
async def startup():
    await client.start()

@app.post("/users/")
async def create_user(user_data: dict):
    """Create user and send welcome email in background."""
    # 1. Save user to database (fast, synchronous)
    user = db.save_user(user_data)

    # 2. Send welcome email in background (non-blocking!)
    task_id = await client.delay(
        "send_welcome_email",
        user.id,
        user.email,
        priority="normal"
    )

    # 3. Return immediately (fast response!)
    return {
        "user_id": user.id,
        "email_task_id": task_id,
        "message": "User created, welcome email sending"
    }
```

### Pattern 2: Batch Processing

```python
async def process_batch(items: list):
    """Process many items in parallel."""
    # Submit all tasks (non-blocking)
    task_ids = []
    for item in items:
        task_id = await client.delay("process_item", item)
        task_ids.append(task_id)

    print(f"Submitted {len(task_ids)} tasks")

    # Wait for completion
    completed = 0
    while completed < len(task_ids):
        completed = 0
        for task_id in task_ids:
            result = await client.get_task_result(task_id)
            if result and result.status != TaskStatus.PENDING:
                completed += 1

        print(f"Progress: {completed}/{len(task_ids)}")
        await asyncio.sleep(1)

    print("All tasks complete!")
```

### Pattern 3: Workflow with Dependencies

```python
async def complex_workflow(data: dict):
    """Multi-stage workflow with dependencies."""
    # Stage 1: Process data (blocking - need result)
    result1 = await client.submit_task("stage1_process", data)

    # Stage 2: Two parallel tasks (non-blocking)
    task_id_2a = await client.delay("stage2a_transform", result1.result)
    task_id_2b = await client.delay("stage2b_validate", result1.result)

    # Wait for both
    result2a = await client.get_task_result(task_id_2a)
    result2b = await client.get_task_result(task_id_2b)

    # Stage 3: Final processing (blocking - need final result)
    final_result = await client.submit_task(
        "stage3_merge",
        result2a.result,
        result2b.result
    )

    return final_result.result
```

### Pattern 4: Fire and Forget

```python
@app.post("/analytics/")
async def track_event(event_data: dict):
    """Track analytics event."""
    # Fire and forget - don't care about result
    await client.delay("track_analytics", event_data, priority="low")

    # Return immediately
    return {"status": "tracked"}
```

---

## Best Practices

### 1. Default to Non-Blocking

```python
# GOOD - Fast response
task_id = await client.delay("send_email", email)
return {"task_id": task_id}

# BAD - Slow response
result = await client.submit_task("send_email", email)
return {"result": result}
```

### 2. Use Blocking Only When Necessary

```python
# GOOD - Need the result
processed_data = await client.submit_task("process", data)
return {"data": processed_data.result}

# BAD - Don't need the result
result = await client.submit_task("log_event", event)  # Why wait?
```

### 3. Handle Missing Results Gracefully

```python
# GOOD - Check if result exists
result = await client.get_task_result(task_id)
if result:
    if result.status == TaskStatus.SUCCESS:
        return {"result": result.result}
    else:
        return {"error": result.error}
else:
    return {"status": "still_processing"}

# BAD - Assume result exists
result = await client.get_task_result(task_id)
return {"result": result.result}  # Might be None!
```

### 4. Use Appropriate Timeouts

```python
# GOOD - With timeout
task_id = await client.delay("task", data)
start = time.time()
while time.time() - start < 30:  # 30 second timeout
    result = await client.get_task_result(task_id)
    if result and result.status != TaskStatus.PENDING:
        return result
    await asyncio.sleep(0.5)
raise TimeoutError("Task took too long")

# BAD - Infinite wait
while True:
    result = await client.get_task_result(task_id)
    if result:
        return result
```

---

## Common Pitfalls

### Pitfall 1: Blocking in Request Handlers

```python
# ❌ BAD - Blocks request
@app.post("/process/")
async def process(data: dict):
    result = await client.submit_task("heavy_task", data)
    return {"result": result.result}

# ✅ GOOD - Returns immediately
@app.post("/process/")
async def process(data: dict):
    task_id = await client.delay("heavy_task", data)
    return {"task_id": task_id}
```

### Pitfall 2: Not Handling Pending Status

```python
# ❌ BAD - Assumes immediate completion
task_id = await client.delay("task", data)
result = await client.get_task_result(task_id)
return result.result  # Might be None if still pending!

# ✅ GOOD - Check status
task_id = await client.delay("task", data)
result = await client.get_task_result(task_id)
if result and result.status == TaskStatus.SUCCESS:
    return result.result
else:
    return {"status": "processing", "task_id": task_id}
```

### Pitfall 3: Over-Polling

```python
# ❌ BAD - Polls too frequently
while True:
    result = await client.get_task_result(task_id)
    if result:
        break
    await asyncio.sleep(0.01)  # Polls 100 times per second!

# ✅ GOOD - Reasonable poll interval
while True:
    result = await client.get_task_result(task_id)
    if result:
        break
    await asyncio.sleep(0.5)  # Polls 2 times per second
```

---

## See Also

- [Client Guide](clients.md) - Client API reference
- [FastAPI Integration](fastapi.md) - Web application patterns
- [API Reference](api.md) - Complete API documentation
