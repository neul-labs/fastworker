# FastQueue

A brokerless task queue using nng patterns, featuring reliable delivery, priority queues, load balancing, and service discovery.

[![PyPI version](https://badge.fury.io/py/fastqueue.svg)](https://badge.fury.io/py/fastqueue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Brokerless Architecture**: No central broker required, reducing single points of failure
- **Native NNG Patterns**: Leverages nng's built-in patterns for reliability and performance
- **Priority Queues**: Support for task prioritization (CRITICAL, HIGH, NORMAL, LOW)
- **Load Balancing**: Automatic distribution of tasks to available workers
- **Automatic Service Discovery**: Transparent worker discovery with no manual configuration
- **Reliable Delivery**: Guaranteed message delivery with retry mechanisms
- **Easy to Use**: Simple API similar to Celery
- **FastAPI Integration**: Seamless integration with FastAPI applications

## Installation

```bash
pip install fastqueue
```

## Quick Start

### 1. Define Tasks

```python
from fastqueue import task

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

@task
def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y
```

### 2. Start Workers

Start one or more workers in separate terminals:

```bash
# Start workers (automatically discover each other)
fastqueue worker --worker-id worker1 --task-modules tasks
fastqueue worker --worker-id worker2 --task-modules tasks
```

### 3. Submit Tasks

Submit tasks using the CLI:

```bash
# Submit a task
fastqueue submit --task-name add --args 2 3

# Submit a high priority task
fastqueue submit --task-name multiply --args 4 7 --priority high
```

### 4. Use in FastAPI Applications

```python
from fastapi import FastAPI
from fastqueue import task, Client

app = FastAPI()
client = Client()

@task
def process_data(data: dict) -> dict:
    return {"result": "processed"}

@app.on_event("startup")
async def startup_event():
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    client.stop()

@app.post("/process/")
async def process_endpoint(data: dict):
    result = await client.delay("process_data", data)
    return result
```

## Documentation

See the [documentation](docs/index.md) for detailed information:

- [API Reference](docs/api.md)
- [Worker Guide](docs/workers.md)
- [Client Guide](docs/clients.md)
- [FastAPI Integration](docs/fastapi.md)
- [NNG Patterns Used](docs/nng_patterns.md)

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/fastqueue.git
cd fastqueue

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.