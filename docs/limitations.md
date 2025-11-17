# Limitations and Scope

This document clarifies what FastWorker is designed for, where it excels, and where it may not be the right choice.

## What FastWorker Is

FastWorker is a **lightweight, brokerless task queue** for Python applications that need:

- **Simple distributed task processing** without complex infrastructure
- **Zero external dependencies** (no Redis, RabbitMQ, etc.)
- **Fast deployment** with minimal configuration
- **Direct peer-to-peer communication** for reduced latency
- **Built-in service discovery** for automatic worker coordination
- **Priority-based task execution** with multiple priority levels

### Design Philosophy

FastWorker is designed for:
- **Simplicity over features**: Easy to understand and deploy
- **Self-contained systems**: No external brokers or databases required
- **Python-first**: Optimized for Python applications
- **Moderate scale**: Thousands of tasks, not millions per second

---

## Deployment Simplicity: The Key Advantage

### Traditional Task Queue Stack

A typical Celery-based deployment requires **multiple components**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ FastAPI  │───▶│  Celery  │───▶│  Redis   │              │
│  │   App    │    │  Client  │    │  Broker  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                        │                     │
│                                        ▼                     │
│                   ┌─────────────────────────────┐           │
│                   │   Celery Workers (Python)   │           │
│                   └─────────────────────────────┘           │
│                                        │                     │
│                                        ▼                     │
│                   ┌─────────────────────────────┐           │
│                   │ Redis Result Backend        │           │
│                   │ (or PostgreSQL/MongoDB)     │           │
│                   └─────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘

Components to deploy, manage, and monitor:
✗ Your application server
✗ Redis broker (or RabbitMQ - even more complex!)
✗ Celery workers
✗ Redis result backend (or separate database)
✗ Optional: Flower monitoring dashboard
✗ Optional: Redis Sentinel for HA

Total: 4-6+ separate services
```

### FastWorker Deployment

FastWorker requires **only Python workers**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  ┌──────────┐    ┌──────────────┐                           │
│  │ FastAPI  │───▶│  FastWorker   │                           │
│  │   App    │    │    Client    │                           │
│  └──────────┘    └──────────────┘                           │
│                          │                                   │
│                          ▼                                   │
│         ┌─────────────────────────────────────┐             │
│         │  FastWorker Control Plane (Python)   │             │
│         │  • Coordinates tasks                │             │
│         │  • Caches results                   │             │
│         │  • Manages workers                  │             │
│         └─────────────────────────────────────┘             │
│                          │                                   │
│                          ▼                                   │
│         ┌─────────────────────────────────────┐             │
│         │   FastWorker Subworkers (Python)     │             │
│         │   • Process tasks                   │             │
│         │   • Auto-discovered                 │             │
│         └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘

Components to deploy, manage, and monitor:
✓ Your application server
✓ FastWorker control plane (Python process)
✓ FastWorker subworkers (Python processes) - optional for scaling

Total: 2-3 Python services (no external dependencies!)
```

### The Difference

| Aspect | Traditional (Celery + Redis) | FastWorker |
|--------|------------------------------|-----------|
| **Components** | 4-6+ services | 2-3 Python processes |
| **External dependencies** | Redis/RabbitMQ required | None |
| **Languages/Runtimes** | Python + Redis/Erlang | Python only |
| **Configuration files** | Multiple (Celery, Redis, workers) | Minimal (env vars) |
| **Ports to manage** | Multiple services × ports | Single service × 4-5 ports |
| **Monitoring targets** | Each service separately | Python processes only |
| **Security surface** | Redis auth, network security, etc. | Python process security |
| **Failure points** | Broker, backend, workers | Control plane, workers |
| **Operational knowledge** | Python + Redis/RabbitMQ + Celery | Python only |

---

## Real-World Deployment Comparison

### Example 1: Docker Compose

**Traditional Stack (Celery + Redis):**

```yaml
# docker-compose.yml - Traditional
version: '3.8'

services:
  # Your application
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  # Redis broker (external dependency #1)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Celery workers
  celery_worker:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  # Optional: Flower monitoring (external dependency #2)
  flower:
    build: .
    command: celery -A tasks flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:

# Services: 4 (web, redis, celery_worker, flower)
# External dependencies: 2 (Redis, Flower)
# Configuration complexity: High
```

**FastWorker:**

```yaml
# docker-compose.yml - FastWorker
version: '3.8'

services:
  # Your application
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTWORKER_DISCOVERY_ADDRESS=tcp://control-plane:5550
    depends_on:
      - control-plane

  # FastWorker control plane (pure Python)
  control-plane:
    build: .
    command: fastworker control-plane --task-modules tasks
    ports:
      - "5550-5560:5550-5560"
    environment:
      - FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5555

  # Optional: FastWorker subworkers for scaling (pure Python)
  subworker:
    build: .
    command: fastworker subworker --task-modules tasks
    environment:
      - FASTWORKER_CONTROL_PLANE_ADDRESS=tcp://control-plane:5555
      - FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5561
    depends_on:
      - control-plane
    deploy:
      replicas: 2

# Services: 3 (web, control-plane, subworker)
# External dependencies: 0 (all Python!)
# Configuration complexity: Low
```

**Comparison:**
- **Services**: 4 vs 3
- **External dependencies**: 2 vs 0 ✅
- **Docker images**: 2+ (Python + Redis) vs 1 (Python only) ✅
- **Volumes**: 1 (Redis persistence) vs 0 ✅
- **Configuration**: Complex vs Simple ✅

---

### Example 2: Kubernetes Deployment

**Traditional Stack (Celery + Redis):**

```yaml
# Traditional Kubernetes - Multiple manifests needed

# 1. Redis Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
# 2. Redis Service
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
  - port: 6379
---
# 3. Celery Worker Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: worker
        image: myapp:latest
        command: ["celery", "-A", "tasks", "worker"]
        env:
        - name: CELERY_BROKER_URL
          value: redis://redis:6379/0
---
# 4. Web App Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: web
        image: myapp:latest
        env:
        - name: CELERY_BROKER_URL
          value: redis://redis:6379/0
---
# 5. ConfigMap for shared config
apiVersion: v1
kind: ConfigMap
metadata:
  name: celery-config
data:
  CELERY_BROKER_URL: redis://redis:6379/0
---
# 6. Optional: Redis PersistentVolumeClaim
# 7. Optional: Redis StatefulSet for HA
# 8. Optional: Flower deployment for monitoring

# Total manifests: 6-8+
# Total pods: 6+ (web×2, redis×1, celery×3, flower×1)
```

**FastWorker:**

```yaml
# FastWorker Kubernetes - Simpler

# 1. Control Plane Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastworker-control-plane
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: control-plane
        image: myapp:latest
        command: ["fastworker", "control-plane", "--task-modules", "tasks"]
        ports:
        - containerPort: 5550
        - containerPort: 5555
---
# 2. Control Plane Service
apiVersion: v1
kind: Service
metadata:
  name: control-plane
spec:
  ports:
  - name: discovery
    port: 5550
  - name: tasks
    port: 5555
---
# 3. Subworker Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastworker-subworker
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: subworker
        image: myapp:latest
        command: ["fastworker", "subworker", "--task-modules", "tasks"]
        env:
        - name: FASTWORKER_CONTROL_PLANE_ADDRESS
          value: tcp://control-plane:5555
---
# 4. Web App Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: web
        image: myapp:latest
        env:
        - name: FASTWORKER_DISCOVERY_ADDRESS
          value: tcp://control-plane:5550

# Total manifests: 4
# Total pods: 6 (web×2, control-plane×1, subworker×3)
# No external services needed!
```

**Comparison:**
- **Manifests**: 6-8+ vs 4 ✅
- **Pod types**: 4+ vs 3 ✅
- **External services**: Redis vs None ✅
- **Persistent volumes**: Required vs Optional ✅
- **Container images**: 2+ vs 1 ✅

---

## Operational Benefits

### 1. Reduced Infrastructure Complexity

**Traditional:**
```
You need to know:
• Redis administration
• Redis persistence and snapshotting
• Redis memory management
• Redis clustering/replication for HA
• Celery configuration
• Celery broker connection management
• Result backend tuning
• Multiple service monitoring
```

**FastWorker:**
```
You need to know:
• Python process management
• Environment variables
• Basic networking (ports)
```

### 2. Fewer Moving Parts = Less to Break

**Traditional failure scenarios:**
- Redis broker crashes → all tasks fail
- Redis out of memory → task submissions fail
- Network issue to Redis → workers can't get tasks
- Result backend down → can't retrieve results
- Celery version mismatch → incompatibility issues

**FastWorker failure scenarios:**
- Control plane crashes → tasks in queue lost (restart recovers)
- Subworker crashes → control plane redistributes tasks
- Network issue → automatic reconnection built-in

### 3. Simplified Monitoring

**Traditional monitoring requirements:**
```
Monitor:
✗ Redis CPU, memory, disk I/O
✗ Redis connection count
✗ Redis keyspace
✗ Celery worker health
✗ Celery queue lengths
✗ Celery task success/failure rates
✗ Result backend health
✗ Network connectivity between services
```

**FastWorker monitoring requirements:**
```
Monitor:
✓ Control plane Python process health
✓ Subworker Python process health
✓ Task success/failure rates (application-level)
```

### 4. Security Simplification

**Traditional security concerns:**
```
✗ Redis authentication
✗ Redis network encryption (TLS)
✗ Redis ACLs
✗ Firewall rules for Redis ports
✗ Broker credential management
✗ Result backend authentication
✗ Multiple services to patch/update
```

**FastWorker security concerns:**
```
✓ Python process security
✓ Network firewall for FastWorker ports
✓ Standard Python security practices
✓ Single codebase to patch/update
```

### 5. Cost Savings

**Traditional costs:**
```
• Redis server resources (CPU, RAM, disk)
• Redis HA/clustering infrastructure
• Potential Redis license costs (Redis Enterprise)
• Monitoring tools for Redis
• Staff time learning/managing Redis
• Backup storage for Redis snapshots
```

**FastWorker costs:**
```
• Python worker resources only
• No external service costs
• No specialized tooling needed
• Staff only needs Python knowledge
```

---

## Development Experience

### Local Development Setup

**Traditional (Celery + Redis):**

```bash
# Terminal 1: Start Redis
docker run -p 6379:6379 redis

# Terminal 2: Start your app
export CELERY_BROKER_URL=redis://localhost:6379
uvicorn main:app --reload

# Terminal 3: Start Celery worker
celery -A tasks worker --loglevel=info

# Terminal 4: Optional - Start Flower
celery -A tasks flower

# Required: 3-4 terminals, Docker, Redis knowledge
```

**FastWorker:**

```bash
# Terminal 1: Start control plane
fastworker control-plane --task-modules tasks

# Terminal 2: Start your app
uvicorn main:app --reload

# Optional Terminal 3: Add subworker for testing scaling
fastworker subworker --worker-id sw1 --task-modules tasks

# Required: 2 terminals, no Docker needed!
```

### Testing

**Traditional:**
```python
# tests/test_tasks.py
import pytest
from celery import Celery

@pytest.fixture
def celery_app():
    # Need to mock/setup Redis connection
    app = Celery(broker='redis://localhost:6379/0')
    return app

def test_task(celery_app):
    # Complex test setup
    result = my_task.apply_async()
    # Need Redis running for integration tests
```

**FastWorker:**
```python
# tests/test_tasks.py
import pytest
from fastworker import Client

@pytest.fixture
async def fastworker_client():
    # No external dependencies!
    client = Client()
    await client.start()
    yield client
    client.stop()

async def test_task(fastworker_client):
    # Simple test, no Redis needed
    result = await fastworker_client.delay("my_task", arg1, arg2)
```

---

## Migration Path: Simplifying Your Stack

### Before: Traditional Stack

```
┌─────────────┐
│   Your App  │
└─────┬───────┘
      │
      ▼
┌─────────────┐     ┌─────────────┐
│   Celery    │────▶│    Redis    │ ← Need to manage
└─────────────┘     └─────────────┘
      │                     │
      ▼                     ▼
┌─────────────┐     ┌─────────────┐
│   Workers   │     │   Results   │
└─────────────┘     └─────────────┘

Components: 5
Languages/Runtimes: 2 (Python, Redis)
Ops Complexity: High
```

### After: FastWorker

```
┌─────────────┐
│   Your App  │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  FastWorker  │ ← Pure Python
│Control Plane│
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Subworkers │ ← Pure Python
└─────────────┘

Components: 3
Languages/Runtimes: 1 (Python)
Ops Complexity: Low
```

### What You Eliminate

- ❌ Redis server deployment and management
- ❌ Redis monitoring and alerting
- ❌ Redis backup and recovery
- ❌ Redis version upgrades
- ❌ Redis memory tuning
- ❌ Redis authentication setup
- ❌ Result backend configuration
- ❌ Broker connection pool tuning
- ❌ Multiple service dependencies

### What You Keep

- ✅ Python workers (you already have these!)
- ✅ Your task code (minimal changes)
- ✅ Python monitoring tools you already use
- ✅ Python security practices you already follow

---

## Where FastWorker Excels

### ✅ Ideal Use Cases

#### 1. Web Application Background Tasks

Perfect for offloading work from web requests:

```python
# FastAPI example
@app.post("/process/")
async def process_data(data: dict):
    # Offload heavy processing to background
    task_id = await client.delay("process_data", data)
    return {"task_id": task_id}
```

**Good for:**
- Image processing and resizing
- Report generation
- Email sending
- Data validation and enrichment
- PDF generation
- Webhook notifications

#### 2. Microservices Task Distribution

Ideal for coordinating tasks across microservices:

```python
# Service A submits task
await client.delay("sync_user_data", user_id)

# Service B processes it
@task
def sync_user_data(user_id):
    # Sync data across services
    pass
```

#### 3. Development and Testing

Excellent for development environments:

- No external dependencies to set up
- Fast iteration cycles
- Easy debugging with Python tooling
- Lightweight for local development

#### 4. Small to Medium Scale Deployments

Works well for:
- **Task volume**: Hundreds to thousands of tasks per minute
- **Worker count**: 1-50 workers
- **Data size**: KB to low MB per task
- **Network**: Single datacenter or low-latency network

#### 5. Priority-Based Processing

Strong support for priority queues:

```python
# Critical tasks processed first
await client.delay("urgent_alert", priority=TaskPriority.CRITICAL)
await client.delay("send_email", priority=TaskPriority.LOW)
```

#### 6. Real-time Task Callbacks

Built-in callback support for reactive workflows:

```python
# Get notified when task completes
await client.delay_with_callback(
    "process_order",
    callback_address,
    order_id
)
```

---

## Limitations and Constraints

### ❌ Where FastWorker May Not Be Suitable

#### 1. Extreme Scale Requirements

**Not ideal for:**
- **Millions of tasks per second**
- **Hundreds or thousands of workers**
- **Global distribution across multiple datacenters**

**Why:** FastWorker uses direct peer-to-peer connections, which don't scale as efficiently as broker-based systems at extreme scale.

**Alternative:** Use RabbitMQ, Apache Kafka, or cloud-based queues (AWS SQS, Google Cloud Tasks).

#### 2. Task Persistence Requirements

**Limitation:** Tasks are **in-memory only**. If the control plane crashes, queued tasks are lost.

**Not suitable for:**
- Mission-critical financial transactions
- Tasks that absolutely cannot be lost
- Long-term task storage (days/weeks)

**Workaround:**
- Implement application-level persistence
- Use at-least-once delivery patterns
- Store task state externally before submission

**Alternative:** RabbitMQ with persistent queues, Celery with result backends.

#### 3. Multi-Language Support

**Limitation:** FastWorker is **Python-only**. Workers and clients must be Python applications.

**Not suitable for:**
- Polyglot microservices (Python, Go, Java, Node.js mixed)
- Language-agnostic task queues

**Alternative:** RabbitMQ, Apache Kafka, NATS, or cloud-based queues support multiple languages.

#### 4. Complex Routing and Workflows

**Limited support for:**
- Task chains and workflows (task A → task B → task C)
- Conditional routing based on task results
- Complex retry policies with exponential backoff
- Scheduled/cron-like periodic tasks
- Task dependencies and DAGs (Directed Acyclic Graphs)

**Alternative:**
- **Celery**: Chains, groups, chords, workflows
- **Apache Airflow**: Complex DAGs and scheduling
- **Temporal**: Durable workflow orchestration
- **Prefect**: Modern workflow orchestration

#### 5. Long-Running Tasks (Hours/Days)

**Not ideal for:**
- Tasks that run for hours or days
- Tasks requiring checkpointing
- Tasks requiring pause/resume functionality

**Why:**
- Result cache has TTL (default 1 hour)
- No built-in checkpointing
- Workers hold connections open

**Alternative:**
- **Celery** with result backends for long tasks
- **Temporal** for durable long-running workflows
- Job schedulers like **Apache Airflow**

#### 6. Exactly-Once Delivery Guarantees

**Limitation:** FastWorker provides **at-most-once** delivery semantics.

- If a worker crashes during task execution, the task may be lost
- No automatic retry on worker failure
- No distributed transaction support

**Not suitable for:**
- Financial transactions requiring exactly-once processing
- Critical operations that cannot be duplicated or lost

**Alternative:**
- **RabbitMQ** with publisher confirms and consumer acknowledgments
- **Apache Kafka** with transactional guarantees
- Implement idempotency in your task handlers

#### 7. Task Inspection and Monitoring

**Limited capabilities:**
- No built-in web UI for task monitoring
- No flower-like dashboard
- Basic task status tracking only
- Limited metrics and observability

**Not suitable for:**
- Teams requiring detailed task analytics
- Complex monitoring requirements
- Audit trails and compliance tracking

**Alternative:**
- **Celery** with Flower for web UI
- **Apache Airflow** with built-in UI
- Cloud-based solutions with dashboards

#### 8. Advanced Retry Policies

**Limited retry support:**
- Client-side retries only (for submission failures)
- No worker-side automatic retries on task failure
- No exponential backoff strategies
- No retry queues or dead-letter queues

**Workaround:** Implement retry logic in task handlers:

```python
@task
def task_with_retry():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return do_work()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

**Alternative:** Celery with built-in retry decorators.

#### 9. Task Result Storage

**Limitation:**
- Results stored in-memory with LRU eviction
- Default TTL of 1 hour
- Limited by control plane memory

**Not suitable for:**
- Long-term result storage
- Large result data (GB+)
- Audit requirements for all task results

**Workaround:** Store results in your own database:

```python
@task
def my_task(data):
    result = process(data)
    # Store in your database
    db.save_result(task_id, result)
    return result
```

**Alternative:** Celery with Redis/database result backends.

#### 10. Multi-Tenancy and Isolation

**Limited support for:**
- Tenant-specific queues
- Resource quotas per tenant
- Isolated worker pools per customer

**Not suitable for:**
- SaaS platforms with strict tenant isolation
- Multi-tenant applications with resource limits

**Alternative:** Deploy separate FastWorker instances per tenant, or use broker-based solutions with virtual hosts (RabbitMQ).

---

## Architectural Limitations

### Network Requirements

**FastWorker requires:**
- Low-latency network between workers and control plane
- Direct connectivity (no NAT traversal built-in)
- Multiple ports open (one per priority level)

**Not suitable for:**
- Geo-distributed workers across continents
- Workers behind strict firewalls/NAT
- Highly restricted network environments

### Single Control Plane

**Current architecture:**
- One control plane coordinates all work
- Control plane is a single point of coordination (though it can process tasks too)
- Control plane failure impacts task distribution

**Limitation:** No built-in control plane HA/failover.

**Not suitable for:**
- Systems requiring 99.99%+ uptime guarantees
- Mission-critical systems without downtime tolerance

**Mitigation:** Deploy control plane with container orchestration restart policies.

### Memory Constraints

**Control plane stores:**
- Task queue in memory
- Result cache in memory (default 10,000 results)
- Subworker registry in memory

**Impact:**
- Control plane memory grows with queue size
- Large result cache increases memory usage
- Not suitable for millions of queued tasks

---

## Performance Characteristics

### Throughput

**Expected performance:**
- **Low scale**: 100-1,000 tasks/minute - Excellent
- **Medium scale**: 1,000-10,000 tasks/minute - Good
- **High scale**: 10,000-100,000 tasks/minute - Degraded
- **Extreme scale**: 100,000+ tasks/minute - Not recommended

### Latency

**Task submission latency:**
- Local network: <10ms
- Same datacenter: 10-50ms
- Cross-datacenter: Higher latency

**Good for:** Real-time web applications, APIs
**Not ideal for:** Ultra-low latency requirements (<1ms)

### Worker Scaling

**Recommended worker count:**
- Optimal: 1-20 workers
- Good: 20-50 workers
- Degraded: 50-100 workers
- Not recommended: 100+ workers

**Why:** Service discovery and connection overhead increases with worker count.

---

## Comparison with Alternatives

### FastWorker vs Celery

| Feature | FastWorker | Celery |
|---------|-----------|--------|
| External dependencies | None | Redis/RabbitMQ required |
| Setup complexity | Very low | Medium |
| Scalability | Moderate (1K-10K tasks/min) | High (100K+ tasks/min) |
| Task workflows | Basic | Advanced (chains, groups, chords) |
| Result storage | In-memory (1 hour) | Persistent backends |
| Monitoring | Basic | Advanced (Flower UI) |
| Language support | Python only | Python only |
| Multi-datacenter | Limited | Good with proper broker setup |
| **Best for** | Simple background tasks | Complex workflows, high scale |

### FastWorker vs RabbitMQ

| Feature | FastWorker | RabbitMQ |
|---------|-----------|----------|
| Setup complexity | Very low | Medium-High |
| Language support | Python only | Multi-language |
| Message persistence | No | Yes |
| Delivery guarantees | At-most-once | Configurable (at-least-once, exactly-once) |
| Scalability | Moderate | Very high |
| Operational overhead | Low | Medium-High |
| **Best for** | Python applications, simple setups | Multi-language, mission-critical |

### FastWorker vs Cloud Queues (SQS, Cloud Tasks)

| Feature | FastWorker | Cloud Queues |
|---------|-----------|--------------|
| Cost | Free (self-hosted) | Pay per request |
| Setup | Simple | Very simple |
| Vendor lock-in | None | High |
| Scalability | Moderate | Unlimited |
| Persistence | No | Yes |
| Multi-region | Manual | Built-in |
| **Best for** | Self-hosted, cost-sensitive | Cloud-native, unlimited scale |

### FastWorker vs Apache Kafka

| Feature | FastWorker | Kafka |
|---------|-----------|-------|
| Setup complexity | Very low | High |
| Throughput | Moderate | Very high |
| Message retention | 1 hour (results) | Configurable (days/weeks) |
| Ordering guarantees | Priority-based | Partition-based |
| Use case | Task queue | Event streaming |
| Operational overhead | Low | High |
| **Best for** | Simple task distribution | Event sourcing, log aggregation |

---

## When to Choose FastWorker

### ✅ Choose FastWorker if:

1. **You want zero external dependencies**
   - No Redis/RabbitMQ to maintain
   - Simple deployment

2. **You have a Python-only stack**
   - All workers are Python
   - All clients are Python

3. **You need moderate scale**
   - Hundreds to thousands of tasks per minute
   - 1-50 workers

4. **You want fast development iteration**
   - Quick local setup
   - Easy debugging
   - Minimal configuration

5. **You need priority queues**
   - Built-in priority support
   - Simple priority-based routing

6. **You value simplicity**
   - Easy to understand codebase
   - Minimal moving parts

### ❌ Consider alternatives if:

1. **You need extreme scale**
   - Millions of tasks per second
   - Hundreds of workers
   → Use Celery, RabbitMQ, or Kafka

2. **You need task persistence**
   - Tasks must survive crashes
   - Long-term task history
   → Use Celery with backends, RabbitMQ

3. **You have multi-language requirements**
   - Mix of Python, Go, Java, Node.js
   → Use RabbitMQ, NATS, or cloud queues

4. **You need complex workflows**
   - Task chains, dependencies
   - Conditional routing, DAGs
   → Use Celery, Airflow, Temporal, or Prefect

5. **You need exactly-once guarantees**
   - Financial transactions
   - Critical operations
   → Use RabbitMQ, Kafka, or implement idempotency

6. **You need advanced monitoring**
   - Web UI for task inspection
   - Detailed metrics and analytics
   → Use Celery with Flower, or Airflow

7. **You need geo-distribution**
   - Workers across continents
   - Multi-region deployment
   → Use cloud queues or distributed message brokers

---

## Migration Considerations

### Moving FROM FastWorker

**When to migrate:**
- Outgrowing scale limits (>10K tasks/min)
- Need for task persistence
- Requiring multi-language support
- Need for complex workflows

**Migration path:**
1. Implement task persistence layer
2. Gradually migrate high-volume tasks to alternative queue
3. Keep FastWorker for low-volume, simple tasks
4. Eventually fully migrate when alternative is stable

### Moving TO FastWorker

**When to simplify:**
- Over-engineered with Celery for simple use case
- Want to reduce operational overhead
- Pure Python stack
- Moderate task volume

**Migration path:**
1. Start with new tasks on FastWorker
2. Keep existing Celery/RabbitMQ for complex workflows
3. Gradually migrate simple tasks
4. Retire complex infrastructure when ready

---

## Anti-Patterns

### ❌ What NOT to do with FastWorker

#### 1. Don't Use for Critical Financial Transactions

```python
# BAD - No persistence, no exactly-once guarantees
@task
def process_payment(amount, account):
    charge_credit_card(amount)  # Could be lost if crash!
    update_balance(account, amount)
```

**Better:** Use a transactional system with exactly-once guarantees.

#### 2. Don't Submit Massive Tasks

```python
# BAD - Large data in task arguments
@task
def process_huge_file(file_data):  # file_data is 100MB!
    return analyze(file_data)
```

**Better:** Pass file path/URL, load data in worker:

```python
@task
def process_huge_file(file_path):
    with open(file_path) as f:
        data = f.read()
    return analyze(data)
```

#### 3. Don't Use for Long-Term Result Storage

```python
# BAD - Results expire after 1 hour
task_id = await client.delay("generate_report", user_id)
# Come back tomorrow to check...
result = await client.get_task_result(task_id)  # Will be None!
```

**Better:** Store results in your own database.

#### 4. Don't Deploy Across High-Latency Networks

```python
# BAD - Workers in different continents
# Control plane in US, worker in Asia = high latency
```

**Better:** Keep workers close to control plane, or use geo-distributed queue.

#### 5. Don't Rely on Task Ordering

```python
# BAD - Assuming tasks execute in order
await client.delay("task1")
await client.delay("task2")  # Might execute before task1!
```

**Better:** Use task chains/workflows (not built into FastWorker) or explicit dependencies.

---

## Future Considerations

Features currently **not** supported but may be added:

- ⏳ Control plane high availability
- ⏳ Task persistence options
- ⏳ Advanced retry policies
- ⏳ Task workflow support
- ⏳ Web UI for monitoring
- ⏳ Dead letter queues
- ⏳ Scheduled/periodic tasks

These are potential future enhancements, not guarantees.

---

## Summary

### FastWorker is excellent for:
- 🎯 Simple background task processing in web applications
- 🎯 Python-only stacks
- 🎯 Development and testing environments
- 🎯 Small to medium scale (1K-10K tasks/min)
- 🎯 Zero-dependency deployments
- 🎯 Priority-based task processing
- 🎯 Rapid prototyping and iteration

### FastWorker is NOT suitable for:
- ❌ Extreme scale (100K+ tasks/min)
- ❌ Multi-language environments
- ❌ Mission-critical systems requiring persistence
- ❌ Complex workflow orchestration
- ❌ Geo-distributed deployments
- ❌ Exactly-once delivery guarantees
- ❌ Long-term task storage

### The Right Tool for the Right Job

FastWorker fills a specific niche: **lightweight, zero-dependency task queues for Python applications at moderate scale**. It's designed to be simple, fast to deploy, and easy to understand.

If your requirements exceed these boundaries, consider more feature-rich alternatives like Celery, RabbitMQ, or cloud-based queues. There's no shame in choosing the right tool for your specific needs.

---

## See Also

- [Architecture Overview](index.md) - Understanding FastWorker's design
- [Configuration](configuration.md) - Tuning for your use case
- [API Reference](api.md) - Complete API documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [FastAPI Integration](fastapi.md) - Web application integration
