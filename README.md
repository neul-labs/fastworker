# FastQueue

A brokerless task queue for Python applications with automatic worker discovery and priority handling.

[![PyPI version](https://badge.fury.io/py/fastqueue.svg)](https://badge.fury.io/py/fastqueue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Brokerless Architecture** - No Redis, RabbitMQ, or other message brokers required
- **Automatic Worker Discovery** - Workers find each other automatically on the network
- **Priority Queues** - Support for critical, high, normal, and low priority tasks
- **Built-in Reliability** - Automatic retries and error handling
- **FastAPI Integration** - Seamless integration with web applications
- **Zero Configuration** - Works out of the box with sensible defaults

## Installation

```bash
pip install fastqueue
```

## Quick Start

### 1. Define Tasks

```python
# tasks.py
from fastqueue import task

@task
def send_email(recipient: str, subject: str, body: str):
    # Your email sending logic
    print(f"Email sent to {recipient}")
    return "sent"

@task
def process_image(image_path: str):
    # Your image processing logic
    print(f"Processed {image_path}")
    return "processed"
```

### 2. Start Workers

```bash
# Terminal 1
fastqueue worker --worker-id worker1 --task-modules tasks

# Terminal 2 (optional - for scaling)
fastqueue worker --worker-id worker2 --task-modules tasks
```

### 3. Submit Tasks

```python
from fastqueue import Client
import asyncio

async def main():
    client = Client()
    await client.start()

    # Submit tasks
    result = await client.delay("send_email", "user@example.com", "Hello", "Welcome!")
    print(f"Task result: {result.result}")

    client.stop()

asyncio.run(main())
```

## CLI Usage

```bash
# Submit tasks via CLI
fastqueue submit --task-name send_email --args user@example.com "Hello" "Welcome!"

# List available tasks
fastqueue list --task-modules tasks
```

## FastAPI Integration

```python
from fastapi import FastAPI
from fastqueue import Client, task

app = FastAPI()
client = Client()

@task
def background_process(data: dict):
    # Your background processing
    return {"processed": data}

@app.on_event("startup")
async def startup():
    await client.start()

@app.on_event("shutdown")
async def shutdown():
    client.stop()

@app.post("/process")
async def process_data(data: dict):
    result = await client.delay("background_process", data)
    return {"task_id": result.task_id, "status": result.status}
```

## Priority Handling

```python
from fastqueue.tasks.models import TaskPriority

# Submit with priority
await client.delay("critical_task", priority=TaskPriority.CRITICAL)
await client.delay("normal_task", priority=TaskPriority.NORMAL)
```

## Configuration

Workers and clients accept configuration parameters:

```python
# Custom worker configuration
worker = Worker(
    worker_id="custom-worker",
    base_address="tcp://127.0.0.1:6000",
    discovery_address="tcp://127.0.0.1:6001"
)

# Custom client configuration
client = Client(
    discovery_address="tcp://127.0.0.1:6001",
    timeout=60,
    retries=5
)
```

## Architecture

FastQueue uses NNG (Next Generation Networking) patterns for direct worker-to-worker communication:

- **No Single Point of Failure** - No central broker to fail
- **Service Discovery** - Workers announce themselves and discover peers
- **Load Balancing** - Tasks distributed across available workers
- **Fault Tolerance** - Failed tasks automatically retry on other workers

## Development

```bash
# Clone repository
git clone https://github.com/dipankar/fastqueue.git
cd fastqueue

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
```

## Requirements

- Python 3.12+
- pynng
- pydantic

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.