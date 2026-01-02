# Tasks

Tasks are Python functions decorated with `@task` that can be executed by FastWorker workers.

## Defining Tasks

Use the `@task` decorator to register a function as a task:

```python
from fastworker import task

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

@task
def process_data(data: dict) -> dict:
    """Process some data."""
    return {"processed": True, "input": data}

@task
async def async_task(url: str) -> str:
    """Async task example."""
    # Async I/O operations
    return f"Fetched: {url}"
```

## Task Requirements

1. **Decorated with `@task`**: Required for registration
2. **Importable module**: Tasks must be in a module that can be imported
3. **Serializable arguments**: Arguments must be JSON-serializable (or Pickle-serializable if using Pickle format)
4. **Serializable return value**: Return values must be serializable

## Loading Tasks

Workers load tasks from modules specified with `--task-modules`:

```bash
# Load from single module
fastworker control-plane --task-modules mytasks

# Load from multiple modules (comma-separated)
fastworker control-plane --task-modules mytasks,other_tasks,more_tasks
```

## Task Priority

Tasks can be submitted with different priority levels:

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

### Priority Levels

| Priority | Value | Description |
|----------|-------|-------------|
| `CRITICAL` | 0 | Highest priority, processed first |
| `HIGH` | 1 | High priority |
| `NORMAL` | 2 | Default priority |
| `LOW` | 3 | Lowest priority, processed last |

## Task Status

Tasks have the following status values:

| Status | Description |
|--------|-------------|
| `PENDING` | Task submitted, waiting for processing |
| `STARTED` | Task is being processed |
| `SUCCESS` | Task completed successfully |
| `FAILURE` | Task failed with an error |

## Task Result

When a task completes, you receive a `TaskResult`:

```python
result = await client.get_task_result(task_id)

if result:
    print(f"Task ID: {result.task_id}")
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")
    print(f"Started: {result.started_at}")
    print(f"Completed: {result.completed_at}")
```

## Best Practices

### 1. Keep Tasks Focused

```python
# Good - single responsibility
@task
def send_email(to: str, subject: str, body: str) -> bool:
    return email_service.send(to, subject, body)

# Bad - too many responsibilities
@task
def do_everything(user_id: int):
    user = get_user(user_id)
    send_email(user.email, ...)
    update_database(...)
    notify_slack(...)
```

### 2. Handle Errors Gracefully

```python
@task
def risky_task(data: dict) -> dict:
    try:
        return process(data)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise  # Re-raise to mark task as failed
```

### 3. Use Type Hints

```python
@task
def typed_task(name: str, count: int) -> dict[str, any]:
    return {"name": name, "count": count}
```

### 4. Avoid Large Arguments

```python
# Bad - large data in arguments
@task
def process_file(file_contents: bytes):  # 100MB file!
    return analyze(file_contents)

# Good - pass reference, load in worker
@task
def process_file(file_path: str):
    with open(file_path, 'rb') as f:
        return analyze(f.read())
```

### 5. Make Tasks Idempotent When Possible

```python
@task
def update_user_status(user_id: int, status: str) -> bool:
    # Safe to call multiple times
    user = get_user(user_id)
    if user.status != status:
        user.status = status
        user.save()
    return True
```

## Serialization

### JSON (Default)

JSON-serializable types:

- `str`, `int`, `float`, `bool`, `None`
- `list`, `dict`
- Objects with `.dict()` or `.model_dump()` methods (Pydantic)

```python
@task
def json_task(data: dict) -> dict:
    return {"result": data["value"] * 2}
```

### Pickle

For complex Python objects, use Pickle serialization:

```bash
export FASTWORKER_SERIALIZATION_FORMAT=PICKLE
```

!!! warning
    Only use Pickle in trusted environments. Never use Pickle with untrusted task data.

### Common Serialization Issues

```python
# Bad - datetime not JSON serializable
@task
def bad_task():
    return {"timestamp": datetime.now()}

# Good - convert to string
@task
def good_task():
    return {"timestamp": datetime.now().isoformat()}
```
