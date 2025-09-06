# FastQueue

Add background workers to your Python applications in seconds, without the complexity.

[![PyPI version](https://badge.fury.io/py/fastqueue.svg)](https://badge.fury.io/py/fastqueue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why FastQueue?

Adding background processing to your application shouldn't be hard. FastQueue makes it incredibly simple to offload time-consuming tasks without dealing with complex brokers, queues, or configurations.

### The Problem
Traditional task queues require:
- Setting up and maintaining a message broker (Redis, RabbitMQ, etc.)
- Managing separate queue servers
- Dealing with connection issues and reliability concerns
- Complex configuration and deployment

### The FastQueue Solution
FastQueue eliminates all that complexity:
- **No brokers to manage** - Workers communicate directly with each other
- **Automatic discovery** - Workers find each other automatically
- **Zero configuration** - Start workers and you're done
- **Built-in reliability** - Tasks are retried automatically if they fail

## Quick Start

### 1. Install FastQueue

```bash
pip install fastqueue
```

### 2. Define Your Tasks

Create `tasks.py`:

```python
from fastqueue import task

@task
def send_email(recipient: str, subject: str, body: str):
    """Send an email - this might take a few seconds."""
    # Your email sending logic here
    print(f"Email sent to {recipient}")

@task
def process_image(image_path: str):
    """Process an image - this might take a while."""
    # Your image processing logic here
    print(f"Processed image: {image_path}")

@task
def generate_report(data: dict):
    """Generate a report - this might be CPU intensive."""
    # Your report generation logic here
    print("Report generated")
```

### 3. Start Your Workers

In one terminal, start as many workers as you need:

```bash
# Start your first worker
fastqueue worker --worker-id worker1 --task-modules tasks

# In another terminal, start a second worker for more power
fastqueue worker --worker-id worker2 --task-modules tasks
```

That's it! Your workers automatically discover each other and start sharing the workload.

### 4. Use Tasks in Your Application

```python
# In your main application
from fastqueue import Client

# Create a client to submit tasks
client = Client()

# Submit tasks to be processed in the background
await client.delay("send_email", "user@example.com", "Hello", "Welcome!")
await client.delay("process_image", "/path/to/image.jpg")
await client.delay("generate_report", {"sales": 1000})
```

Or use the CLI:

```bash
# Submit tasks from the command line
fastqueue submit --task-name send_email --args user@example.com "Hello" "Welcome!"
fastqueue submit --task-name process_image --args /path/to/image.jpg
```

## Key Benefits

### 🚀 Effortless Scaling
Need more processing power? Just start another worker. No configuration needed.

### 🔧 Zero Maintenance
No brokers to monitor, no queues to manage. Just your workers doing what they do best.

### 🔄 Automatic Load Balancing
Tasks are automatically distributed across all available workers.

### ⚡ Priority Handling
Mark important tasks as "critical" to ensure they get processed first.

### 🛡️ Built-in Reliability
If a worker fails, tasks are automatically retried on other workers.

## FastAPI Integration

FastQueue works seamlessly with FastAPI:

```python
from fastapi import FastAPI
from fastqueue import task, Client

app = FastAPI()
client = Client()

@task
def process_user_data(user_id: int):
    # Process user data in the background
    pass

@app.on_event("startup")
async def startup_event():
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    client.stop()

@app.post("/users/{user_id}/process")
async def process_user(user_id: int):
    # This returns immediately while processing happens in the background
    await client.delay("process_user_data", user_id)
    return {"message": "Processing started"}
```

## How It Works

FastQueue uses advanced networking patterns that allow workers to communicate directly with each other, eliminating the need for a central broker. This makes your system more reliable and easier to manage.

When you start workers, they automatically discover each other on the network and begin sharing work. If a worker goes down, others continue processing tasks without interruption.

## Documentation

- [API Reference](docs/api.md)
- [Worker Guide](docs/workers.md)
- [Client Guide](docs/clients.md)
- [FastAPI Integration](docs/fastapi.md)

## Installation

```bash
pip install fastqueue
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.