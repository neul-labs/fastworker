# Result Caching

The control plane maintains a result cache for storing task results.

## Overview

- **In-Memory Cache**: Results stored in control plane memory
- **LRU Eviction**: Least recently used results evicted when cache is full
- **TTL Expiration**: Results automatically expire after configured time
- **Automatic Cleanup**: Expired results cleaned up every minute

## Configuration

### CLI Options

```bash
fastworker control-plane \
  --result-cache-size 20000 \
  --result-cache-ttl 7200 \
  --task-modules mytasks
```

### Environment Variables

```bash
export FASTWORKER_RESULT_CACHE_SIZE=20000
export FASTWORKER_RESULT_CACHE_TTL=7200
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--result-cache-size` | `10000` | Maximum number of results to cache |
| `--result-cache-ttl` | `3600` | TTL in seconds (default: 1 hour) |

## Querying Results

### Using Client

```python
result = await client.get_task_result(task_id)

if result:
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Completed: {result.completed_at}")
else:
    print("Result not found or expired")
```

### Using CLI

```bash
fastworker status --task-id <uuid>
```

### Using REST API

```bash
curl http://127.0.0.1:8080/api/tasks?limit=50
```

## Cache Behavior

### LRU Eviction

When the cache reaches its maximum size:

1. Least recently accessed results are evicted first
2. Accessing a result updates its "last accessed" time
3. New results are always added (evicting old ones if needed)

### TTL Expiration

- Results expire after the configured TTL
- Expired results are removed during cleanup (every 60 seconds)
- Querying an expired result returns `None`

### Example Timeline

```
Time 0:00 - Task A completes, result cached
Time 0:30 - Task A result queried (still valid)
Time 1:00 - Task A result still valid (within 1 hour TTL)
Time 1:01 - Cleanup runs, Task A result still valid
Time 1:30 - Task A result queried (still valid)
Time 2:00 - Task A result expires (TTL exceeded)
Time 2:01 - Cleanup runs, Task A result removed
```

## Monitoring Cache

### Via REST API

```bash
curl http://127.0.0.1:8080/api/cache
```

Returns:

```json
{
  "max_size": 10000,
  "current_size": 150,
  "utilization_percent": 1.5,
  "ttl_seconds": 3600,
  "by_status": {
    "success": 140,
    "failure": 10
  }
}
```

### Via Management GUI

The built-in GUI shows:

- Cache utilization percentage
- Current number of cached results
- Maximum cache size
- Results by status

## Best Practices

### 1. Size Cache Appropriately

Consider your task volume:

```bash
# Low volume: 1-100 tasks/minute
--result-cache-size 5000

# Medium volume: 100-1000 tasks/minute
--result-cache-size 10000

# High volume: 1000-10000 tasks/minute
--result-cache-size 50000
```

### 2. Set Appropriate TTL

Balance availability vs memory:

```bash
# Short-lived results (15 minutes)
--result-cache-ttl 900

# Standard (1 hour, default)
--result-cache-ttl 3600

# Long-lived results (4 hours)
--result-cache-ttl 14400
```

### 3. Store Important Results Externally

For results you need to keep:

```python
@task
def important_task(data):
    result = process(data)

    # Store in your database
    db.save_result(task_id, result)

    return result
```

### 4. Handle Missing Results

```python
result = await client.get_task_result(task_id)

if result is None:
    # Result expired or never existed
    # Consider re-submitting the task
    pass
```

## Limitations

- **In-Memory Only**: Results lost if control plane restarts
- **Size Limited**: Large results consume more memory
- **TTL Limited**: Results expire after configured time

For persistent storage, implement your own database integration:

```python
@task
def persistent_task(data):
    result = process(data)

    # Store in persistent storage
    redis_client.setex(f"result:{task_id}", 86400, json.dumps(result))

    return result
```
