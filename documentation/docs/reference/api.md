# API Reference

Complete API documentation for FastWorker components.

## Core Components

### `@task` Decorator

Registers a function as a task that can be executed by workers.

```python
from fastworker import task

@task
def my_function(x: int, y: int) -> int:
    return x + y
```

---

## Client

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

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `discovery_address` | str | `tcp://127.0.0.1:5550` | Discovery address |
| `serialization_format` | SerializationFormat | `JSON` | Serialization format |
| `timeout` | int | `30` | Task timeout in seconds |
| `retries` | int | `3` | Number of retries |

#### Methods

##### `start()`

Start the client and connect to workers.

```python
await client.start()
```

##### `stop()`

Stop the client and close connections.

```python
client.stop()
```

##### `delay()`

Submit a task and return immediately with task ID (non-blocking).

```python
task_id = await client.delay(
    task_name: str,
    *args,
    priority: TaskPriority = TaskPriority.NORMAL,
    countdown: float = None,       # Delay in seconds before execution
    eta: datetime = None,           # Absolute execution time
    **kwargs
) -> str
```

##### `submit_task()`

Submit a task and wait for result (blocking).

```python
result = await client.submit_task(
    task_name: str,
    args: tuple = (),
    kwargs: dict = {},
    priority: TaskPriority = TaskPriority.NORMAL,
    countdown: float = None,
    eta: datetime = None
) -> TaskResult
```

##### `delay_with_callback()`

Submit a task with callback notification when complete.

```python
task_id = await client.delay_with_callback(
    task_name: str,
    callback_address: str,
    *args,
    callback_data: dict = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    countdown: float = None,
    eta: datetime = None,
    **kwargs
) -> str
```

##### `submit_batch()`

Submit multiple tasks atomically in a single network message.

```python
task_ids = await client.submit_batch(
    tasks: list[dict],
    default_priority: TaskPriority = TaskPriority.NORMAL
) -> list[str]
```

Each task dict accepts: `task_name` (required), `args`, `kwargs`, `priority`, `countdown`, `eta`.

##### `cancel_task()`

Cancel a queued or running task by ID.

```python
cancelled = await client.cancel_task(task_id: str) -> bool
```

##### `get_task_result()`

Query task result from control plane's result cache.

```python
result = await client.get_task_result(task_id: str) -> Optional[TaskResult]
```

##### `get_result()`

Get task result from local cache.

```python
result = client.get_result(task_id: str) -> Optional[TaskResult]
```

##### `get_status()`

Get task status by task ID.

```python
status = client.get_status(task_id: str) -> Optional[TaskStatus]
```

---

## Workers

### `ControlPlaneWorker` Class

Control plane worker that manages subworkers and processes tasks.

#### Constructor

```python
ControlPlaneWorker(
    worker_id: str = "control-plane",
    base_address: str = "tcp://127.0.0.1:5555",
    discovery_address: str = "tcp://127.0.0.1:5550",
    serialization_format: SerializationFormat = SerializationFormat.JSON,
    subworker_management_port: int = 5560,
    result_cache_max_size: int = 10000,
    result_cache_ttl_seconds: int = 3600,
    concurrency: int = 1
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `worker_id` | str | `"control-plane"` | Worker identifier |
| `base_address` | str | `"tcp://127.0.0.1:5555"` | Base address for task ports |
| `discovery_address` | str | `"tcp://127.0.0.1:5550"` | Discovery broadcast address |
| `serialization_format` | SerializationFormat | `JSON` | Serialization format |
| `subworker_management_port` | int | `5560` | Port for subworker management |
| `result_cache_max_size` | int | `10000` | Max cached results |
| `result_cache_ttl_seconds` | int | `3600` | Cache TTL in seconds |
| `concurrency` | int | `1` | Max concurrent task executions |

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
    serialization_format: SerializationFormat = SerializationFormat.JSON,
    concurrency: int = 1
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `worker_id` | str | Yes | Unique subworker identifier |
| `control_plane_address` | str | Yes | Address of the control plane |
| `base_address` | str | No | Base address for this subworker |
| `discovery_address` | str | No | Discovery address |
| `serialization_format` | SerializationFormat | No | Serialization format |
| `concurrency` | int | No | Max concurrent task executions |

#### Methods

- `start()` - Start the subworker and register with control plane
- `stop()` - Stop the subworker

---

## Models

### `Task`

Represents a task to be executed with a formal state machine lifecycle.

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Unique task ID |
| `name` | str | Task function name |
| `args` | tuple | Positional arguments |
| `kwargs` | dict | Keyword arguments |
| `priority` | TaskPriority | Task priority |
| `state` | TaskStatus | Current state machine state |
| `retry_count` | int | Number of retry attempts made |
| `max_retries` | int | Maximum retry attempts (0 = no retries) |
| `retry_delay` | float | Seconds between retries |
| `retry_backoff` | float | Exponential backoff multiplier |
| `timeout` | float | Optional — per-task timeout in seconds |
| `eta` | datetime | Optional — scheduled execution time |
| `assigned_worker` | str | Optional — worker assigned to execute |
| `created_at` | datetime | Creation timestamp |
| `started_at` | Optional[datetime] | Start timestamp |
| `completed_at` | Optional[datetime] | Completion timestamp |
| `result` | Any | Task result |
| `error` | Optional[str] | Error message if failed |

### `TaskResult`

Represents the result of a task execution.

| Property | Type | Description |
|----------|------|-------------|
| `task_id` | str | Task ID |
| `status` | TaskStatus | Execution status |
| `result` | Any | Task result |
| `error` | Optional[str] | Error message if failed |
| `started_at` | Optional[datetime] | Start timestamp |
| `completed_at` | Optional[datetime] | Completion timestamp |

### `CallbackInfo`

Represents callback information for task completion notifications.

| Property | Type | Description |
|----------|------|-------------|
| `address` | str | NNG address to send callback to |
| `data` | Optional[dict] | Additional callback data |

---

## Enums

### `TaskPriority`

Task priority levels.

| Value | Description |
|-------|-------------|
| `CRITICAL` | Highest priority (0) |
| `HIGH` | High priority (1) |
| `NORMAL` | Default priority (2) |
| `LOW` | Lowest priority (3) |

### `TaskStatus`

Task execution status (9-state state machine).

| Value | Description |
|-------|-------------|
| `PENDING` | Task created, not yet queued |
| `SCHEDULED` | Task delayed with ETA, waiting for execution time |
| `QUEUED` | Task in queue, waiting to be assigned |
| `ASSIGNED` | Task assigned to a worker |
| `RUNNING` | Task is being processed |
| `SUCCESS` | Task completed successfully (terminal) |
| `FAILURE` | Task failed with an error |
| `RETRYING` | Task is being retried (transitions back to QUEUED) |
| `CANCELLED` | Task was cancelled (terminal) |

### `SerializationFormat`

Serialization formats.

| Value | Description |
|-------|-------------|
| `JSON` | JSON serialization (default) |
| `PICKLE` | Python pickle serialization |

---

## CLI Commands

### `fastworker control-plane`

Start the control plane worker.

```bash
fastworker control-plane [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--worker-id` | `control-plane` | Worker identifier |
| `--base-address` | `tcp://127.0.0.1:5555` | Base address |
| `--discovery-address` | `tcp://127.0.0.1:5550` | Discovery address |
| `--subworker-port` | `5560` | Subworker management port |
| `--result-cache-size` | `10000` | Maximum cached results |
| `--result-cache-ttl` | `3600` | Cache TTL in seconds |
| `--task-modules` | - | Task modules to load |
| `--concurrency` | `1` | Max concurrent task executions |
| `--gui-host` | `127.0.0.1` | GUI host |
| `--gui-port` | `8080` | GUI port |
| `--no-gui` | - | Disable GUI |

### `fastworker subworker`

Start a subworker.

```bash
fastworker subworker [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--worker-id` | Yes | Worker identifier |
| `--control-plane-address` | Yes | Control plane address |
| `--base-address` | No | Base address |
| `--discovery-address` | No | Discovery address |
| `--task-modules` | No | Task modules to load |
| `--concurrency` | No | Max concurrent task executions |

### `fastworker submit`

Submit a task.

```bash
fastworker submit [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--task-name` | Task name to execute |
| `--args` | Task arguments |
| `--non-blocking` | Return immediately with task ID |
| `--countdown` | Delay execution by N seconds |
| `--eta` | Execute at specific ISO 8601 datetime |

### `fastworker cancel`

Cancel a task by ID.

```bash
fastworker cancel --task-id <uuid>
```

### `fastworker status`

Get task status.

```bash
fastworker status --task-id <uuid>
```

### `fastworker list`

List available tasks.

```bash
fastworker list --task-modules mytasks
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTWORKER_GUI_ENABLED` | `true` | Enable/disable the management GUI |
| `FASTWORKER_GUI_HOST` | `127.0.0.1` | GUI server host address |
| `FASTWORKER_GUI_PORT` | `8080` | GUI server port |
| `FASTWORKER_GUI_API_KEY` | — | API key for write endpoint authentication (Bearer token) |
| `FASTWORKER_GUI_CORS_ORIGIN` | `*` | Allowed CORS origin (comma-separated) |
| `FASTWORKER_WORKER_CONCURRENCY` | `1` | Default concurrency for all worker types |
| `FASTWORKER_SERIALIZATION_FORMAT` | `JSON` | Task serialization format (`JSON` or `PICKLE`) |
