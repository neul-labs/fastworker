#!/bin/bash
# FastWorker Example Startup Script

echo "Starting FastWorker Example"

# Create a virtual environment if it doesn't exist
if [ ! -d "fastworker-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv fastworker-env
    source fastworker-env/bin/activate
    pip install poetry
else
    source fastworker-env/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Create example task file
cat > mytasks.py << 'EOF'
from fastworker import task
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
echo ""
echo "=========================================="
echo "FastWorker Control Plane Architecture"
echo "=========================================="
echo ""
echo "To run the example:"
echo ""
echo "1. Start the Control Plane Worker (in Terminal 1):"
echo "   fastworker control-plane --worker-id control-plane --base-address tcp://127.0.0.1:5555 --task-modules mytasks"
echo ""
echo "2. Start Subworkers in separate terminals:"
echo "   Terminal 2:"
echo "   fastworker subworker --worker-id subworker1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks"
echo ""
echo "   Terminal 3:"
echo "   fastworker subworker --worker-id subworker2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules mytasks"
echo ""
echo "   Terminal 4 (optional - more subworkers for scaling):"
echo "   fastworker subworker --worker-id subworker3 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5569 --task-modules mytasks"
echo ""
echo "3. Submit tasks in another terminal (clients connect to control plane):"
echo "   fastworker submit --task-name add --args 5 3"
echo "   fastworker submit --task-name multiply --args 4 7 --priority high"
echo "   fastworker submit --task-name async_task --args 3 --priority critical"
echo "   fastworker submit --task-name cpu_intensive_task --args 1000000 --priority normal"
echo ""
echo "4. List available tasks:"
echo "   fastworker list --task-modules mytasks"
echo ""
echo "=========================================="
echo "Architecture Notes:"
echo "=========================================="
echo "- Control Plane: Coordinates subworkers and also processes tasks"
echo "- Subworkers: Register with control plane and process distributed tasks"
echo "- Clients: Connect only to the control plane"
echo "- Load Balancing: Control plane distributes tasks to least-loaded subworkers"
echo "- High Availability: Control plane processes tasks if no subworkers available"
echo ""
echo "Press Ctrl+C in each terminal to stop the respective component"