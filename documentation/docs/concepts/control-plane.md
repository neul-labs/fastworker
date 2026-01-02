# Control Plane

The control plane is the central coordinator in FastWorker's architecture.

## Overview

The control plane worker acts as both:

- **Coordinator**: Manages subworkers, distributes tasks, tracks load
- **Worker**: Processes tasks directly when no subworkers are available

## Starting the Control Plane

```bash
fastworker control-plane \
  --worker-id control-plane \
  --base-address tcp://127.0.0.1:5555 \
  --discovery-address tcp://127.0.0.1:5550 \
  --result-cache-size 10000 \
  --result-cache-ttl 3600 \
  --task-modules mytasks
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--worker-id` | `control-plane` | Control plane identifier |
| `--base-address` | `tcp://127.0.0.1:5555` | Base address for task processing |
| `--discovery-address` | `tcp://127.0.0.1:5550` | Service discovery address |
| `--subworker-port` | `5560` | Port for subworker registration |
| `--result-cache-size` | `10000` | Maximum cached results |
| `--result-cache-ttl` | `3600` | Cache TTL in seconds (1 hour) |
| `--task-modules` | - | Task modules to load |
| `--gui-host` | `127.0.0.1` | Management GUI host |
| `--gui-port` | `8080` | Management GUI port |
| `--no-gui` | `false` | Disable management GUI |

## Task Distribution

The control plane uses intelligent task distribution:

1. **Load Balancing**: Tasks sent to subworker with lowest load
2. **Priority Handling**: Tasks processed in priority order (CRITICAL → HIGH → NORMAL → LOW)
3. **Fallback**: Control plane processes tasks if no subworkers available
4. **Health Monitoring**: Inactive subworkers automatically excluded

## Result Caching

The control plane maintains a result cache with:

- **LRU Eviction**: Least recently accessed results evicted when cache is full
- **TTL Expiration**: Results expire after configured TTL
- **Automatic Cleanup**: Expired results cleaned up every minute
- **Query Endpoint**: Clients can query results by task ID

### Configuration

```bash
fastworker control-plane \
  --result-cache-size 20000 \
  --result-cache-ttl 7200 \
  --task-modules mytasks
```

### Querying Results

=== "CLI"

    ```bash
    fastworker status --task-id <uuid>
    ```

=== "Python"

    ```python
    result = await client.get_task_result(task_id)
    ```

## Monitoring

Get subworker status programmatically:

```python
from fastworker.workers.control_plane import ControlPlaneWorker

control_plane = ControlPlaneWorker()
status = control_plane.get_subworker_status()
print(status)
```

Returns:

```python
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
```

## Scaling

Simply start additional subworkers - no configuration changes needed:

```bash
# Terminal 1: Control plane
fastworker control-plane --task-modules mytasks

# Terminal 2: Subworker 1
fastworker subworker --worker-id sw1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks

# Terminal 3: Subworker 2
fastworker subworker --worker-id sw2 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5565 \
  --task-modules mytasks
```

Tasks automatically distribute across all available subworkers.

## Best Practices

1. **Start Control Plane First**: Always start before subworkers and clients
2. **Use Unique Ports**: Ensure subworkers use non-overlapping port ranges
3. **Monitor Cache Size**: Adjust based on task volume
4. **Set Appropriate TTL**: Balance result availability vs memory usage
5. **Health Monitoring**: Monitor subworker status in production
