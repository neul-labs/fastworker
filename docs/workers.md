# Worker Guide

## Starting Workers

Workers are started using the CLI command:

```bash
fastqueue worker --worker-id <worker_id> --task-modules <module1> [<module2> ...]
```

### Parameters

- `--worker-id` (required): Unique identifier for the worker
- `--base-address` (optional): Base address for the worker (default: `tcp://127.0.0.1:5555`)
- `--discovery-address` (optional): Discovery address (default: `tcp://127.0.0.1:5550`)
- `--task-modules` (optional): Task modules to load

### Example

```bash
# Start a worker with default settings
fastqueue worker --worker-id worker1 --task-modules myapp.tasks

# Start a worker with custom addresses
fastqueue worker --worker-id worker2 --base-address tcp://192.168.1.100:5555 --discovery-address tcp://192.168.1.100:5550 --task-modules myapp.tasks
```

## Worker Internals

Workers use several nng patterns for operation:

1. **Surveyor/Respondent Pattern**: For receiving tasks and sending results
2. **Bus Pattern**: For automatic service discovery
3. **Automatic Load Balancing**: Tasks are distributed among available workers

## Worker Discovery

Workers automatically discover each other through the built-in service discovery mechanism:

1. Workers announce themselves on the network when starting
2. Other workers and clients automatically discover them
3. No manual configuration is required

## Task Processing

Workers process tasks in priority order:

1. **CRITICAL** tasks are processed first
2. **HIGH** tasks are processed second
3. **NORMAL** tasks are processed third
4. **LOW** tasks are processed last

## Graceful Shutdown

Workers handle shutdown signals gracefully:

1. Press `Ctrl+C` to stop a worker
2. The worker will finish processing the current task
3. The worker will unregister itself from service discovery
4. The worker will close all connections

## Multiple Workers

You can run multiple workers for scalability:

```bash
# Terminal 1
fastqueue worker --worker-id worker1 --task-modules myapp.tasks

# Terminal 2
fastqueue worker --worker-id worker2 --task-modules myapp.tasks

# Terminal 3
fastqueue worker --worker-id worker3 --task-modules myapp.tasks
```

Tasks will be automatically load-balanced among the available workers.

## Worker Health

Workers continuously monitor their health and network connections:

1. Automatic reconnection to the discovery network
2. Error handling for task processing
3. Logging of important events