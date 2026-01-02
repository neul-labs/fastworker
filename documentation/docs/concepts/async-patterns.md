# Async Patterns

FastWorker provides both **blocking** and **non-blocking** task submission patterns. Understanding the difference is crucial for building responsive applications.

## Quick Comparison

| Method | Behavior | Returns | Use Case |
|--------|----------|---------|----------|
| `submit_task()` | **Blocking** - Waits for result | `TaskResult` | When you need the result immediately |
| `delay()` | **Non-blocking** - Returns immediately | `task_id` (str) | Background tasks, fire-and-forget |
| `delay_with_callback()` | **Non-blocking** - Returns immediately | `task_id` (str) | Reactive workflows with notifications |

---

## Blocking: `submit_task()`

Submits a task and **waits** for the result before continuing.

```python
from fastworker import Client
from fastworker.tasks.models import TaskPriority

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

### When to Use Blocking

✅ **Use when:**

- You need the result immediately
- The calling code depends on the task result
- Tasks complete quickly (< 1 second)

❌ **Don't use when:**

- Handling web requests (causes slow response times)
- Task takes a long time to complete
- Processing multiple tasks in parallel

---

## Non-Blocking: `delay()`

Submits a task and **returns immediately** with a task ID. The task executes in the background.

```python
from fastworker import Client

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

### When to Use Non-Blocking

✅ **Use when:**

- Handling web requests (fast response times)
- Task takes time to complete
- Fire-and-forget scenarios
- Processing multiple tasks in parallel

❌ **Don't use when:**

- You need the result immediately
- Next steps depend on task result

---

## Performance Comparison

### Blocking (Sequential)

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

### Non-Blocking (Parallel)

```python
# Non-blocking: Parallel processing
start = time.time()
task_ids = []
for item in items:  # 100 items
    task_id = await client.delay("process", item)  # Returns immediately
    task_ids.append(task_id)

# All tasks submitted in < 1 second!
print(f"All tasks submitted in {time.time() - start:.2f}s")

# Collect results later
await asyncio.sleep(5)  # Give tasks time to complete
results = [await client.get_task_result(tid) for tid in task_ids]
# Duration: ~5 seconds (all tasks run in parallel)
```

**Benefit:** Submits all tasks immediately, processes in parallel.

---

## Real-World Patterns

### Pattern 1: Web API Background Processing

```python
from fastapi import FastAPI
from fastworker import Client

app = FastAPI()
client = Client()

@app.post("/users/")
async def create_user(user_data: dict):
    """Create user and send welcome email in background."""
    # 1. Save user to database (fast)
    user = db.save_user(user_data)

    # 2. Send welcome email in background (non-blocking!)
    task_id = await client.delay("send_welcome_email", user.id, user.email)

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
    task_ids = [await client.delay("process_item", item) for item in items]
    print(f"Submitted {len(task_ids)} tasks")

    # Wait for completion
    while True:
        results = [await client.get_task_result(tid) for tid in task_ids]
        completed = sum(1 for r in results if r and r.status != "pending")
        print(f"Progress: {completed}/{len(task_ids)}")

        if completed == len(task_ids):
            break
        await asyncio.sleep(1)

    print("All tasks complete!")
```

### Pattern 3: Fire and Forget

```python
@app.post("/analytics/")
async def track_event(event_data: dict):
    """Track analytics event - don't care about result."""
    await client.delay("track_analytics", event_data, priority="low")
    return {"status": "tracked"}
```

---

## Retrieving Results

### Option 1: Poll for Results

```python
task_id = await client.delay("long_task", data)

# Poll periodically
while True:
    result = await client.get_task_result(task_id)
    if result and result.status != TaskStatus.PENDING:
        break
    await asyncio.sleep(0.5)

print(f"Result: {result.result}")
```

### Option 2: Use Callbacks

```python
task_id = await client.delay_with_callback(
    "long_task",
    callback_address="tcp://localhost:6000",
    data,
    callback_data={"request_id": 123}
)

# Callback listener will be notified when complete
```

---

## Best Practices

### 1. Default to Non-Blocking

```python
# Good - Fast response
task_id = await client.delay("send_email", email)
return {"task_id": task_id}

# Bad - Slow response
result = await client.submit_task("send_email", email)
return {"result": result}
```

### 2. Handle Missing Results

```python
# Good - Check if result exists
result = await client.get_task_result(task_id)
if result and result.status == TaskStatus.SUCCESS:
    return {"result": result.result}
else:
    return {"status": "processing", "task_id": task_id}

# Bad - Assume result exists
result = await client.get_task_result(task_id)
return {"result": result.result}  # Might be None!
```

### 3. Use Appropriate Poll Intervals

```python
# Good - Reasonable poll interval
await asyncio.sleep(0.5)  # Polls 2 times per second

# Bad - Too frequent
await asyncio.sleep(0.01)  # Polls 100 times per second!
```

---

## Common Pitfalls

### Blocking in Request Handlers

```python
# ❌ Bad - Blocks request
@app.post("/process/")
async def process(data: dict):
    result = await client.submit_task("heavy_task", data)
    return {"result": result.result}

# ✅ Good - Returns immediately
@app.post("/process/")
async def process(data: dict):
    task_id = await client.delay("heavy_task", data)
    return {"task_id": task_id}
```

### Not Handling Pending Status

```python
# ❌ Bad - Assumes immediate completion
task_id = await client.delay("task", data)
result = await client.get_task_result(task_id)
return result.result  # Might be None!

# ✅ Good - Check status
result = await client.get_task_result(task_id)
if result and result.status == TaskStatus.SUCCESS:
    return result.result
```
