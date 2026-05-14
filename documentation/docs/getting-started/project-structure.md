# Project Structure — From Single File to Production

FastWorker grows with your project. Start with one file and refactor as you scale.

## Level 1: Single File

**When:** Prototyping, small scripts, < 5 tasks.

```
project/
└── mytasks.py
```

```python
# mytasks.py
from fastworker import task

@task
def add(x: int, y: int) -> int:
    return x + y

@task
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

```bash
fastworker control-plane --task-modules mytasks
fastworker submit --task-name add --args 5 3
```

Everything in one file. `fastworker` discovers all `@task`-decorated functions automatically.

## Level 2: Package

**When:** 5-15 tasks, multiple developers, tasks are getting hard to find.

```
project/
└── tasks/
    ├── __init__.py     # re-exports everything
    ├── emails.py
    └── reports.py
```

```python
# tasks/__init__.py
from project.tasks.emails import *  # noqa
from project.tasks.reports import *  # noqa
```

```bash
fastworker control-plane --task-modules project.tasks
```

The `__init__.py` acts as a single import point. Add new task modules freely — just re-export them.

## Level 3: Organized

**When:** 15+ tasks, shared business logic, need separation of concerns.

```
project/
└── app/
    ├── tasks/
    │   ├── __init__.py
    │   ├── background.py    # one-shot tasks
    │   └── scheduled.py     # periodic/cron tasks
    ├── services/
    │   └── notifications.py # business logic
    └── models/
        └── schemas.py       # pydantic models
```

Tasks are thin wrappers. Business logic lives in `services/`:

```python
# app/tasks/background.py
from fastworker import task
from app.services.notifications import send_email

@task
def notify_user(user_id: int, message: str):
    return send_email(user_id, message)
```

```bash
fastworker control-plane --task-modules app.tasks
```

## Level 4: FastAPI Integration

**When:** Building a web API with background processing.

```
project/
└── app/
    ├── api/
    │   └── routes.py         # FastAPI endpoints
    ├── tasks/
    │   ├── __init__.py
    │   ├── background.py
    │   └── scheduled.py
    ├── services/
    ├── models/
    └── main.py               # FastAPI app + FastWorker
```

```python
# app/main.py
from fastapi import FastAPI
from fastworker.integration.fastapi import FastWorker
from app.api.routes import router
import app.tasks  # registers @task functions

app = FastAPI()
app.include_router(router)
fw = FastWorker(app)
```

```bash
# Terminal 1
fastworker control-plane --task-modules app.tasks

# Terminal 2
uvicorn app.main:app --reload
```

## When to Move to the Next Level

| Signal | Action |
|---|---|
| Scrolling past 100 lines in one task file | Move to package |
| Copy-pasting logic between tasks | Extract to services/ |
| Need cron or periodic execution | Add scheduled.py |
| Building a web UI for your app | Add FastAPI integration |
| Tasks sharing database models | Create models/ directory |

## CLI: View Task Tree

```bash
fastworker list --tree --task-modules app.tasks
```

Shows the module hierarchy with task names and schedule metadata.
