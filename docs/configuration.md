# Configuration Guide

FastQueue supports configuration through both code and environment variables. Environment variables provide a convenient way to configure your application without hardcoding values, making it easy to deploy across different environments.

## Environment Variables

All FastQueue components (Client, ControlPlaneWorker, SubWorker) can be configured using environment variables with the `FASTQUEUE_` prefix.

### Client Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTQUEUE_DISCOVERY_ADDRESS` | Discovery address for finding workers | `tcp://127.0.0.1:5550` |
| `FASTQUEUE_SERIALIZATION_FORMAT` | Serialization format (`JSON` or `PICKLE`) | `JSON` |
| `FASTQUEUE_TIMEOUT` | Task timeout in seconds | `30` |
| `FASTQUEUE_RETRIES` | Number of retries for failed submissions | `3` |

#### Example

```bash
export FASTQUEUE_DISCOVERY_ADDRESS="tcp://10.0.0.1:5550"
export FASTQUEUE_TIMEOUT="60"
export FASTQUEUE_RETRIES="5"
```

```python
from fastqueue import Client

# Client will automatically use environment variables
client = Client()
await client.start()

# Or override specific values
client = Client(timeout=120)  # Uses env vars for other settings
```

### Control Plane Worker Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTQUEUE_WORKER_ID` | Unique identifier for the control plane | `control-plane` |
| `FASTQUEUE_BASE_ADDRESS` | Base address for task processing | `tcp://127.0.0.1:5555` |
| `FASTQUEUE_DISCOVERY_ADDRESS` | Service discovery address | `tcp://127.0.0.1:5550` |
| `FASTQUEUE_SERIALIZATION_FORMAT` | Serialization format (`JSON` or `PICKLE`) | `JSON` |
| `FASTQUEUE_SUBWORKER_PORT` | Port for subworker management | `5560` |
| `FASTQUEUE_RESULT_CACHE_SIZE` | Maximum number of cached results | `10000` |
| `FASTQUEUE_RESULT_CACHE_TTL` | Cache TTL in seconds | `3600` (1 hour) |

#### Example

```bash
export FASTQUEUE_WORKER_ID="control-plane-prod"
export FASTQUEUE_BASE_ADDRESS="tcp://0.0.0.0:5555"
export FASTQUEUE_RESULT_CACHE_SIZE="50000"
export FASTQUEUE_RESULT_CACHE_TTL="7200"
```

```python
from fastqueue.workers.control_plane import ControlPlaneWorker

# Worker will automatically use environment variables
worker = ControlPlaneWorker()
worker.start()

# Or override specific values
worker = ControlPlaneWorker(result_cache_max_size=100000)
```

### Subworker Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTQUEUE_WORKER_ID` | Unique identifier for the subworker | **(required)** |
| `FASTQUEUE_CONTROL_PLANE_ADDRESS` | Address of the control plane | **(required)** |
| `FASTQUEUE_BASE_ADDRESS` | Base address for this subworker | `tcp://127.0.0.1:5555` |
| `FASTQUEUE_DISCOVERY_ADDRESS` | Service discovery address | `tcp://127.0.0.1:5550` |
| `FASTQUEUE_SERIALIZATION_FORMAT` | Serialization format (`JSON` or `PICKLE`) | `JSON` |

**Note:** `FASTQUEUE_WORKER_ID` and `FASTQUEUE_CONTROL_PLANE_ADDRESS` are required for subworkers.

#### Example

```bash
export FASTQUEUE_WORKER_ID="subworker-1"
export FASTQUEUE_CONTROL_PLANE_ADDRESS="tcp://10.0.0.1:5555"
export FASTQUEUE_BASE_ADDRESS="tcp://0.0.0.0:5561"
```

```python
from fastqueue.workers.subworker import SubWorker

# Worker will automatically use environment variables
worker = SubWorker()
worker.start()

# Or provide values explicitly
worker = SubWorker(
    worker_id="subworker-2",
    control_plane_address="tcp://10.0.0.1:5555"
)
```

## Configuration Patterns

### Development Environment

For local development:

```bash
# .env.development
FASTQUEUE_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
FASTQUEUE_BASE_ADDRESS=tcp://127.0.0.1:5555
FASTQUEUE_TIMEOUT=30
FASTQUEUE_RETRIES=3
FASTQUEUE_SERIALIZATION_FORMAT=JSON
```

### Production Environment

For production deployment:

```bash
# .env.production
FASTQUEUE_DISCOVERY_ADDRESS=tcp://0.0.0.0:5550
FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555
FASTQUEUE_TIMEOUT=60
FASTQUEUE_RETRIES=5
FASTQUEUE_RESULT_CACHE_SIZE=50000
FASTQUEUE_RESULT_CACHE_TTL=7200
FASTQUEUE_SERIALIZATION_FORMAT=JSON
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install fastqueue

# Environment variables
ENV FASTQUEUE_DISCOVERY_ADDRESS=tcp://0.0.0.0:5550
ENV FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555
ENV FASTQUEUE_RESULT_CACHE_SIZE=50000

CMD ["fastqueue", "control-plane", "--task-modules", "tasks"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  control-plane:
    image: myapp:latest
    environment:
      FASTQUEUE_WORKER_ID: control-plane
      FASTQUEUE_BASE_ADDRESS: tcp://0.0.0.0:5555
      FASTQUEUE_DISCOVERY_ADDRESS: tcp://0.0.0.0:5550
      FASTQUEUE_RESULT_CACHE_SIZE: 50000
      FASTQUEUE_RESULT_CACHE_TTL: 7200
    command: ["fastqueue", "control-plane", "--task-modules", "tasks"]
    ports:
      - "5550-5560:5550-5560"

  subworker-1:
    image: myapp:latest
    environment:
      FASTQUEUE_WORKER_ID: subworker-1
      FASTQUEUE_CONTROL_PLANE_ADDRESS: tcp://control-plane:5555
      FASTQUEUE_BASE_ADDRESS: tcp://0.0.0.0:5561
      FASTQUEUE_DISCOVERY_ADDRESS: tcp://control-plane:5550
    command: ["fastqueue", "subworker", "--task-modules", "tasks"]
    depends_on:
      - control-plane

  subworker-2:
    image: myapp:latest
    environment:
      FASTQUEUE_WORKER_ID: subworker-2
      FASTQUEUE_CONTROL_PLANE_ADDRESS: tcp://control-plane:5555
      FASTQUEUE_BASE_ADDRESS: tcp://0.0.0.0:5565
      FASTQUEUE_DISCOVERY_ADDRESS: tcp://control-plane:5550
    command: ["fastqueue", "subworker", "--task-modules", "tasks"]
    depends_on:
      - control-plane

  app:
    image: myapp:latest
    environment:
      FASTQUEUE_DISCOVERY_ADDRESS: tcp://control-plane:5550
      FASTQUEUE_TIMEOUT: 60
      FASTQUEUE_RETRIES: 5
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    ports:
      - "8000:8000"
    depends_on:
      - control-plane
```

### Kubernetes Deployment

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastqueue-config
data:
  FASTQUEUE_DISCOVERY_ADDRESS: "tcp://control-plane:5550"
  FASTQUEUE_BASE_ADDRESS: "tcp://0.0.0.0:5555"
  FASTQUEUE_TIMEOUT: "60"
  FASTQUEUE_RETRIES: "5"
  FASTQUEUE_RESULT_CACHE_SIZE: "50000"
  FASTQUEUE_RESULT_CACHE_TTL: "7200"
  FASTQUEUE_SERIALIZATION_FORMAT: "JSON"

---
# control-plane-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastqueue-control-plane
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fastqueue-control-plane
  template:
    metadata:
      labels:
        app: fastqueue-control-plane
    spec:
      containers:
      - name: control-plane
        image: myapp:latest
        envFrom:
        - configMapRef:
            name: fastqueue-config
        env:
        - name: FASTQUEUE_WORKER_ID
          value: "control-plane"
        command: ["fastqueue", "control-plane", "--task-modules", "tasks"]
        ports:
        - containerPort: 5550
        - containerPort: 5555
        - containerPort: 5560

---
# subworker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastqueue-subworker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastqueue-subworker
  template:
    metadata:
      labels:
        app: fastqueue-subworker
    spec:
      containers:
      - name: subworker
        image: myapp:latest
        envFrom:
        - configMapRef:
            name: fastqueue-config
        env:
        - name: FASTQUEUE_WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: FASTQUEUE_CONTROL_PLANE_ADDRESS
          value: "tcp://control-plane:5555"
        - name: FASTQUEUE_BASE_ADDRESS
          value: "tcp://0.0.0.0:5561"
        command: ["fastqueue", "subworker", "--task-modules", "tasks"]
```

## Priority: Code vs Environment Variables

Configuration follows this priority order (highest to lowest):

1. **Explicit arguments** passed to constructors
2. **Environment variables**
3. **Default values**

### Example

```python
# Environment variable set
# FASTQUEUE_TIMEOUT=60

# Case 1: Explicit argument (highest priority)
client = Client(timeout=120)  # Uses 120

# Case 2: Environment variable
client = Client()  # Uses 60 from env var

# Case 3: If no env var was set
# client = Client()  # Would use default 30
```

## Serialization Formats

FastQueue supports two serialization formats:

### JSON (Default)

- **Pros**: Human-readable, language-agnostic, secure
- **Cons**: Limited type support, slower than Pickle
- **Use when**: Sharing tasks across languages, security is critical

```bash
export FASTQUEUE_SERIALIZATION_FORMAT=JSON
```

### Pickle

- **Pros**: Fast, supports complex Python objects
- **Cons**: Python-only, security risks with untrusted data
- **Use when**: All Python environment, maximum performance needed

```bash
export FASTQUEUE_SERIALIZATION_FORMAT=PICKLE
```

**Warning:** Only use Pickle in trusted environments. Never use Pickle with untrusted task data.

## Port Allocation

FastQueue uses multiple ports for different priorities and services:

### Control Plane Ports

If `FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555`:

- **5555**: Critical priority tasks
- **5556**: High priority tasks
- **5557**: Normal priority tasks
- **5558**: Low priority tasks
- **5559**: Result query endpoint
- **5560**: Subworker management (or value from `FASTQUEUE_SUBWORKER_PORT`)

### Subworker Ports

Each subworker needs its own port range. If you have 3 subworkers:

```bash
# Subworker 1
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5561

# Subworker 2
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5565

# Subworker 3
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5569
```

Each will use 4 consecutive ports (one per priority level).

## Best Practices

### 1. Use Environment Variables for Deployment

Always use environment variables in production:

```python
# Good - uses environment variables
client = Client()

# Avoid - hardcoded values
client = Client(discovery_address="tcp://10.0.0.1:5550")
```

### 2. Document Your Configuration

Create a `.env.example` file:

```bash
# .env.example
FASTQUEUE_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
FASTQUEUE_BASE_ADDRESS=tcp://127.0.0.1:5555
FASTQUEUE_TIMEOUT=30
FASTQUEUE_RETRIES=3
FASTQUEUE_SERIALIZATION_FORMAT=JSON
FASTQUEUE_RESULT_CACHE_SIZE=10000
FASTQUEUE_RESULT_CACHE_TTL=3600
```

### 3. Use Different Configs per Environment

```bash
# Development
source .env.development

# Staging
source .env.staging

# Production
source .env.production
```

### 4. Validate Configuration

```python
import os

# Validate required variables
required_vars = [
    "FASTQUEUE_WORKER_ID",
    "FASTQUEUE_CONTROL_PLANE_ADDRESS"
]

for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Required environment variable {var} not set")
```

### 5. Use Config Management Tools

Consider using:
- **python-dotenv**: Load .env files
- **pydantic-settings**: Type-safe settings management
- **dynaconf**: Multi-environment configuration

Example with python-dotenv:

```python
from dotenv import load_dotenv
from fastqueue import Client

# Load environment variables from .env file
load_dotenv()

client = Client()  # Uses variables from .env
```

## Troubleshooting

### Configuration Not Being Applied

**Problem:** Environment variables are set but not being used.

**Solution:** Ensure variables are exported and available to the process:

```bash
# Check if variable is set
echo $FASTQUEUE_DISCOVERY_ADDRESS

# Export if not already
export FASTQUEUE_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
```

### Port Conflicts

**Problem:** Address already in use errors.

**Solution:** Ensure each component uses unique ports:

```bash
# Control plane
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555

# Subworker 1
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5561

# Subworker 2
export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5565
```

### Type Conversion Errors

**Problem:** Integer environment variables causing errors.

**Solution:** FastQueue handles conversion automatically, but ensure values are valid:

```bash
# Good
export FASTQUEUE_TIMEOUT=60

# Bad
export FASTQUEUE_TIMEOUT=sixty  # Will cause error
```

## See Also

- [Client Guide](clients.md) - Client usage and configuration
- [Control Plane](control_plane.md) - Control plane architecture
- [Workers](workers.md) - Worker configuration
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
