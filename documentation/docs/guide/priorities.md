# Task Priorities

FastWorker supports four priority levels for task execution.

## Priority Levels

| Priority | Value | Description |
|----------|-------|-------------|
| `CRITICAL` | 0 | Highest priority, processed first |
| `HIGH` | 1 | High priority |
| `NORMAL` | 2 | Default priority |
| `LOW` | 3 | Lowest priority, processed last |

## Using Priorities

### With Enum

```python
from fastworker import Client
from fastworker.tasks.models import TaskPriority

client = Client()
await client.start()

# Critical - processed first
await client.delay("urgent_alert", data, priority=TaskPriority.CRITICAL)

# High priority
await client.delay("important_task", data, priority=TaskPriority.HIGH)

# Normal (default)
await client.delay("regular_task", data, priority=TaskPriority.NORMAL)

# Low - processed last
await client.delay("background_task", data, priority=TaskPriority.LOW)
```

### With String

```python
await client.delay("my_task", priority="critical")
await client.delay("my_task", priority="high")
await client.delay("my_task", priority="normal")
await client.delay("my_task", priority="low")
```

## How Priority Works

### Separate Queues

Each priority level has its own queue:

```
Control Plane
├── Critical Queue ──> Processed first
├── High Queue ──────> Processed second
├── Normal Queue ────> Processed third
└── Low Queue ───────> Processed last
```

### Processing Order

1. Workers always check the CRITICAL queue first
2. If CRITICAL is empty, check HIGH
3. If HIGH is empty, check NORMAL
4. If NORMAL is empty, check LOW

This means:

- Critical tasks are never delayed by lower-priority tasks
- Low-priority tasks may be delayed if higher-priority tasks keep arriving

## Port Allocation

Each priority level uses a different port:

| Priority | Port Offset | Example (base 5555) |
|----------|-------------|---------------------|
| CRITICAL | Base + 0 | 5555 |
| HIGH | Base + 1 | 5556 |
| NORMAL | Base + 2 | 5557 |
| LOW | Base + 3 | 5558 |

## Use Cases

### Critical Priority

Use for:

- System alerts
- Security events
- User-blocking operations

```python
await client.delay("send_security_alert", user_id, priority=TaskPriority.CRITICAL)
```

### High Priority

Use for:

- Important business operations
- Time-sensitive processing
- User-facing notifications

```python
await client.delay("send_order_confirmation", order_id, priority=TaskPriority.HIGH)
```

### Normal Priority (Default)

Use for:

- Standard background tasks
- Regular processing

```python
await client.delay("process_upload", file_id)  # Uses NORMAL by default
```

### Low Priority

Use for:

- Analytics and logging
- Cleanup tasks
- Non-urgent processing

```python
await client.delay("track_analytics", event_data, priority=TaskPriority.LOW)
```

## Best Practices

### 1. Use Critical Sparingly

```python
# Good - actual critical task
await client.delay("fraud_alert", transaction_id, priority=TaskPriority.CRITICAL)

# Bad - not really critical
await client.delay("send_newsletter", priority=TaskPriority.CRITICAL)
```

### 2. Default to Normal

Most tasks should use the default NORMAL priority:

```python
# Let most tasks be normal
await client.delay("process_data", data)  # Normal is default
```

### 3. Use Low for Background Work

```python
# Analytics can wait
await client.delay("track_page_view", page_data, priority=TaskPriority.LOW)

# Cleanup can wait
await client.delay("cleanup_temp_files", priority=TaskPriority.LOW)
```

### 4. Monitor Queue Sizes

Watch for queues building up, which indicates:

- Too many high-priority tasks
- Not enough workers
- Tasks taking too long

## Viewing Queues

### Via Management GUI

The built-in GUI at `http://127.0.0.1:8080` shows queue sizes for each priority level.

### Via REST API

```bash
curl http://127.0.0.1:8080/api/queues
```

Returns:

```json
{
  "queues": {
    "critical": {"count": 0, "tasks": []},
    "high": {"count": 1, "tasks": [{"id": "abc123", "name": "urgent_task"}]},
    "normal": {"count": 3, "tasks": [...]},
    "low": {"count": 1, "tasks": [...]}
  },
  "total_queued": 5
}
```
