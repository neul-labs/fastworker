# Workers

Workers are the task processors in FastWorker. There are two types: the **Control Plane** and **Subworkers**.

## Architecture Overview

```
┌─────────────────────────────┐
│     Control Plane           │
│  • Coordinates all work     │
│  • Processes tasks          │
│  • Caches results           │
└─────────────┬───────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│ Sub-  │ │ Sub-  │ │ Sub-  │
│worker1│ │worker2│ │worker3│
└───────┘ └───────┘ └───────┘
```

## Starting Workers

### Control Plane

The control plane should be started first:

```bash
fastworker control-plane --worker-id control-plane --task-modules mytasks
```

### Subworkers

Subworkers register with the control plane:

```bash
fastworker subworker \
  --worker-id subworker1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks
```

### Subworker Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--worker-id` | Yes | Unique subworker identifier |
| `--control-plane-address` | Yes | Address of the control plane |
| `--base-address` | No | Base address for this subworker |
| `--discovery-address` | No | Discovery address |
| `--task-modules` | No | Task modules to load |

## Port Allocation

Each subworker needs its own port range. Use non-overlapping ports:

```bash
# Subworker 1: ports 5561-5564
fastworker subworker --worker-id sw1 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5561 \
  --task-modules mytasks

# Subworker 2: ports 5565-5568
fastworker subworker --worker-id sw2 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5565 \
  --task-modules mytasks

# Subworker 3: ports 5569-5572
fastworker subworker --worker-id sw3 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5569 \
  --task-modules mytasks
```

## Task Processing

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

## Health Monitoring

The control plane monitors subworker health:

- Tracks last seen timestamp
- Marks subworkers inactive after 30 seconds of no activity
- Automatically excludes inactive subworkers from task distribution

## Graceful Shutdown

Workers handle shutdown signals gracefully:

1. Press `Ctrl+C` to stop
2. Current tasks complete processing
3. Workers unregister from service discovery
4. All connections close cleanly

## Scaling

### Adding Subworkers

Simply start additional subworkers - no configuration changes needed:

```bash
# Start more workers at any time
fastworker subworker --worker-id sw4 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5573 \
  --task-modules mytasks
```

Tasks automatically distribute across all available subworkers.

### Removing Subworkers

Stop a subworker with `Ctrl+C`. The control plane will:

- Detect the subworker is inactive
- Stop routing tasks to it
- Continue distributing to remaining workers

## Recommended Worker Count

| Workers | Performance |
|---------|-------------|
| 1-20 | Optimal |
| 20-50 | Good |
| 50-100 | Degraded |
| 100+ | Not recommended |

Service discovery and connection overhead increases with worker count.
