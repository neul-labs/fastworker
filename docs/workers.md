# Worker Guide

## Architecture Overview

FastQueue uses a **Control Plane Architecture**:

- **Control Plane Worker**: Central coordinator that manages subworkers and processes tasks
- **Subworkers**: Additional workers that register with the control plane for load distribution

## Starting the Control Plane

The control plane is the central coordinator and should be started first:

fastqueue control-plane --worker-id control-plane --task-modules mytasks### Control Plane Parameters

- `--worker-id` (optional): Control plane identifier (default: "control-plane")
- `--base-address` (optional): Base address (default: `tcp://127.0.0.1:5555`)
- `--discovery-address` (optional): Discovery address (default: `tcp://127.0.0.1:5550`)
- `--subworker-port` (optional): Subworker management port (default: 5560)
- `--result-cache-size` (optional): Maximum cached results (default: 10000)
- `--result-cache-ttl` (optional): Cache TTL in seconds (default: 3600)
- `--task-modules` (optional): Task modules to load

### Example

# Start control plane with custom cache settings
fastqueue control-plane \
  --worker-id control-plane \
  --result-cache-size 20000 \
  --result-cache-ttl 7200 \
  --task-modules mytasks## Starting Subworkers

Subworkers register with the control plane and receive distributed tasks:

fastqueue subworker \
  --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks### Subworker Parameters

- `--worker-id` (required): Unique subworker identifier
- `--control-plane-address` (required): Address of the control plane
- `--base-address` (optional): Base address for this subworker (default: `tcp://127.0.0.1:5555`)
- `--discovery-address` (optional): Discovery address (default: `tcp://127.0.0.1:5550`)
- `--task-modules` (optional): Task modules to load

### Port Allocation

Each subworker needs its own port range. Use non-overlapping ports:

# Subworker 1: ports 5561-5564
fastqueue subworker --worker-id sw1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks

# Subworker 2: ports 5565-5568
fastqueue subworker --worker-id sw2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules mytasks

# Subworker 3: ports 5569-5572
fastqueue subworker --worker-id sw3 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5569 --task-modules mytasks## Task Processing

### Priority Order

Tasks are processed in priority order:

1. **CRITICAL** tasks are processed first
2. **HIGH** tasks are processed second
3. **NORMAL** tasks are processed third
4. **LOW** tasks are processed last

### Load Balancing

The control plane automatically:
- Distributes tasks to least-loaded subworkers
- Processes tasks locally if no subworkers available
- Monitors subworker health and load

## Result Caching

The control plane maintains a result cache:

- **Size Limit**: Configurable maximum number of results (default: 10,000)
- **TTL**: Results expire after configured time (default: 1 hour)
- **LRU Eviction**: Least recently accessed results evicted when cache is full
- **Automatic Cleanup**: Expired results cleaned up every minute

## Graceful Shutdown

Workers handle shutdown signals gracefully:

1. Press `Ctrl+C` to stop
2. Current tasks complete processing
3. Workers unregister from service discovery
4. All connections close cleanly

## Scaling

### Adding Subworkers

Simply start additional subworkers - no configuration changes needed:

# Terminal 1: Control plane
fastqueue control-plane --task-modules mytasks

# Terminal 2: Subworker 1
fastqueue subworker --worker-id sw1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks

# Terminal 3: Subworker 2
fastqueue subworker --worker-id sw2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules mytasksTasks automatically distribute across all available subworkers.

## Health Monitoring

The control plane monitors subworker health:

- Tracks last seen timestamp
- Marks subworkers inactive after 30 seconds of no activity
- Automatically excludes inactive subworkers from task distribution