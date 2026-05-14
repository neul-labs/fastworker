# Why FastWorker?

FastWorker is a brokerless task queue for Python. If you need background tasks but don't want to manage Redis, RabbitMQ, or cloud infrastructure, FastWorker is for you.

## The Problem

Background task processing is a universal need:

- Send emails without blocking the HTTP response
- Generate reports asynchronously
- Run periodic cleanup jobs
- Process uploaded files in the background

The standard solution is Celery + Redis/RabbitMQ. It works, but it requires:

1. **Install and configure** a broker (Redis/RabbitMQ)
2. **Install and configure** Celery
3. **Manage** multiple processes (worker, beat scheduler, monitoring)
4. **Secure** the broker (network, auth, TLS)
5. **Monitor** broker health, memory, connection limits
6. **Deploy** all of it consistently across environments

That's 4-6 services before you've written a single line of business logic.

## The FastWorker Approach

FastWorker eliminates the broker entirely. It uses a control plane with built-in NNG (nanomsg-next-generation) messaging — workers connect directly, discover each other automatically, and coordinate task distribution without any external service.

**What you deploy:**
- 1 control plane process (includes dashboard)
- N subworker processes (optional, for scaling)
- Your application with the FastWorker client

**What you don't deploy:**
- No Redis
- No RabbitMQ
- No beat scheduler
- No Flower
- No broker monitoring

## When to Use FastWorker

### Good fit

- Python monoliths or microservices
- 1K-10K tasks per minute
- Web apps (FastAPI, Flask, Django)
- Periodic/cron jobs
- File processing pipelines
- Notification/email dispatch
- Teams of 1-10 developers

### Not a good fit

- 100K+ tasks per minute (use Celery + Redis cluster)
- Multi-language workers (use RabbitMQ)
- Complex DAG workflows (use Airflow or Temporal)
- Strict durability guarantees (use a database-backed queue)
- Teams requiring broker-level HA (active/passive, clustering)

See the full [Limitations & Scope](limitations.md) doc for details.

## Trade-offs

| | FastWorker | Celery + Redis |
|---|---|---|
| **Simplicity** | Excellent — zero infrastructure | Poor — 4-6 moving parts |
| **Setup speed** | 30 seconds | 30+ minutes |
| **Maximum throughput** | ~10K tasks/min | 100K+ tasks/min |
| **Durability** | In-memory (at-least-once) | Redis persistence (configurable) |
| **Ecosystem maturity** | New (v0.3.0) | Battle-tested (10+ years) |
| **Multi-language** | Python only | Any language |
| **Workflow orchestration** | Not supported | Canvas/Chord/Chain |
| **Operational overhead** | Near zero | Significant |
