# FastAPI Integration

FastWorker provides a native FastAPI integration that feels like a built-in framework feature. One line wires everything up — no manual Client lifecycle, no null guards.

## Quick Start

```python
from fastapi import FastAPI
from fastworker import task
from fastworker.integration.fastapi import FastWorker

app = FastAPI()
fw = FastWorker(app)  # handles all lifecycle automatically


@task
def send_welcome_email(user_id: int, email: str) -> str:
    return f"Welcome email sent to {email}"


@app.post("/users/{user_id}/welcome")
async def welcome_user(user_id: int, email: str):
    task_id = await fw.delay("send_welcome_email", user_id, email)
    return {"task_id": task_id, "status": "queued"}
```

```bash
# Terminal 1: Control plane
fastworker control-plane --task-modules app

# Terminal 2: FastAPI app
uvicorn app:app --reload
```

## How It Works

`FastWorker(app)` creates an internal `Client` and registers it on the FastAPI lifespan:

- **Startup**: Client discovers the control plane automatically
- **Shutdown**: Client closes sockets gracefully
- **Existing lifespans**: If your app already has a lifespan (e.g., for database connections), FastWorker chains with it — both run correctly

### Lifespan Chaining

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def db_lifespan(app):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=db_lifespan)
fw = FastWorker(app)  # chains with db_lifespan automatically
```

## Available Methods

All methods are async and delegated to the internal Client:

| Method | Returns | Blocking? |
|---|---|---|
| `fw.delay(name, *args, **kwargs)` | `str` (task_id) | No |
| `fw.submit_task(name, args, kwargs)` | `TaskResult` | Yes |
| `fw.delay_with_callback(name, addr, *args)` | `str` (task_id) | No |
| `fw.submit_batch(tasks)` | `list[str]` | No |
| `fw.cancel_task(task_id)` | `bool` | — |
| `fw.get_task_result(task_id)` | `TaskResult \| None` | — |
| `fw.get_result(task_id)` | `TaskResult \| None` (local cache) | — |
| `fw.get_status(task_id)` | `TaskStatus \| None` | — |

## Priority & Scheduling

```python
from fastworker.tasks.models import TaskPriority

# High priority
await fw.delay("critical_task", data, priority=TaskPriority.CRITICAL)

# Delayed execution (10 seconds)
await fw.delay("reminder", user_id, countdown=10)

# Specific time
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
await fw.delay("scheduled_job", eta=eta)
```

## Health Check

The `worker_count` property reports discovered workers — perfect for health endpoints:

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "workers_online": fw.worker_count,
    }
```

## Custom Client Configuration

Pass keyword arguments through to the underlying `Client`:

```python
fw = FastWorker(
    app,
    client_kwargs={
        "timeout": 60,
        "retries": 5,
        "discovery_address": "tcp://127.0.0.1:5550",
    },
)
```

## Raw Client Access

If you need Client methods not directly exposed on `FastWorker`:

```python
# Access underlying client
fw.client.workers          # raw worker list
fw.client.pending_tasks    # queued tasks
```

## Task Callbacks

Get notified when a task completes:

```python
@app.post("/reports/generate")
async def generate_report(params: dict):
    task_id = await fw.delay_with_callback(
        "generate_report",
        "tcp://127.0.0.1:6000",  # callback listener address
        params,
        callback_data={"notify": "admin"},
    )
    return {"task_id": task_id}
```

## Batch Submission

Submit multiple tasks atomically:

```python
@app.post("/notify-all")
async def notify_all(user_ids: list[int]):
    tasks = [
        {"task_name": "send_notification", "args": (uid, "System update")}
        for uid in user_ids
    ]
    task_ids = await fw.submit_batch(tasks)
    return {"count": len(task_ids), "task_ids": task_ids}
```

## Project Structure for Larger Apps

For production FastAPI + FastWorker apps:

```
app/
├── api/
│   └── routes.py          # FastAPI endpoints
├── tasks/
│   ├── __init__.py         # imports all task modules
│   ├── emails.py           # @task email functions
│   └── reports.py          # @task report functions
├── services/               # business logic (shared)
├── models/                 # pydantic models
└── main.py                 # FastAPI app + FastWorker
```

`main.py`:
```python
from fastapi import FastAPI
from fastworker.integration.fastapi import FastWorker
from app.api.routes import router
from app.tasks import *  # noqa — registers @task functions

app = FastAPI()
app.include_router(router)
fw = FastWorker(app)
```

Start with:
```bash
fastworker control-plane --task-modules app.tasks
uvicorn app.main:app
```

## Migration from Manual Client

**Before (v0.2.x)**:
```python
client = Client()

@app.on_event("startup")
async def startup():
    await client.start()

@app.on_event("shutdown")
async def shutdown():
    client.stop()

@app.post("/task")
async def create(data: dict):
    if client:  # null guard
        task_id = await client.delay("my_task", data)
    return {"task_id": task_id}
```

**After (v0.3.0)**:
```python
fw = FastWorker(app)

@app.post("/task")
async def create(data: dict):
    task_id = await fw.delay("my_task", data)
    return {"task_id": task_id}
```
