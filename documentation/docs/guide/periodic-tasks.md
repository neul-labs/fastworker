# Periodic & Cron Tasks

FastWorker supports recurring task execution using either interval-based scheduling or cron expressions. No external scheduler required.

## Quick Start

```python
from fastworker import task


@task(repeat_interval=60)  # runs every 60 seconds
def cleanup_sessions():
    ...


@task(cron="0 */6 * * *")  # runs every 6 hours
def generate_reports():
    ...
```

Start the control plane normally — periodic tasks are scheduled automatically:

```bash
fastworker control-plane --task-modules mytasks
```

## Interval-Based Scheduling

Use `repeat_interval` (in seconds) for fixed-interval execution:

```python
@task(repeat_interval=30)
def heartbeat():
    """Runs every 30 seconds."""
    ...

@task(repeat_interval=3600)
def hourly_cleanup():
    """Runs every hour."""
    ...
```

The first execution happens immediately on startup. Subsequent executions are spaced by `repeat_interval` seconds from the time the previous execution **started** (not completed).

## Cron-Based Scheduling

Use `cron` with a standard 5-field cron expression:

```
minute hour day-of-month month day-of-week
```

| Field | Range | Example |
|---|---|---|
| minute | 0-59 | `0`, `*/15`, `30` |
| hour | 0-23 | `0`, `*/6`, `9` |
| day-of-month | 1-31 | `1`, `15`, `*` |
| month | 1-12 | `*`, `1`, `6` |
| day-of-week | 0-6 (Sun=0) | `0`, `1-5`, `*` |

### Common Patterns

```python
@task(cron="*/5 * * * *")    # every 5 minutes
@task(cron="0 * * * *")      # every hour at minute 0
@task(cron="0 9 * * 1-5")    # weekdays at 9am
@task(cron="0 0 1 * *")      # midnight on the 1st of each month
@task(cron="0 3 * * 0")      # Sundays at 3am
@task(cron="*/30 9-17 * * 1-5")  # every 30 minutes during business hours
```

### Supported Syntax

- `*` — any value
- `*/N` — step (every N)
- `1,3,5` — list
- `1-5` — range
- `1-5/2` — range with step

## Execution Limits

### Repeat Count

Limit how many times a periodic task executes:

```python
@task(repeat_interval=60, repeat_count=10)
def limited_task():
    """Runs exactly 10 times, then stops."""
    ...
```

### Repeat Until

Stop recurring after a specific time:

```python
from datetime import datetime, timedelta

end_time = (datetime.now() + timedelta(hours=24)).isoformat()

@task(repeat_interval=300, repeat_until=end_time)
def temporary_job():
    """Runs for 24 hours, then stops."""
    ...
```

## Skip-If-Running Guard

If a periodic task is still executing when its next scheduled time arrives, the new execution is **skipped** (not queued). This prevents task pile-up. The task will execute again at the next scheduled interval after the current run completes.

```python
@task(repeat_interval=5)  # if this takes >5 seconds, the next tick is skipped
def slow_task():
    import time
    time.sleep(10)
```

## CLI: Listing Periodic Tasks

```bash
fastworker list --task-modules mytasks --list-periodic
```

Output:
```
Periodic tasks:
  - cleanup_sessions [repeat_interval=3600s]
  - generate_reports [cron="0 */6 * * *"]
  - heartbeat [repeat_interval=30s (count=100)]
  - temporary_job [repeat_interval=300s (until=2026-01-02T12:00:00)]
```

## Viewing in the GUI

Periodic tasks appear in the management GUI (http://127.0.0.1:8080) under the Tasks tab. Each execution creates a new task instance with a unique task ID. The schedule metadata is visible in the periodic tasks list.

## Combining Periodic and Non-Periodic Task Modules

Periodic and regular tasks coexist in the same module. Only tasks with `repeat_interval` or `cron` are treated as periodic:

```python
from fastworker import task


@task                          # regular task
def send_notification(user_id: int, message: str):
    ...

@task(repeat_interval=300)    # periodic task
def refresh_cache():
    ...

@task(cron="0 9 * * *")       # periodic task
def daily_summary():
    ...
```
