# Quick Start

Get FastWorker running in under 5 minutes.

## Prerequisites

- Python 3.12 or higher
- pip or uv package manager

## Installation

```bash
pip install fastworker
```

## Step 1: Define Your Tasks

Create a file called `mytasks.py`:

```python
# mytasks.py
from fastworker import task

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

@task
def process_data(data: dict) -> dict:
    """Process some data."""
    return {"processed": True, "input": data}
```

## Step 2: Start the Control Plane

Open a terminal and run:

```bash
fastworker control-plane --task-modules mytasks
```

You should see output indicating the control plane is running. The built-in management GUI is now available at **http://127.0.0.1:8080**

## Step 3: Submit Tasks

### Using the CLI

```bash
# Blocking - wait for result
fastworker submit --task-name add --args 5 3
# Output: 8

# Non-blocking - get task ID immediately
fastworker submit --task-name add --args 5 3 --non-blocking
# Output: Task ID: 550e8400-e29b-41d4-a716-446655440000
```

### Using Python

```python
# submit_task.py
from fastworker import Client
import asyncio

async def main():
    client = Client()
    await client.start()

    # Non-blocking submission
    task_id = await client.delay("add", 5, 3)
    print(f"Task ID: {task_id}")

    # Wait a moment for processing
    await asyncio.sleep(1)

    # Get result
    result = await client.get_task_result(task_id)
    if result:
        print(f"Result: {result.result}")

    client.stop()

asyncio.run(main())
```

## Step 4: Scale with Subworkers (Optional)

For higher throughput, add subworkers in additional terminals:

```bash
# Terminal 2: Start subworker 1
fastworker subworker \
  --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks

# Terminal 3: Start subworker 2
fastworker subworker \
  --worker-id subworker2 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5565 \
  --task-modules mytasks
```

Tasks are automatically distributed across all available workers.

## What's Next?

- [Installation Guide](installation.md) - Detailed installation options
- [Configuration](configuration.md) - Environment variables and settings
- [Architecture](../concepts/architecture.md) - Understand how FastWorker works
- [Client Usage](../guide/client.md) - Complete client API guide
