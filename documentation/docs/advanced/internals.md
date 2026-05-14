# Internals — How FastWorker Works

An overview of FastWorker's internal architecture for developers who want to understand, debug, or extend the system.

## Communication: NNG Patterns

FastWorker uses [NNG](https://nng.nanomsg.org/) (nanomsg-next-generation) for all process communication. No HTTP, no gRPC — raw TCP sockets with well-defined messaging patterns.

### Pattern Types

| Pattern | Use Case |
|---|---|
| **REQ/REP** | Client → Control Plane task submission, result queries |
| **BUS** | Service discovery announcements |
| **SURVEYOR/RESPONDENT** | Subworker task distribution |
| **PAIR** | Task completion callbacks |

### Addressing

Tasks are routed by priority using adjacent ports:

```
Base port (e.g., 5555):
  5555 → CRITICAL
  5556 → HIGH
  5557 → NORMAL
  5558 → LOW
  5559 → Result queries
  5560 → Subworker registration (default)
```

## Service Discovery

Workers and the control plane announce themselves on a BUS socket at the discovery address (default: `tcp://127.0.0.1:5550`). Announcements are broadcast every 2 seconds.

```
Control Plane ──► BUS (5550) ◄── Worker 1
                     ◄── Worker 2
                     ◄── Client
```

No central registry. No DNS. Just broadcast and listen.

## Task Lifecycle State Machine

Tasks follow a formal 9-state machine with atomic transitions:

```
PENDING → QUEUED → ASSIGNED → RUNNING → SUCCESS
                     ↓             ↓
                  SCHEDULED     FAILURE → RETRYING → QUEUED
                     ↓             ↓
                  CANCELLED    CANCELLED
```

Each transition is protected by `asyncio.Lock`. Terminal states (SUCCESS, CANCELLED) are immutable. Events are emitted on every transition via the EventBus.

## Heap-Based Scheduling

Both delayed tasks (ETA/countdown) and periodic tasks use a shared min-heap:

```
Heap entry: (eta, task_id, task, meta)
```

- **One-shot delayed**: `meta = None`, popped once when ETA arrives
- **Periodic**: `meta` is `{is_periodic, schedule_config, times_run, task_name}`, re-pushed after each execution

The `_process_scheduled_tasks` loop checks the heap every 1 second. Due tasks are dequeued and either executed (periodic) or moved to the priority queue (one-shot).

## Worker Lifecycle

Workers follow a 6-state machine:

```
INIT → STARTING → RUNNING → DRAINING → STOPPING → STOPPED
```

- **RUNNING**: Full operation — accepts and processes tasks
- **DRAINING**: Finishes in-flight tasks, rejects new work
- **STOPPED**: All sockets closed, process exits

Graceful shutdown respects `shutdown_timeout` (default 30s). In-flight tasks past the timeout are cancelled.

## Result Cache

An in-memory LRU cache using `collections.OrderedDict`:

- **Store**: `_store_result(result)` — evicts LRU entry when at `max_size`
- **Retrieve**: `_get_result(task_id)` — updates access time, checks TTL
- **Cleanup**: Background task runs every 60 seconds, removes expired entries

Default: 10,000 entries, 1-hour TTL.

## Concurrency Model

Each worker uses `asyncio.Semaphore` to limit concurrent task executions:

```python
self._concurrency_semaphore = asyncio.Semaphore(self.concurrency)

async def _execute_and_respond(self, task, respondent):
    async with self._concurrency_semaphore:
        result = await self._execute_task(task)
    await respondent.send(...)
```

A control plane spawns separate asyncio tasks for each priority level, and the subworker management runs in its own loop.

## Event Bus

An `asyncio.Queue`-based pub/sub system that powers the GUI's Server-Sent Events (SSE) stream:

```python
event_bus.emit("task.started", {"task_id": id, "name": name})
# → GUI SSE clients receive the event
# → Telemetry exporters receive the event
```

Events are fire-and-forget — subscribers are observers, not participants.
