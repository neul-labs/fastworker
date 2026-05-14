# FastWorker

**No Redis. No RabbitMQ. Just Python.**

[![PyPI version](https://badge.fury.io/py/fastworker.svg)](https://badge.fury.io/py/fastworker)
[![Python](https://img.shields.io/pypi/pyversions/fastworker.svg)](https://pypi.org/project/fastworker/)
[![Downloads](https://static.pepy.tech/badge/fastworker)](https://pepy.tech/project/fastworker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://neul-labs.github.io/fastworker/)

Background tasks in 30 seconds. Zero infrastructure.

```bash
pip install fastworker
```

## Why FastWorker?

| | FastWorker | Celery + Redis | RabbitMQ | AWS SQS |
|---|---|---|---|---|
| **External dependencies** | 0 | 2+ (broker + backend) | 1+ (RabbitMQ) | SQS + IAM |
| **Setup time** | 30 seconds | 30+ minutes | 30+ minutes | 15+ minutes |
| **Built-in dashboard** | Yes | No (needs Flower) | No (needs RabbitMQ UI) | No (needs CloudWatch) |
| **Worker discovery** | Automatic | Manual config | Manual config | None |
| **Cron/periodic tasks** | Built-in | needs celery-beat | needs scheduler | needs CloudWatch Events |
| **FastAPI integration** | Native (`FastWorker(app)`) | Manual | Manual | Manual |
| **Lines of config** | 1 | 15+ | 20+ | 10+ |

**Celery — 10+ lines of config:**

```python
# celery_app.py
from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

```bash
redis-server &                        # broker
celery -A celery_app worker &         # worker
celery -A celery_app beat &           # scheduler (for periodic tasks)
flower -A celery_app &                # monitoring (optional)
```

**FastWorker — 1 line:**

```python
# mytasks.py
from fastworker import task

@task
def add(x: int, y: int) -> int:
    return x + y
```

```bash
fastworker control-plane --task-modules mytasks
```

## Features

- **Zero Infrastructure** — No Redis, RabbitMQ, or message broker. Pure Python.
- **FastAPI Native** — `FastWorker(app)` auto-wires lifecycle, feels like a built-in feature.
- **Periodic & Cron Tasks** — `@task(repeat_interval=60)` or `@task(cron="0 */6 * * *")`. Built-in, no beat scheduler.
- **Built-in Dashboard** — Real-time web UI with dark mode. Workers, queues, task history. No extra setup.
- **Automatic Worker Discovery** — Workers and clients find each other on the network. Zero config.
- **Priority Queues** — CRITICAL, HIGH, NORMAL, LOW. Tasks routed by urgency.
- **Result Caching** — LRU cache with configurable TTL and size limits.
- **Task Callbacks** — Real-time notifications when tasks complete.
- **OpenTelemetry** — Optional distributed tracing and metrics.

FastWorker is designed for moderate-scale Python applications (1K-10K tasks/min). For extreme scale or complex workflows, see [Limitations & Scope](documentation/docs/limitations.md).

## Quick Start

### 1. Install

```bash
pip install fastworker
```

### 2. Define Tasks

```python
# mytasks.py
from fastworker import task

@task
def add(x: int, y: int) -> int:
    return x + y

@task(repeat_interval=300)
def refresh_cache():
    return {"cache": "refreshed"}
```

### 3. Run

```bash
fastworker control-plane --task-modules mytasks
```

The dashboard opens at http://127.0.0.1:8080.

Submit tasks:
```bash
fastworker submit --task-name add --args 5 3
fastworker submit --task-name add --args 10 20 --non-blocking
```

## FastAPI Integration (v0.3.0)

```python
from fastapi import FastAPI
from fastworker.integration.fastapi import FastWorker

app = FastAPI()
fw = FastWorker(app)  # done — lifecycle, discovery, everything


@task
def send_welcome_email(user_id: int, email: str) -> str:
    return f"Welcome email sent to {email}"


@app.post("/users/{user_id}/welcome")
async def welcome_user(user_id: int, email: str):
    task_id = await fw.delay("send_welcome_email", user_id, email)
    return {"task_id": task_id, "status": "queued"}


@app.get("/health")
async def health():
    return {"status": "healthy", "workers_online": fw.worker_count}
```

```bash
# Terminal 1
fastworker control-plane --task-modules app

# Terminal 2
uvicorn app:app --reload
```

[Full FastAPI docs &rarr;](documentation/docs/integration/fastapi.md)

## Periodic & Cron Tasks (v0.3.0)

```python
@task(repeat_interval=60)        # every 60 seconds
def heartbeat():
    ...

@task(cron="*/5 * * * *")        # every 5 minutes
def sync_data():
    ...

@task(cron="0 9 * * 1-5")        # weekdays at 9am
def morning_report():
    ...

@task(repeat_interval=30, repeat_count=100)  # exactly 100 times
def limited_job():
    ...
```

[Periodic tasks docs &rarr;](documentation/docs/guide/periodic-tasks.md)

## Project Structure — Grow From One File

FastWorker scales with your project:

```
# Level 1: Single file
mytasks.py

# Level 2: Package
tasks/
├── __init__.py
├── emails.py
└── reports.py

# Level 3: Organized
app/
├── tasks/
│   ├── background.py
│   └── scheduled.py
├── services/
└── models/

# Level 4: FastAPI
app/
├── api/
├── tasks/
├── main.py      # FastWorker(app)
└── ...
```

[Project structure guide &rarr;](documentation/docs/getting-started/project-structure.md)

## Client Usage

```python
from fastworker import Client

client = Client()
await client.start()

# Non-blocking — returns task ID immediately
task_id = await client.delay("add", 5, 3)

# Blocking — waits for result
result = await client.submit_task("add", args=(5, 3))
print(result.result)  # 8

# Batch submit
task_ids = await client.submit_batch([
    {"task_name": "add", "args": (1, 2)},
    {"task_name": "add", "args": (3, 4)},
])

# With callback
task_id = await client.delay_with_callback(
    "process_data", "tcp://127.0.0.1:6000", data,
    callback_data={"source": "api"},
)

# Query status
result = await client.get_task_result(task_id)

client.stop()
```

## CLI Reference

```bash
# Control plane (with dashboard)
fastworker control-plane --task-modules mytasks

# Subworker (for scaling)
fastworker subworker --worker-id w1 --control-plane-address tcp://127.0.0.1:5555 --task-modules mytasks

# Submit tasks
fastworker submit --task-name add --args 5 3
fastworker submit --task-name add --args 5 3 --non-blocking
fastworker submit --task-name add --args 5 3 --priority critical
fastworker submit --task-name report --args '"Q1"' --countdown 60

# List tasks
fastworker list --task-modules mytasks
fastworker list --task-modules mytasks --list-periodic
fastworker list --task-modules mytasks --tree

# Task management
fastworker status --task-id <uuid>
fastworker cancel --task-id <uuid>
```

## Dashboard

Start the control plane and open http://127.0.0.1:8080.

- Real-time worker status and load metrics
- Queue sizes by priority
- Task history with status and timing
- Cache utilization stats
- Dark mode
- Auto-refresh

```bash
fastworker control-plane --gui-host 0.0.0.0 --gui-port 9000 --task-modules mytasks
fastworker control-plane --no-gui --task-modules mytasks  # disable dashboard
```

## Extending FastWorker

Clear extension points for custom behavior:

- **Task Hooks** — `@task(before=..., after=...)` for per-task middleware
- **Event Bus** — Subscribe to `task.success`, `task.failure`, `worker.inactive` events
- **Custom Serializers** — Implement your own serialization format
- **Result Backends** — Redis, S3, PostgreSQL persistence

[Extending FastWorker &rarr;](documentation/docs/advanced/extending.md)

## Development

```bash
git clone https://github.com/neul-labs/fastworker.git
cd fastworker

uv sync
uv run pytest
uv run ruff check .
```

## Requirements

- Python 3.12+
- pynng >= 0.8.1
- pydantic >= 2.0.0

## Documentation

- [Index](documentation/docs/index.md)
- [Why FastWorker?](documentation/docs/getting-started/why-fastworker.md)
- [Project Structure](documentation/docs/getting-started/project-structure.md)
- [Architecture](documentation/docs/concepts/architecture.md)
- [FastAPI Integration](documentation/docs/integration/fastapi.md)
- [Periodic & Cron Tasks](documentation/docs/guide/periodic-tasks.md)
- [Management GUI](documentation/docs/gui.md)
- [Extending FastWorker](documentation/docs/advanced/extending.md)
- [Internals](documentation/docs/advanced/internals.md)
- [Benchmarks](documentation/docs/reference/benchmarks.md)
- [API Reference](documentation/docs/api.md)
- [Telemetry](documentation/docs/telemetry.md)
- [Limitations & Scope](documentation/docs/limitations.md)

## License

MIT — see [LICENSE](LICENSE).
