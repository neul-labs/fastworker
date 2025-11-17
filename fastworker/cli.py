"""CLI interface for FastWorker."""
import argparse
import asyncio
import sys
import importlib
import logging
from fastworker.workers.worker import Worker
from fastworker.clients.client import Client
from fastworker.tasks.registry import task_registry
from fastworker.tasks.models import TaskStatus, TaskResult
from fastworker.workers.control_plane import ControlPlaneWorker
from fastworker.workers.subworker import SubWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def convert_arg_type(arg: str):
    """Try to convert string argument to appropriate type."""
    # Try boolean
    if arg.lower() in ('true', 'false'):
        return arg.lower() == 'true'
    
    # Try integer
    try:
        return int(arg)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(arg)
    except ValueError:
        pass
    
    # Return as string if no conversion works
    return arg

def convert_args(args_list):
    """Convert list of string arguments to appropriate types."""
    return tuple(convert_arg_type(arg) for arg in args_list)

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
    
    # Convert string arguments to appropriate types
    converted_args = convert_args(args.args) if args.args else ()
    
    # Create client
    client = Client(discovery_address=args.discovery_address)
    
    # Submit task
    async def submit():
        try:
            await client.start()
            
            # Use delay() for non-blocking submission (now async)
            task_id = await client.delay(
                args.task_name,
                *converted_args,  # Use converted args instead of args.args
                priority=args.priority
            )
            
            print(f"Task submitted with ID: {task_id}")
            
            # If non-blocking mode, just return the task ID
            if args.non_blocking:
                print(f"Task ID: {task_id}")
                return None
            
            # Otherwise, wait for result (blocking mode)
            print("Waiting for result...")
            
            # Poll for result (with timeout)
            max_wait = 60  # 60 seconds max wait
            wait_interval = 0.1
            waited = 0.0
            
            while waited < max_wait:
                result = client.get_result(task_id)
                if result and result.status != TaskStatus.PENDING:
                    return result
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Timeout - return pending result
            return client.get_result(task_id) or TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                error="Timeout waiting for task result"
            )
        finally:
            client.stop()
    
    result = asyncio.run(submit())
    
    # Only print result if we were blocking
    if not args.non_blocking and result:
        print(f"Task result: {result}")
        if result.status == TaskStatus.SUCCESS:
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

def start_control_plane(args):
    """Start a control plane worker."""
    # Load task modules
    if args.task_modules:
        load_tasks(args.task_modules)
    
    # Create and start control plane worker
    control_plane = ControlPlaneWorker(
        worker_id=args.worker_id or "control-plane",
        base_address=args.base_address,
        discovery_address=args.discovery_address,
        subworker_management_port=args.subworker_port,
        result_cache_max_size=args.result_cache_size,
        result_cache_ttl_seconds=args.result_cache_ttl
    )
    
    print(f"Starting control plane worker {control_plane.worker_id}")
    print(f"Base address: {args.base_address}")
    print(f"Discovery address: {args.discovery_address}")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(control_plane.start())
    except KeyboardInterrupt:
        print("\nStopping control plane...")
        control_plane.stop()

def start_subworker(args):
    """Start a subworker."""
    # Load task modules
    if args.task_modules:
        load_tasks(args.task_modules)
    
    # Create and start subworker
    subworker = SubWorker(
        worker_id=args.worker_id,
        control_plane_address=args.control_plane_address,
        base_address=args.base_address,
        discovery_address=args.discovery_address
    )
    
    print(f"Starting subworker {args.worker_id}")
    print(f"Control plane: {args.control_plane_address}")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(subworker.start())
    except KeyboardInterrupt:
        print("\nStopping subworker...")
        subworker.stop()

def get_task_status(args):
    """Get the status/result of a task by task ID."""
    # Create client
    client = Client(discovery_address=args.discovery_address)
    
    async def get_status():
        try:
            await client.start()
            
            # Query result from control plane
            result = await client.get_task_result(args.task_id)
            
            if result:
                print(f"Task ID: {args.task_id}")
                print(f"Status: {result.status.value}")
                
                if result.status == TaskStatus.SUCCESS:
                    print(f"Result: {result.result}")
                elif result.status == TaskStatus.FAILURE:
                    print(f"Error: {result.error}")
                elif result.status == TaskStatus.PENDING:
                    print("Task is still pending (not yet processed)")
                elif result.status == TaskStatus.STARTED:
                    print("Task is currently being processed")
                
                if result.started_at:
                    print(f"Started at: {result.started_at}")
                if result.completed_at:
                    print(f"Completed at: {result.completed_at}")
                return 0
            else:
                print(f"Task ID {args.task_id} not found or expired.")
                print("The result may have expired from the cache or the task hasn't completed yet.")
                return 1
            
        finally:
            client.stop()
    
    exit_code = asyncio.run(get_status())
    return exit_code

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FastWorker CLI - Brokerless task queue using nng")
    
    # Global logging level option
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Set logging level (default: INFO)')
    
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
    submit_parser.add_argument("--non-blocking", action="store_true",
                              help="Submit task and return immediately with task ID (non-blocking)")
    submit_parser.set_defaults(func=submit_task)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available tasks")
    list_parser.add_argument("--task-modules", nargs="*", 
                            help="Task modules to load")
    list_parser.set_defaults(func=list_tasks)
    
    # Control plane command
    control_plane_parser = subparsers.add_parser("control-plane", help="Start control plane worker")
    control_plane_parser.add_argument("--worker-id", help="Control plane worker ID (default: control-plane)")
    control_plane_parser.add_argument("--base-address", default="tcp://127.0.0.1:5555", 
                              help="Base address (default: tcp://127.0.0.1:5555)")
    control_plane_parser.add_argument("--discovery-address", default="tcp://127.0.0.1:5550",
                              help="Discovery address (default: tcp://127.0.0.1:5550)")
    control_plane_parser.add_argument("--subworker-port", type=int, default=5560,
                              help="Subworker management port (default: 5560)")
    control_plane_parser.add_argument("--result-cache-size", type=int, default=10000,
                              help="Maximum number of results to cache (default: 10000)")
    control_plane_parser.add_argument("--result-cache-ttl", type=int, default=3600,
                              help="Result cache TTL in seconds (default: 3600 = 1 hour)")
    control_plane_parser.add_argument("--task-modules", nargs="*", 
                              help="Task modules to load")
    control_plane_parser.set_defaults(func=start_control_plane)
    
    # Subworker command
    subworker_parser = subparsers.add_parser("subworker", help="Start a subworker")
    subworker_parser.add_argument("--worker-id", required=True, help="Subworker ID")
    subworker_parser.add_argument("--control-plane-address", required=True,
                              help="Control plane address (e.g., tcp://127.0.0.1:5555)")
    subworker_parser.add_argument("--base-address", default="tcp://127.0.0.1:5555", 
                              help="Base address for subworker (default: tcp://127.0.0.1:5555)")
    subworker_parser.add_argument("--discovery-address", default="tcp://127.0.0.1:5550",
                              help="Discovery address (default: tcp://127.0.0.1:5550)")
    subworker_parser.add_argument("--task-modules", nargs="*", 
                              help="Task modules to load")
    subworker_parser.set_defaults(func=start_subworker)

    # Status command
    status_parser = subparsers.add_parser("status", help="Get task status by task ID")
    status_parser.add_argument("--task-id", required=True, help="Task ID (UUID)")
    status_parser.add_argument("--discovery-address", default="tcp://127.0.0.1:5550",
                              help="Discovery address (default: tcp://127.0.0.1:5550)")
    status_parser.set_defaults(func=get_task_status)

    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging level
    log_level = getattr(args, 'log_level', 'INFO')
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    if not args.command:
        parser.print_help()
        return
    
    # Call the appropriate function
    args.func(args)

if __name__ == "__main__":
    main()