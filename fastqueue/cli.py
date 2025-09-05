"""CLI interface for FastQueue."""
import argparse
import asyncio
import sys
import importlib
from fastqueue.workers.worker import Worker
from fastqueue.clients.client import Client
from fastqueue.tasks.registry import task_registry

def load_tasks(task_modules):
    """Load task modules."""
    for module_name in task_modules:
        try:
            importlib.import_module(module_name)
            print(f"Loaded tasks from {module_name}")
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")

def start_worker(args):
    """Start a worker."""
    # Load task modules
    if args.task_modules:
        load_tasks(args.task_modules)
    
    # Create and start worker
    worker = Worker(
        worker_id=args.worker_id,
        base_address=args.base_address,
        discovery_address=args.discovery_address
    )
    
    print(f"Starting worker {args.worker_id}")
    print(f"Base address: {args.base_address}")
    print(f"Discovery address: {args.discovery_address}")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        print("\nStopping worker...")
        worker.stop()

def submit_task(args):
    """Submit a task."""
    # Load task modules
    if args.task_modules:
        load_tasks(args.task_modules)
    
    # Create client
    client = Client(discovery_address=args.discovery_address)
    
    # Submit task
    async def submit():
        await client.start()
        result = await client.delay(
            args.task_name,
            *args.args,
            priority=args.priority
        )
        client.stop()
        return result
    
    result = asyncio.run(submit())
    
    print(f"Task result: {result}")
    if result.status == "success":
        print(f"Result: {result.result}")
    else:
        print(f"Error: {result.error}")

def list_tasks(args):
    """List available tasks."""
    # Load task modules
    if args.task_modules:
        load_tasks(args.task_modules)
    
    tasks = task_registry.list_tasks()
    print("Available tasks:")
    for name in tasks:
        print(f"  - {name}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FastQueue CLI - Brokerless task queue using nng")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Start a worker")
    worker_parser.add_argument("--worker-id", required=True, help="Worker ID")
    worker_parser.add_argument("--base-address", default="tcp://127.0.0.1:5555", 
                              help="Base address for worker (default: tcp://127.0.0.1:5555)")
    worker_parser.add_argument("--discovery-address", default="tcp://127.0.0.1:5550",
                              help="Discovery address (default: tcp://127.0.0.1:5550)")
    worker_parser.add_argument("--task-modules", nargs="*", 
                              help="Task modules to load")
    worker_parser.set_defaults(func=start_worker)
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a task")
    submit_parser.add_argument("--discovery-address", default="tcp://127.0.0.1:5550",
                              help="Discovery address (default: tcp://127.0.0.1:5550)")
    submit_parser.add_argument("--task-name", required=True, help="Task name")
    submit_parser.add_argument("--args", nargs="*", default=[], help="Task arguments")
    submit_parser.add_argument("--priority", default="normal", 
                              choices=["low", "normal", "high", "critical"],
                              help="Task priority (default: normal)")
    submit_parser.add_argument("--task-modules", nargs="*", 
                              help="Task modules to load")
    submit_parser.set_defaults(func=submit_task)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available tasks")
    list_parser.add_argument("--task-modules", nargs="*", 
                            help="Task modules to load")
    list_parser.set_defaults(func=list_tasks)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Call the appropriate function
    args.func(args)

if __name__ == "__main__":
    main()