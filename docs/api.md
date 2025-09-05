# API Reference

## Core Components

### `@task` Decorator

Registers a function as a task that can be executed by workers.

```python
from fastqueue import task

@task
def my_function(x: int, y: int) -> int:
    return x + y
```

### `Worker` Class

Worker that executes tasks using nng patterns with built-in service discovery.

#### Constructor

```python
Worker(worker_id: str, base_address: str = "tcp://127.0.0.1:5555", discovery_address: str = "tcp://127.0.0.1:5550", serialization_format: SerializationFormat = SerializationFormat.JSON)
```

#### Methods

- `start()` - Start the worker
- `stop()` - Stop the worker

### `Client` Class

Client for submitting tasks to workers with built-in service discovery.

#### Constructor

```python
Client(discovery_address: str = "tcp://127.0.0.1:5550", serialization_format: SerializationFormat = SerializationFormat.JSON, timeout: int = 30, retries: int = 3)
```

#### Methods

- `start()` - Start the client
- `stop()` - Stop the client
- `submit_task(task_name: str, args: tuple = (), kwargs: dict = {}, priority: TaskPriority = TaskPriority.NORMAL)` - Submit a task
- `delay(task_name: str, *args, priority: TaskPriority = TaskPriority.NORMAL, **kwargs)` - Submit a task and return immediately

## Task Priority

Tasks can be submitted with different priority levels:

- `TaskPriority.CRITICAL`
- `TaskPriority.HIGH`
- `TaskPriority.NORMAL`
- `TaskPriority.LOW`

## Serialization Formats

Supported serialization formats:

- `SerializationFormat.JSON` (default)
- `SerializationFormat.PICKLE`

## Task Models

### `Task`

Represents a task to be executed.

Properties:
- `id: str` - Unique task ID
- `name: str` - Task function name
- `args: tuple` - Positional arguments
- `kwargs: dict` - Keyword arguments
- `priority: TaskPriority` - Task priority
- `created_at: datetime` - Creation timestamp
- `started_at: Optional[datetime]` - Start timestamp
- `completed_at: Optional[datetime]` - Completion timestamp
- `status: TaskStatus` - Current status
- `result: Any` - Task result
- `error: Optional[str]` - Error message if failed

### `TaskResult`

Represents the result of a task execution.

Properties:
- `task_id: str` - Task ID
- `status: TaskStatus` - Execution status
- `result: Any` - Task result
- `error: Optional[str]` - Error message if failed
- `started_at: Optional[datetime]` - Start timestamp
- `completed_at: Optional[datetime]` - Completion timestamp

## Enums

### `TaskPriority`

- `LOW`
- `NORMAL`
- `HIGH`
- `CRITICAL`

### `TaskStatus`

- `PENDING`
- `STARTED`
- `SUCCESS`
- `FAILURE`

### `SerializationFormat`

- `JSON`
- `PICKLE`