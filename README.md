# FastWorker

A brokerless task queue for Python applications with automatic worker discovery and priority handling.

**No Redis. No RabbitMQ. Just Python.**

[![PyPI version](https://badge.fury.io/py/fastworker.svg)](https://badge.fury.io/py/fastworker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why FastWorker?

Traditional task queues (Celery + Redis) require deploying and managing **4-6+ separate services**:
- Your application
- Redis broker
- Celery workers
- Redis result backend
- Optional: Flower monitoring
- Optional: Redis Sentinel for HA

**FastWorker requires just 2-3 Python processes:**
- Your application
- FastWorker control plane
- FastWorker workers (optional, for scaling)

**That's it.** No external dependencies. No Redis to configure, monitor, backup, or secure. Just Python.

## Features

- **Brokerless Architecture** - No Redis, RabbitMQ, or other message brokers required
- **Control Plane Architecture** - Centralized coordination with distributed subworkers
- **Automatic Worker Discovery** - Workers find each other automatically on the network
- **Priority Queues** - Support for critical, high, normal, and low priority tasks
- **Result Caching** - Task results cached with expiration and memory limits
- **Task Completion Callbacks** - Receive real-time notifications when tasks complete
- **Built-in Reliability** - Automatic retries and error handling
- **FastAPI Integration** - Seamless integration with web applications
- **OpenTelemetry Support** - Optional distributed tracing and metrics for observability
- **Zero Configuration** - Works out of the box with sensible defaults

**Note:** FastWorker is designed for moderate-scale Python applications (1K-10K tasks/min). For extreme scale, multi-language support, or complex workflows, see [Limitations & Scope](docs/limitations.md).

## Installation

```bash
pip install fastworker
```

## Quick Start

### 1. Define Tasks

```python
# mytasks.py
from fastworker import task

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

@task
def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y
```

### 2. Start Control Plane

```bash
# Terminal 1 - Start the control plane (coordinates and also processes tasks)
fastworker control-plane --worker-id control-plane --task-modules mytasks
```

### 3. Start Subworkers (Optional - for scaling)

```bash
# Terminal 2 - Start subworker 1
fastworker subworker --worker-id subworker1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks

# Terminal 3 - Start subworker 2 (optional)
fastworker subworker --worker-id subworker2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules mytasks
```

### 4. Submit Tasks

**Blocking mode (wait for result):**
```bash
fastworker submit --task-name add --args 5 3
```

**Non-blocking mode (get task ID immediately):**
```bash
fastworker submit --task-name add --args 5 3 --non-blocking
# Returns: Task ID: <uuid>
```

**Check task status:**
```bash
fastworker status --task-id <uuid>
```

### 5. Using Python Client

**Non-blocking (recommended):**
```python
from fastworker import Client
import asyncio

async def main():
    client = Client()
    await client.start()

    # Non-blocking: Returns immediately with task ID
    task_id = await client.delay("add", 5, 3)
    print(f"Task submitted: {task_id}")

    # Check result later
    result = await client.get_task_result(task_id)
    if result:
        print(f"Result: {result.result}")

    client.stop()

asyncio.run(main())
```

**Blocking (when you need the result immediately):**
```python
# Blocking: Waits for result
result = await client.submit_task("add", args=(5, 3))
print(f"Result: {result.result}")
```

## Architecture

FastWorker uses a **Control Plane Architecture**:

- **Control Plane Worker**: Central coordinator that manages subworkers and also processes tasks
- **Subworkers**: Additional workers that register with the control plane for load distribution
- **Clients**: Connect only to the control plane for task submission

### Benefits

- **Centralized Management**: Control plane coordinates all task distribution
- **Load Balancing**: Tasks automatically distributed to least-loaded subworkers
- **High Availability**: Control plane processes tasks if no subworkers available
- **Result Persistence**: Results cached in control plane with expiration
- **Scalability**: Add subworkers dynamically without reconfiguration

## CLI Usage

```bash
# Start control plane
fastworker control-plane --worker-id control-plane --task-modules mytasks

# Start subworker
fastworker subworker --worker-id subworker1 --control-plane-address tcp://127.0.0.1:5555 --task-modules mytasks

# Submit task (blocking)
fastworker submit --task-name add --args 5 3

# Submit task (non-blocking)
fastworker submit --task-name add --args 5 3 --non-blocking

# Check task status
fastworker status --task-id <uuid>

# List available tasks
fastworker list --task-modules mytasks
```

## Priority Handling

```python
from fastworker.tasks.models import TaskPriority

# Submit with priority
await client.delay("critical_task", priority=TaskPriority.CRITICAL)
await client.delay("normal_task", priority=TaskPriority.NORMAL)
```

## Result Caching

The control plane maintains a result cache with:
- **Configurable Size**: Default 10,000 results (configurable via `--result-cache-size`)
- **TTL**: Default 1 hour (configurable via `--result-cache-ttl`)
- **LRU Eviction**: Least recently accessed results evicted when cache is full
- **Automatic Cleanup**: Expired results cleaned up every minute

## Configuration

### Control Plane

```bash
fastworker control-plane \
  --worker-id control-plane \
  --base-address tcp://127.0.0.1:5555 \
  --discovery-address tcp://127.0.0.1:5550 \
  --result-cache-size 10000 \
  --result-cache-ttl 3600 \
  --task-modules mytasks
```

### Subworker

```bash
fastworker subworker \
  --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks
```

### Client

```python
client = Client(
    discovery_address="tcp://127.0.0.1:5550",
    timeout=60,
    retries=5
)
```

## Development

```bash
# Clone repository
git clone https://github.com/dipankar/fastworker.git
cd fastworker

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

## Documentation

For detailed documentation, see:

- [Documentation Index](docs/index.md) - Complete documentation
- [Limitations & Scope](docs/limitations.md) - **Start here** - What FastWorker is and when to use it
- [API Reference](docs/api.md) - Full API documentation
- [FastAPI Integration](docs/fastapi.md) - Web framework integration
- [OpenTelemetry Integration](docs/telemetry.md) - Distributed tracing and metrics
- [Configuration Guide](docs/configuration.md) - Environment variables and settings
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.