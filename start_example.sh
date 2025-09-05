#!/bin/bash
# FastQueue Example Startup Script

echo "Starting FastQueue Example"

# Create a virtual environment if it doesn't exist
if [ ! -d "fastqueue-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv fastqueue-env
    source fastqueue-env/bin/activate
    pip install poetry
else
    source fastqueue-env/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Create example task file
cat > mytasks.py << 'EOF'
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
EOF

echo "Created example task file: mytasks.py"

echo "To run the example:"
echo "1. Start service discovery in one terminal:"
echo "   python -c \""
echo "   import asyncio"
echo "   from fastqueue.discovery.discovery import ServiceDiscovery"
echo "   "
echo "   async def run_discovery():"
echo "       discovery = ServiceDiscovery('tcp://127.0.0.1:5550')"
echo "       await discovery.start()"
echo "       print('Service discovery started on tcp://127.0.0.1:5550')"
echo "       try:"
echo "           while True:"
echo "               await asyncio.sleep(1)"
echo "       except KeyboardInterrupt:"
echo "           pass"
echo "       finally:"
echo "           discovery.stop()"
echo "   "
echo "   asyncio.run(run_discovery())"
echo "   \""
echo ""
echo "2. Start workers in separate terminals:"
echo "   fastqueue worker --worker-id worker1 --base-address tcp://127.0.0.1:5555 --task-modules mytasks"
echo "   fastqueue worker --worker-id worker2 --base-address tcp://127.0.0.1:5565 --task-modules mytasks"
echo ""
echo "3. Submit tasks in another terminal:"
echo "   fastqueue submit --task-name add --args 5 3"
echo "   fastqueue submit --task-name multiply --args 4 7 --priority high"
echo "   fastqueue submit --task-name async_task --args 3 --priority critical"
echo ""
echo "4. List available tasks:"
echo "   fastqueue list --task-modules mytasks"