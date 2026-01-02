# FastAPI Integration

FastWorker integrates seamlessly with FastAPI applications, providing a brokerless alternative to Celery.

## Basic Integration

### 1. Define Tasks

```python
# tasks.py
from fastworker import task

@task
def process_user_registration(user_id: int, email: str) -> dict:
    """Process user registration."""
    return {"user_id": user_id, "status": "registered"}

@task
def send_notification(user_id: int, message: str) -> dict:
    """Send notification to user."""
    return {"user_id": user_id, "notification_sent": True}
```

### 2. Configure FastAPI Application

```python
# main.py
from fastapi import FastAPI, HTTPException
from fastworker import Client

app = FastAPI(title="My FastAPI App")
client = Client()

@app.on_event("startup")
async def startup_event():
    """Initialize FastWorker client on startup."""
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up FastWorker client on shutdown."""
    client.stop()

@app.post("/register/")
async def register_user(user_id: int, email: str):
    """Register a new user."""
    task_id = await client.delay("process_user_registration", user_id, email)
    return {"message": "Registration started", "task_id": task_id}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    result = await client.get_task_result(task_id)
    if result:
        return {"status": result.status, "result": result.result}
    return {"status": "pending"}
```

### 3. Start Workers

```bash
# Terminal 1: Start control plane
fastworker control-plane --task-modules tasks

# Terminal 2: Start FastAPI
uvicorn main:app --reload
```

## Advanced Patterns

### Background Task Processing

```python
@app.post("/users/")
async def create_user(user_data: dict):
    """Create user and send welcome email in background."""
    # Save user synchronously
    user = db.save_user(user_data)

    # Send email in background (non-blocking)
    task_id = await client.delay("send_welcome_email", user.id, user.email)

    return {
        "user_id": user.id,
        "email_task_id": task_id,
        "message": "User created"
    }
```

### Error Handling

```python
@app.post("/process/")
async def process_with_fallback(data: dict):
    """Process data with error handling."""
    task_id = await client.delay("process_data", data)

    # Wait a bit and check result
    await asyncio.sleep(2)
    result = await client.get_task_result(task_id)

    if result:
        if result.status == "failure":
            raise HTTPException(status_code=500, detail=result.error)
        return {"result": result.result}

    return {"task_id": task_id, "status": "processing"}
```

### Health Check

```python
@app.get("/health/")
async def health_check():
    """Health check endpoint."""
    worker_count = len(client.workers) if hasattr(client, 'workers') else 0
    if worker_count > 0:
        return {"status": "healthy", "workers_online": worker_count}
    return {"status": "degraded", "workers_online": 0}
```

### Task Status Tracking

```python
from fastworker.tasks.models import TaskStatus

task_storage = {}

@app.post("/process-with-tracking/")
async def process_with_tracking(data: dict):
    """Process data with status tracking."""
    task_id = await client.delay("process_data", data)
    return {"task_id": task_id, "status": "processing"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    result = await client.get_task_result(task_id)
    if result:
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.status == "success" else None,
            "error": result.error if result.status == "failure" else None
        }
    return {"task_id": task_id, "status": "pending"}
```

## Dependency Injection

```python
from fastapi import Depends

async def get_fastworker_client():
    """Dependency to get FastWorker client."""
    return client

@app.post("/process/")
async def process_data(
    data: dict,
    fw_client: Client = Depends(get_fastworker_client)
):
    """Process data with injected client."""
    task_id = await fw_client.delay("process_data", data)
    return {"task_id": task_id}
```

## Task Callbacks

```python
@app.post("/process-with-callback/")
async def process_with_callback(data: dict, callback_url: str):
    """Process data with callback when finished."""
    task_id = await client.delay_with_callback(
        "process_data",
        callback_url,
        data,
        callback_data={"source": "fastapi"}
    )
    return {"task_id": task_id, "message": "Task submitted"}
```

## Configuration

### Environment-Based

```python
import os

DISCOVERY_ADDRESS = os.getenv("FASTWORKER_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550")
TIMEOUT = int(os.getenv("FASTWORKER_TIMEOUT", "30"))

client = Client(
    discovery_address=DISCOVERY_ADDRESS,
    timeout=TIMEOUT
)
```

### Lifespan Context (Modern FastAPI)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await client.start()
    yield
    # Shutdown
    client.stop()

app = FastAPI(lifespan=lifespan)
```

## Best Practices

1. **Initialize Client Once** - Create a single client instance per application
2. **Use Non-Blocking** - Use `delay()` for fast response times
3. **Handle Errors** - Implement fallback strategies
4. **Monitor Health** - Check worker availability
5. **Set Timeouts** - Configure appropriate timeouts
6. **Use Priorities** - Submit tasks with appropriate priority levels

## Full Example

```python
from fastapi import FastAPI, HTTPException
from fastworker import Client
from contextlib import asynccontextmanager
import os

# Configuration
DISCOVERY = os.getenv("FASTWORKER_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550")
client = Client(discovery_address=DISCOVERY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.start()
    yield
    client.stop()

app = FastAPI(title="FastWorker Example", lifespan=lifespan)

@app.post("/tasks/")
async def create_task(name: str, data: dict, priority: str = "normal"):
    """Submit a new task."""
    task_id = await client.delay(name, data, priority=priority)
    return {"task_id": task_id}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task result."""
    result = await client.get_task_result(task_id)
    if result:
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "error": result.error
        }
    return {"task_id": task_id, "status": "pending"}

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
```
