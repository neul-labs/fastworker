# Architecture

FastWorker uses a **Control Plane Architecture** that eliminates the need for external message brokers.

## Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ TCP (via control plane)
       │
┌──────▼──────────────┐
│  Control Plane      │ (Coordinator + Task Processor)
│  - Task distribution│
│  - Result caching   │
│  - Worker registry  │
│  - Management GUI   │
└──────┬──────────────┘
       │
   ┌───┴───┬────────┐
   │       │        │
┌──▼───┐ ┌▼────┐ ┌─▼────┐
│Sub-  │ │Sub- │ │Sub-  │
│worker│ │worker│ │worker│
└──────┘ └─────┘ └──────┘
```

## Key Components

### Control Plane Worker

The control plane is the central coordinator that:

- **Manages subworkers** - Tracks registration, health, and load
- **Distributes tasks** - Routes tasks to least-loaded workers
- **Processes tasks** - Can execute tasks directly when no subworkers available
- **Caches results** - Stores task results with TTL and LRU eviction
- **Provides discovery** - Allows clients and workers to find each other
- **Hosts management GUI** - Built-in web dashboard for monitoring

### Subworkers

Subworkers are additional task processors that:

- Register with the control plane on startup
- Receive tasks distributed by the control plane
- Process tasks and return results
- Send heartbeats to maintain health status
- Can be added/removed dynamically

### Clients

Clients connect to the control plane to:

- Submit tasks (blocking or non-blocking)
- Query task results
- Check task status

## Communication Patterns

FastWorker uses [NNG (nanomsg-next-generation)](https://nng.nanomsg.org/) for all communication:

| Pattern | Use Case |
|---------|----------|
| REQ/REP | Task submission and result retrieval |
| PUSH/PULL | Task distribution to workers |
| PUB/SUB | Service discovery announcements |

## Port Allocation

The control plane uses multiple ports:

| Port Offset | Purpose |
|-------------|---------|
| Base + 0 | Critical priority tasks |
| Base + 1 | High priority tasks |
| Base + 2 | Normal priority tasks |
| Base + 3 | Low priority tasks |
| Base + 4 | Result query endpoint |
| Base + 5 | Subworker management |

Example with base address `tcp://127.0.0.1:5555`:

- **5555**: Critical priority
- **5556**: High priority
- **5557**: Normal priority
- **5558**: Low priority
- **5559**: Result queries
- **5560**: Subworker management

## Deployment Comparison

### Traditional Stack (Celery + Redis)

```
Components to deploy:
✗ Your application server
✗ Redis broker (or RabbitMQ)
✗ Celery workers
✗ Redis result backend
✗ Optional: Flower monitoring
✗ Optional: Redis Sentinel for HA

Total: 4-6+ separate services
```

### FastWorker

```
Components to deploy:
✓ Your application server
✓ FastWorker control plane
✓ FastWorker subworkers (optional)

Total: 2-3 Python processes
```

## Benefits

| Aspect | FastWorker |
|--------|------------|
| **External dependencies** | None |
| **Languages/Runtimes** | Python only |
| **Configuration** | Minimal (env vars) |
| **Monitoring targets** | Python processes only |
| **Security surface** | Python process security |
| **Operational knowledge** | Python only |

## Limitations

FastWorker is designed for:

- **Moderate scale**: 1K-10K tasks/minute
- **Python-only**: Workers and clients must be Python
- **Single datacenter**: Low-latency network between components

For extreme scale, multi-language support, or complex workflows, see [Limitations](../reference/limitations.md).
