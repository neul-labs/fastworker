# Limitations and Scope

This document clarifies what FastWorker is designed for, where it excels, and where it may not be the right choice.

## What FastWorker Is

FastWorker is a **lightweight, brokerless task queue** for Python applications that need:

- Simple distributed task processing without complex infrastructure
- Zero external dependencies (no Redis, RabbitMQ)
- Fast deployment with minimal configuration
- Direct peer-to-peer communication
- Built-in service discovery
- Priority-based task execution

## Design Philosophy

- **Simplicity over features**: Easy to understand and deploy
- **Self-contained systems**: No external brokers or databases
- **Python-first**: Optimized for Python applications
- **Moderate scale**: Thousands of tasks, not millions per second

---

## Deployment Simplicity

### Traditional Stack (Celery + Redis)

```
Components to deploy:
✗ Your application
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
✓ Your application
✓ FastWorker control plane
✓ FastWorker subworkers (optional)

Total: 2-3 Python processes
```

---

## Where FastWorker Excels

### Ideal Use Cases

1. **Web Application Background Tasks**
   - Image processing, report generation, email sending
   - PDF generation, webhook notifications

2. **Microservices Task Distribution**
   - Coordinating tasks across services

3. **Development and Testing**
   - No external dependencies
   - Fast iteration cycles

4. **Small to Medium Scale**
   - 100-10,000 tasks per minute
   - 1-50 workers

5. **Priority-Based Processing**
   - Built-in priority queues

---

## Limitations

### Not Suitable For

| Limitation | Description | Alternative |
|------------|-------------|-------------|
| **Extreme Scale** | Millions of tasks/second | Kafka, RabbitMQ |
| **Task Persistence** | Tasks in-memory only | Celery with backends |
| **Multi-Language** | Python-only | RabbitMQ, NATS |
| **Complex Workflows** | No chains, DAGs | Airflow, Temporal |
| **Long-Running Tasks** | No checkpointing | Temporal, Airflow |
| **Exactly-Once Delivery** | At-most-once semantics | Kafka |

### Task Persistence

**Limitation:** Tasks are in-memory only. If control plane crashes, queued tasks are lost.

**Workaround:**

```python
# Store task state before submission
db.save_task(task_id, "pending", data)
await client.delay("my_task", data)
```

### Multi-Language Support

**Limitation:** Python-only. Workers and clients must be Python.

### Complex Workflows

**Limited support for:**

- Task chains (A → B → C)
- Conditional routing
- Task dependencies and DAGs
- Scheduled/cron tasks

**Workaround:**

```python
@task
def task_with_retry():
    for attempt in range(3):
        try:
            return do_work()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
```

### Long-Running Tasks

**Not ideal for:**

- Tasks running hours/days
- Tasks requiring checkpointing
- Tasks requiring pause/resume

### Result Storage

**Limitation:**

- Results in-memory with LRU eviction
- Default TTL of 1 hour

**Workaround:**

```python
@task
def my_task(data):
    result = process(data)
    db.save_result(task_id, result)  # Store in your database
    return result
```

---

## Performance Characteristics

### Throughput

| Scale | Tasks/minute | Performance |
|-------|--------------|-------------|
| Low | 100-1,000 | Excellent |
| Medium | 1,000-10,000 | Good |
| High | 10,000-100,000 | Degraded |
| Extreme | 100,000+ | Not recommended |

### Worker Scaling

| Workers | Performance |
|---------|-------------|
| 1-20 | Optimal |
| 20-50 | Good |
| 50-100 | Degraded |
| 100+ | Not recommended |

---

## Comparison with Alternatives

### FastWorker vs Celery

| Feature | FastWorker | Celery |
|---------|-----------|--------|
| External dependencies | None | Redis/RabbitMQ |
| Setup complexity | Very low | Medium |
| Scalability | Moderate | High |
| Task workflows | Basic | Advanced |
| Monitoring | Built-in GUI | Flower UI |

### FastWorker vs RabbitMQ

| Feature | FastWorker | RabbitMQ |
|---------|-----------|----------|
| Setup complexity | Very low | Medium-High |
| Language support | Python only | Multi-language |
| Message persistence | No | Yes |
| Delivery guarantees | At-most-once | Configurable |

### FastWorker vs Cloud Queues (SQS)

| Feature | FastWorker | Cloud Queues |
|---------|-----------|--------------|
| Cost | Free (self-hosted) | Pay per request |
| Vendor lock-in | None | High |
| Scalability | Moderate | Unlimited |
| Multi-region | Manual | Built-in |

---

## When to Choose FastWorker

### Choose FastWorker If:

- You want zero external dependencies
- You have a Python-only stack
- You need moderate scale (1K-10K tasks/min)
- You want fast development iteration
- You need priority queues
- You value simplicity

### Consider Alternatives If:

- You need extreme scale (millions/second)
- You need task persistence
- You have multi-language requirements
- You need complex workflows
- You need exactly-once guarantees
- You need geo-distribution

---

## Anti-Patterns

### Don't Use FastWorker For:

**Critical Financial Transactions:**

```python
# Bad - no persistence, no exactly-once
@task
def process_payment(amount, account):
    charge_credit_card(amount)  # Could be lost!
```

**Massive Task Arguments:**

```python
# Bad - large data in arguments
@task
def process_file(file_data):  # 100MB!
    return analyze(file_data)

# Good - pass reference
@task
def process_file(file_path):
    with open(file_path) as f:
        return analyze(f.read())
```

**Long-Term Result Storage:**

```python
# Bad - results expire after 1 hour
task_id = await client.delay("generate_report", user_id)
# Come back tomorrow...
result = await client.get_task_result(task_id)  # Will be None!
```

---

## Summary

### FastWorker is Excellent For:

- Simple background task processing
- Python-only stacks
- Development and testing
- Small to medium scale
- Zero-dependency deployments

### FastWorker is NOT Suitable For:

- Extreme scale (100K+ tasks/min)
- Multi-language environments
- Mission-critical systems requiring persistence
- Complex workflow orchestration
- Geo-distributed deployments

**The right tool for the right job.** FastWorker fills a specific niche: lightweight, zero-dependency task queues for Python applications at moderate scale.
