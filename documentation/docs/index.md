# FastWorker

A brokerless task queue for Python applications with automatic worker discovery, priority handling, and built-in management GUI.

**No Redis. No RabbitMQ. Just Python.**

[![PyPI version](https://badge.fury.io/py/fastworker.svg)](https://badge.fury.io/py/fastworker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

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
- FastWorker control plane (with built-in web UI)
- FastWorker workers (optional, for scaling)

**That's it.** No external dependencies. No Redis to configure, monitor, backup, or secure. Just Python.

---

## Features

- **Brokerless Architecture** - No Redis, RabbitMQ, or other message brokers required
- **Control Plane Architecture** - Centralized coordination with distributed subworkers
- **Built-in Management GUI** - Real-time web dashboard for monitoring workers, queues, and tasks
- **Automatic Worker Discovery** - Workers find each other automatically on the network
- **Priority Queues** - Support for critical, high, normal, and low priority tasks
- **Result Caching** - Task results cached with expiration and memory limits
- **Task Completion Callbacks** - Receive real-time notifications when tasks complete
- **Built-in Reliability** - Automatic retries and error handling
- **FastAPI Integration** - Seamless integration with web applications
- **OpenTelemetry Support** - Optional distributed tracing and metrics for observability
- **Zero Configuration** - Works out of the box with sensible defaults

!!! note "Scale Considerations"
    FastWorker is designed for moderate-scale Python applications (1K-10K tasks/min). For extreme scale, multi-language support, or complex workflows, see [Limitations & Scope](reference/limitations.md).

---

## Quick Start

### 1. Install FastWorker

```bash
pip install fastworker
```

### 2. Define Tasks

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

### 3. Start Control Plane

```bash
# Terminal 1 - Start the control plane (coordinates and also processes tasks)
fastworker control-plane --task-modules mytasks
```

The control plane starts with a **built-in management GUI** at http://127.0.0.1:8080

### 4. Start Subworkers (Optional)

```bash
# Terminal 2 - Start subworker 1
fastworker subworker --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks
```

### 5. Submit Tasks

=== "CLI (Blocking)"

    ```bash
    fastworker submit --task-name add --args 5 3
    ```

=== "CLI (Non-blocking)"

    ```bash
    fastworker submit --task-name add --args 5 3 --non-blocking
    # Returns: Task ID: <uuid>
    ```

=== "Python (Non-blocking)"

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

=== "Python (Blocking)"

    ```python
    # Blocking: Waits for result
    result = await client.submit_task("add", args=(5, 3))
    print(f"Result: {result.result}")
    ```

---

## Architecture

FastWorker uses a **Control Plane Architecture**:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ TCP (via control plane)
       │
┌──────▼──────────────┐
│  Control Plane      │ (Coordinator + Task Processor)
│  - Task distribution│
│  - Result caching   │
│  - Worker registry  │
└──────┬──────────────┘
       │
   ┌───┴───┬────────┐
   │       │        │
┌──▼───┐ ┌▼────┐ ┌─▼────┐
│Sub-  │ │Sub- │ │Sub-  │
│worker│ │worker│ │worker│
└──────┘ └─────┘ └──────┘
```

### Key Components

- **Control Plane Worker**: Central coordinator that manages subworkers and also processes tasks
- **Subworkers**: Additional workers that register with the control plane for load distribution
- **Clients**: Connect only to the control plane for task submission

### Benefits

- **Centralized Management**: Control plane coordinates all task distribution
- **Load Balancing**: Tasks automatically distributed to least-loaded subworkers
- **High Availability**: Control plane processes tasks if no subworkers available
- **Result Persistence**: Results cached in control plane with expiration
- **Scalability**: Add subworkers dynamically without reconfiguration

---

## Requirements

- Python 3.12+
- pynng (network communication)
- pydantic (data validation)

---

## Documentation Sections

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Getting Started__

    ---

    Install FastWorker and get your first task queue running in minutes.

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

-   :material-puzzle:{ .lg .middle } __Core Concepts__

    ---

    Understand the architecture, control plane, workers, and task system.

    [:octicons-arrow-right-24: Architecture](concepts/architecture.md)

-   :material-book-open:{ .lg .middle } __User Guide__

    ---

    Learn how to use the client, configure priorities, and manage the GUI.

    [:octicons-arrow-right-24: Client Usage](guide/client.md)

-   :material-connection:{ .lg .middle } __Integration__

    ---

    Integrate FastWorker with FastAPI, Flask, Django, and other frameworks.

    [:octicons-arrow-right-24: FastAPI](integration/fastapi.md)

-   :material-cog:{ .lg .middle } __Advanced__

    ---

    Set up OpenTelemetry for distributed tracing and metrics.

    [:octicons-arrow-right-24: Telemetry](advanced/telemetry.md)

-   :material-file-document:{ .lg .middle } __Reference__

    ---

    Complete API reference, CLI commands, and troubleshooting guide.

    [:octicons-arrow-right-24: API Reference](reference/api.md)

</div>

---

## Support

- [GitHub Issues](https://github.com/neul-labs/fastworker/issues) - Bug reports and feature requests
- [Contributing Guide](https://github.com/neul-labs/fastworker/blob/main/CONTRIBUTING.md) - Development guidelines

---

## License

MIT License - see [LICENSE](https://github.com/neul-labs/fastworker/blob/main/LICENSE) for details.
