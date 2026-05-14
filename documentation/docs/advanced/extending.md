# Extending FastWorker

FastWorker is designed with clear extension points. You can customize serialization, add middleware, hook into task lifecycle events, or build custom backends.

## Extension Points Overview

| Extension Point | How | When to Use |
|---|---|---|
| Task Hooks (before/after) | `@task(before=..., after=...)` | Logging, metrics, auth context per task |
| Task Middleware | `task_registry.add_middleware(hook)` | Global pre/post processing for all tasks |
| Custom Serializer | Implement `TaskSerializer` protocol | Avro, MessagePack, custom binary formats |
| Event Bus Listener | `event_bus.subscribe("task.*", handler)` | Slack notifications, audit trails, webhooks |
| Custom NNG Pattern | Subclass `NNGPattern` | Custom protocol adapters |
| Result Backend | Implement `ResultBackend` protocol | Redis, S3, PostgreSQL result persistence |
| Worker Hooks | `Worker.on_task_start / on_task_end` | Custom instrumentation, resource tracking |

## Task Hooks

Attach per-task before/after hooks declaratively:

```python
from fastworker import task

def log_start(task):
    print(f"Starting task {task.name} ({task.id})")

def record_metrics(task):
    print(f"Task {task.name} completed: {task.status}")

@task(before=log_start, after=record_metrics)
def process_order(order_id: int):
    ...
```

Hooks receive the `Task` object and can be sync or async.

## Event Bus

Subscribe to lifecycle events for cross-cutting concerns:

```python
from fastworker.utils.event_bus import event_bus

@event_bus.subscribe("task.failure")
async def on_task_failure(event):
    # event is a dict with: task_id, name, error, status
    await slack.notify(f"Task {event['task_id']} failed: {event['error']}")

@event_bus.subscribe("task.success")
async def on_task_success(event):
    await metrics.increment("tasks.completed")

@event_bus.subscribe("worker.inactive")
async def on_worker_down(event):
    await pagerduty.alert(f"Worker {event['worker_id']} is down")
```

Available events:
- `task.queued`, `task.started`, `task.success`, `task.failure`, `task.cancelled`
- `worker.registered`, `worker.active`, `worker.inactive`
- `task.retrying`

## Custom Serializer

Implement a custom serializer for non-JSON formats:

```python
import msgpack
from fastworker.tasks.serializer import TaskSerializer

class MessagePackSerializer:
    @staticmethod
    def serialize(data: dict) -> bytes:
        return msgpack.packb(data)

    @staticmethod
    def deserialize(data: bytes) -> dict:
        return msgpack.unpackb(data)
```

## Custom Result Backend

Persist task results beyond the in-memory cache:

```python
import redis.asyncio as redis

class RedisResultBackend:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def store(self, task_id: str, result: dict, ttl: int = 3600):
        await self.redis.setex(task_id, ttl, json.dumps(result))

    async def get(self, task_id: str) -> dict | None:
        data = await self.redis.get(task_id)
        return json.loads(data) if data else None
```

## NNG Pattern Subclass

For custom protocol adapters, subclass the pattern base:

```python
from fastworker.patterns.nng_patterns import NNGPattern

class CustomPattern(NNGPattern):
    async def start(self):
        # Custom initialization
        ...

    async def send(self, data: bytes):
        # Custom send logic
        ...

    async def recv(self) -> bytes:
        # Custom receive logic
        ...
```

## Complete Example: Slack Notifier Hook

```python
from fastworker import task
from fastworker.utils.event_bus import event_bus
import httpx


async def notify_slack(event):
    task_id = event.get("task_id", "unknown")
    name = event.get("name", "unknown")
    error = event.get("error", "")
    await httpx.AsyncClient().post(
        "https://hooks.slack.com/services/...",
        json={"text": f"Task *{name}* ({task_id}) failed: {error}"},
    )

event_bus.subscribe("task.failure", notify_slack)
```

Place this in a module that's imported before the control plane starts.
