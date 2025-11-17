# Control Plane Architecture

FastQueue uses a control plane architecture for centralized task coordination and management.

**See Also:**
- [Workers Guide](workers.md) - Worker configuration and management
- [API Reference](api.md) - ControlPlaneWorker API documentation
- [Configuration](configuration.md) - Environment variable configuration
- [Troubleshooting](troubleshooting.md) - Common issues

## Overview

The control plane architecture consists of:

1. **Control Plane Worker**: Central coordinator that manages subworkers and processes tasks
2. **Subworkers**: Additional workers that register with the control plane
3. **Clients**: Connect to the control plane for task submission

## Control Plane Worker

The control plane worker acts as both:
- **Coordinator**: Manages subworkers, distributes tasks, tracks load
- **Worker**: Processes tasks directly when no subworkers are available

### Starting the Control Plane

fastqueue control-plane \
  --worker-id control-plane \
  --base-address tcp://127.0.0.1:5555 \
  --discovery-address tcp://127.0.0.1:5550 \
  --result-cache-size 10000 \
  --result-cache-ttl 3600 \
  --task-modules mytasks

### Parameters

- `--worker-id`: Control plane identifier (default: "control-plane")
- `--base-address`: Base address for task processing (default: `tcp://127.0.0.1:5555`)
- `--discovery-address`: Service discovery address (default: `tcp://127.0.0.1:5550`)
- `--subworker-port`: Port for subworker registration (default: 5560)
- `--result-cache-size`: Maximum number of results to cache (default: 10000)
- `--result-cache-ttl`: Result cache TTL in seconds (default: 3600 = 1 hour)
- `--task-modules`: Task modules to load

### Port Allocation

The control plane uses the following ports:
- **Base port** (e.g., 5555): Critical priority tasks
- **Base + 1** (e.g., 5556): High priority tasks
- **Base + 2** (e.g., 5557): Normal priority tasks
- **Base + 3** (e.g., 5558): Low priority tasks
- **Base + 4** (e.g., 5559): Result query endpoint
- **Base + 5** (e.g., 5560): Subworker management

## Subworkers

Subworkers register with the control plane and receive distributed tasks.

### Starting a Subworker

fastqueue subworker \
  --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks

### Parameters

- `--worker-id`: Unique subworker identifier (required)
- `--control-plane-address`: Address of the control plane (required)
- `--base-address`: Base address for this subworker (default: `tcp://127.0.0.1:5555`)
- `--discovery-address`: Service discovery address (default: `tcp://127.0.0.1:5550`)
- `--task-modules`: Task modules to load

### Port Allocation for Subworkers

Each subworker needs its own port range. Use non-overlapping ports:
- Subworker 1: 5561-5564
- Subworker 2: 5565-5568
- Subworker 3: 5569-5572
- etc.

## Task Distribution

The control plane uses intelligent task distribution:

1. **Load Balancing**: Tasks sent to subworker with lowest load
2. **Priority Handling**: Tasks processed in priority order
3. **Fallback**: Control plane processes tasks if no subworkers available
4. **Health Monitoring**: Inactive subworkers automatically excluded

## Result Caching

The control plane maintains a result cache with:

### Features

- **LRU Eviction**: Least recently accessed results evicted when cache is full
- **TTL Expiration**: Results expire after configured TTL
- **Automatic Cleanup**: Expired results cleaned up every minute
- **Query Endpoint**: Clients can query results by task ID

### Configuration

fastqueue control-plane \
  --result-cache-size 20000 \
  --result-cache-ttl 7200 \
  --task-modules mytasks

### Querying Results

fastqueue status --task-id <uuid>

Or programmatically:

result = await client.get_task_result(task_id)

## Scaling

### Adding Subworkers

Simply start additional subworkers:

fastqueue control-plane --task-modules mytasks

fastqueue subworker --worker-id sw1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks

fastqueue subworker --worker-id sw2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules mytasks

fastqueue subworker --worker-id sw3 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5569 --task-modules mytasks

Tasks will automatically distribute across all available subworkers.

### High Availability

- Control plane processes tasks if subworkers fail
- Subworkers can be added/removed dynamically
- No configuration changes needed when scaling

## Monitoring

The control plane provides subworker status:

from fastqueue.workers.control_plane import ControlPlaneWorker

control_plane = ControlPlaneWorker()
status = control_plane.get_subworker_status()
print(status)

Returns:
{
    'total_subworkers': 3,
    'active_subworkers': 3,
    'subworkers': {
        'subworker1': {
            'address': 'tcp://127.0.0.1:5561',
            'status': 'active',
            'load': 2,
            'last_seen': '2025-11-16T23:52:33'
        },
        ...
    }
}

## Best Practices

1. **Start Control Plane First**: Always start the control plane before subworkers
2. **Use Unique Ports**: Ensure subworkers use non-overlapping port ranges
3. **Monitor Cache Size**: Adjust cache size based on task volume
4. **Set Appropriate TTL**: Balance result availability vs memory usage
5. **Health Monitoring**: Monitor subworker status in production
