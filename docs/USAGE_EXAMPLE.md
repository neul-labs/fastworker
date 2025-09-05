# FastQueue Usage Example

This example demonstrates how to use FastQueue to create a distributed task processing system.

## 1. Define Tasks

First, create a task module (`mytasks.py`):

```python
from fastqueue import task
import asyncio
import time

@task
def add(x: int, y: int) -> int:
    """Add two numbers."""
    print(f"Adding {x} + {y}")
    return x + y

@task
def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    print(f"Multiplying {x} * {y}")
    return x * y

@task
async def async_task(seconds: int) -> str:
    """An asynchronous task."""
    print(f"Starting async task that will take {seconds} seconds")
    await asyncio.sleep(seconds)
    return f"Async task completed after {seconds} seconds"

@task
def cpu_intensive_task(n: int) -> int:
    """A CPU-intensive task."""
    print(f"Starting CPU-intensive task with n={n}")
    result = 0
    for i in range(n):
        result += i * i
    return result
```

## 2. Start Service Discovery

In a production environment, you would typically run the service discovery as a daemon. For this example, we'll start it in the background:

```bash
# Terminal 1: Start service discovery
python -c "
import asyncio
from fastqueue.discovery.discovery import ServiceDiscovery

async def run_discovery():
    discovery = ServiceDiscovery('tcp://127.0.0.1:5550')
    await discovery.start()
    print('Service discovery started on tcp://127.0.0.1:5550')
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        discovery.stop()

asyncio.run(run_discovery())
"
```

## 3. Start Workers

Start one or more workers to process tasks:

```bash
# Terminal 2: Start first worker
fastqueue worker --worker-id worker1 --base-address tcp://127.0.0.1:5555 --task-modules mytasks

# Terminal 3: Start second worker
fastqueue worker --worker-id worker2 --base-address tcp://127.0.0.1:5565 --task-modules mytasks
```

## 4. Submit Tasks

Submit tasks using the client:

```bash
# Terminal 4: Submit various tasks

# Submit a simple task
fastqueue submit --task-name add --args 5 3

# Submit a task with high priority
fastqueue submit --task-name multiply --args 4 7 --priority high

# Submit an async task
fastqueue submit --task-name async_task --args 3 --priority critical

# Submit a CPU-intensive task with normal priority
fastqueue submit --task-name cpu_intensive_task --args 1000000 --priority normal
```

## 5. List Available Tasks

You can list all available tasks:

```bash
fastqueue list --task-modules mytasks
```

## 6. Advanced Usage

### Programmatic Client Usage

You can also use FastQueue programmatically:

```python
import asyncio
from fastqueue.clients.client import Client
from fastqueue.tasks.models import TaskPriority

async def main():
    # Create client
    client = Client(discovery_address="tcp://127.0.0.1:5550")
    await client.start()
    
    # Submit tasks
    result1 = await client.delay("add", 10, 20, priority=TaskPriority.HIGH)
    print(f"Add result: {result1.result}")
    
    result2 = await client.delay("multiply", 5, 6, priority=TaskPriority.CRITICAL)
    print(f"Multiply result: {result2.result}")
    
    # Stop client
    client.stop()

asyncio.run(main())
```

## 7. Monitoring Workers

Workers automatically register themselves with the service discovery system. You can monitor available workers by checking the service discovery logs or by implementing a monitoring client.

## 8. Scaling

To scale the system:

1. Add more workers by starting additional worker processes
2. Workers automatically discover each other through the service discovery
3. Tasks are automatically load-balanced across available workers
4. Priority queues ensure critical tasks are processed first

## Benefits of This Approach

1. **No Single Point of Failure**: No central broker to fail
2. **Automatic Load Balancing**: Tasks are distributed across available workers
3. **Priority Handling**: Critical tasks are processed before lower priority ones
4. **Automatic Discovery**: Workers automatically discover each other
5. **Fault Tolerance**: If a worker fails, tasks can be rerouted to other workers
6. **Easy Scaling**: Simply start more workers to increase capacity

This example demonstrates the core functionality of FastQueue. In a production environment, you would typically run the service discovery, workers, and clients as separate services or daemons.