"""Integration test for FastQueue."""
import asyncio
import threading
import time
import subprocess
import signal
import os
from fastqueue.clients.client import Client
from fastqueue.tasks.registry import task

# Define a test task
@task
def add_numbers(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

# Test the integration
async def test_integration():
    """Test the integration of worker and client."""
    print("Starting integration test...")
    
    # Start service discovery first
    discovery_process = subprocess.Popen([
        "python", "-c", """
import asyncio
from fastqueue.discovery.discovery import ServiceDiscovery

async def run_discovery():
    discovery = ServiceDiscovery("tcp://127.0.0.1:5560")
    await discovery.start()
    print("Service discovery started")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        discovery.stop()

asyncio.run(run_discovery())
"""
    ])
    
    # Wait a bit for discovery to start
    time.sleep(1)
    
    # Start a worker in a subprocess
    worker_process = subprocess.Popen([
        "python", "-c", """
import asyncio
import sys
sys.path.append('/home/dipankar/Github/fastqueue')
from fastqueue.workers.worker import Worker
from fastqueue.tasks.registry import task

@task
def add_numbers(x: int, y: int) -> int:
    return x + y

async def run_worker():
    worker = Worker(
        worker_id="test_worker",
        base_address="tcp://127.0.0.1:5565",
        discovery_address="tcp://127.0.0.1:5560"
    )
    print("Worker started")
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()

asyncio.run(run_worker())
"""
    ])
    
    # Wait a bit for the worker to start
    time.sleep(2)
    
    try:
        # Create a client
        client = Client(discovery_address="tcp://127.0.0.1:5560")
        await client.start()
        
        # Submit a task
        result = await client.delay("add_numbers", 5, 3)
        
        print(f"Task result: {result}")
        if result.status == "success":
            print(f"Result: {result.result}")
            assert result.result == 8
        else:
            print(f"Error: {result.error}")
            assert False, "Task failed"
            
        print("Integration test passed!")
        client.stop()
        
    finally:
        # Stop the worker and discovery
        worker_process.send_signal(signal.SIGINT)
        discovery_process.send_signal(signal.SIGINT)
        worker_process.wait()
        discovery_process.wait()

if __name__ == "__main__":
    asyncio.run(test_integration())