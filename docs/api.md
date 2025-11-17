# API Reference

Complete API documentation for FastQueue components.

**See Also:**
- [Client Guide](clients.md) - Client usage examples
- [Control Plane](control_plane.md) - Control plane architecture
- [Configuration](configuration.md) - Environment variables
- [Troubleshooting](troubleshooting.md) - Common issues

## Core Components

### `@task` Decorator

Registers a function as a task that can be executed by workers.

```python
from fastqueue import task

@task
def my_function(x: int, y: int) -> int:
    return x + y
```

### `ControlPlaneWorker` Class

Control plane worker that manages subworkers and also processes tasks.

#### Constructor

```python
ControlPlaneWorker(
    worker_id: str = "control-plane",
    base_address: str = "tcp://127.0.0.1:5555",
    discovery_address: str = "tcp://127.0.0.1:5550",
    serialization_format: SerializationFormat = SerializationFormat.JSON,
    subworker_management_port: int = 5560,
    result_cache_max_size: int = 10000,
    result_cache_ttl_seconds: int = 3600
)
```

#### Methods

- `start()` - Start the control plane worker
- `stop()` - Stop the control plane worker
- `get_subworker_status()` - Get status of all subworkers

### `SubWorker` Class

Subworker that registers with control plane and processes tasks.

#### Constructor

```python
SubWorker(
    worker_id: str,
    control_plane_address: str,
    base_address: str = "tcp://127.0.0.1:5555",
    discovery_address: str = "tcp://127.0.0.1:5550",
    serialization_format: SerializationFormat = SerializationFormat.JSON
)
```

#### Methods

- `start()` - Start the subworker and register with control plane
- `stop()` - Stop the subworker

### `Client` Class

Client for submitting tasks to workers with built-in service discovery.

#### Constructor

```python
Client(
    discovery_address: str = "tcp://127.0.0.1:5550",
    serialization_format: SerializationFormat = SerializationFormat.JSON,
    timeout: int = 30,
    retries: int = 3
)
```

#### Methods

- `start()` - Start the client
- `stop()` - Stop the client
- `submit_task(task_name: str, args: tuple = (), kwargs: dict = {}, priority: TaskPriority = TaskPriority.NORMAL)` - Submit a task and wait for result
- `delay(task_name: str, *args, priority: TaskPriority = TaskPriority.NORMAL, **kwargs)` - Submit a task and return task ID immediately (non-blocking)
- `delay_with_callback(task_name: str, callback_address: str, *args, callback_data: dict = None, priority: TaskPriority = TaskPriority.NORMAL, **kwargs)` - Submit a task with callback notification when complete
- `get_result(task_id: str)` - Get task result from local cache
- `get_task_result(task_id: str)` - Query task result from control plane's result cache
- `get_status(task_id: str)` - Get task status by task ID

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

### `CallbackInfo`

Represents callback information for task completion notifications.

Properties:
- `address: str` - NNG address to send callback notification to
- `data: Optional[dict]` - Additional data to send with callback

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