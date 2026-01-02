# Configuration

FastWorker supports configuration through both code and environment variables. Environment variables provide a convenient way to configure your application without hardcoding values.

## Environment Variables

All FastWorker components can be configured using environment variables with the `FASTWORKER_` prefix.

### Client Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTWORKER_DISCOVERY_ADDRESS` | Discovery address for finding workers | `tcp://127.0.0.1:5550` |
| `FASTWORKER_SERIALIZATION_FORMAT` | Serialization format (`JSON` or `PICKLE`) | `JSON` |
| `FASTWORKER_TIMEOUT` | Task timeout in seconds | `30` |
| `FASTWORKER_RETRIES` | Number of retries for failed submissions | `3` |

```bash
export FASTWORKER_DISCOVERY_ADDRESS="tcp://10.0.0.1:5550"
export FASTWORKER_TIMEOUT="60"
export FASTWORKER_RETRIES="5"
```

### Control Plane Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTWORKER_WORKER_ID` | Unique identifier for the control plane | `control-plane` |
| `FASTWORKER_BASE_ADDRESS` | Base address for task processing | `tcp://127.0.0.1:5555` |
| `FASTWORKER_DISCOVERY_ADDRESS` | Service discovery address | `tcp://127.0.0.1:5550` |
| `FASTWORKER_SUBWORKER_PORT` | Port for subworker management | `5560` |
| `FASTWORKER_RESULT_CACHE_SIZE` | Maximum number of cached results | `10000` |
| `FASTWORKER_RESULT_CACHE_TTL` | Cache TTL in seconds | `3600` (1 hour) |

### GUI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTWORKER_GUI_ENABLED` | `true` | Enable/disable the GUI |
| `FASTWORKER_GUI_HOST` | `127.0.0.1` | GUI server host address |
| `FASTWORKER_GUI_PORT` | `8080` | GUI server port |

### Subworker Configuration

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `FASTWORKER_WORKER_ID` | Unique identifier for the subworker | **(required)** |
| `FASTWORKER_CONTROL_PLANE_ADDRESS` | Address of the control plane | **(required)** |
| `FASTWORKER_BASE_ADDRESS` | Base address for this subworker | `tcp://127.0.0.1:5555` |

## Configuration Patterns

### Development Environment

```bash
# .env.development
FASTWORKER_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
FASTWORKER_BASE_ADDRESS=tcp://127.0.0.1:5555
FASTWORKER_TIMEOUT=30
FASTWORKER_RETRIES=3
```

### Production Environment

```bash
# .env.production
FASTWORKER_DISCOVERY_ADDRESS=tcp://0.0.0.0:5550
FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5555
FASTWORKER_TIMEOUT=60
FASTWORKER_RETRIES=5
FASTWORKER_RESULT_CACHE_SIZE=50000
FASTWORKER_RESULT_CACHE_TTL=7200
```

### Docker Compose

```yaml
version: '3.8'

services:
  control-plane:
    image: myapp:latest
    environment:
      FASTWORKER_WORKER_ID: control-plane
      FASTWORKER_BASE_ADDRESS: tcp://0.0.0.0:5555
      FASTWORKER_DISCOVERY_ADDRESS: tcp://0.0.0.0:5550
      FASTWORKER_RESULT_CACHE_SIZE: 50000
    command: ["fastworker", "control-plane", "--task-modules", "tasks"]
    ports:
      - "5550-5560:5550-5560"
      - "8080:8080"

  subworker:
    image: myapp:latest
    environment:
      FASTWORKER_WORKER_ID: subworker-1
      FASTWORKER_CONTROL_PLANE_ADDRESS: tcp://control-plane:5555
      FASTWORKER_BASE_ADDRESS: tcp://0.0.0.0:5561
    command: ["fastworker", "subworker", "--task-modules", "tasks"]
    depends_on:
      - control-plane
```

## Priority Order

Configuration follows this priority order (highest to lowest):

1. **Explicit arguments** passed to constructors
2. **Environment variables**
3. **Default values**

```python
# Environment variable set: FASTWORKER_TIMEOUT=60

# Case 1: Explicit argument (highest priority)
client = Client(timeout=120)  # Uses 120

# Case 2: Environment variable
client = Client()  # Uses 60 from env var

# Case 3: If no env var was set
# client = Client()  # Would use default 30
```

## Serialization Formats

### JSON (Default)

- **Pros**: Human-readable, language-agnostic, secure
- **Cons**: Limited type support, slower than Pickle

```bash
export FASTWORKER_SERIALIZATION_FORMAT=JSON
```

### Pickle

- **Pros**: Fast, supports complex Python objects
- **Cons**: Python-only, security risks with untrusted data

```bash
export FASTWORKER_SERIALIZATION_FORMAT=PICKLE
```

!!! warning
    Only use Pickle in trusted environments. Never use Pickle with untrusted task data.

## Port Allocation

### Control Plane Ports

If `FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5555`:

- **5555**: Critical priority tasks
- **5556**: High priority tasks
- **5557**: Normal priority tasks
- **5558**: Low priority tasks
- **5559**: Result query endpoint
- **5560**: Subworker management

### Subworker Ports

Each subworker needs its own port range:

```bash
# Subworker 1: ports 5561-5564
FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5561

# Subworker 2: ports 5565-5568
FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5565

# Subworker 3: ports 5569-5572
FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5569
```

## Best Practices

### 1. Use Environment Variables for Deployment

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
FASTWORKER_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
FASTWORKER_BASE_ADDRESS=tcp://127.0.0.1:5555
FASTWORKER_TIMEOUT=30
FASTWORKER_RETRIES=3
```

### 3. Use python-dotenv

```python
from dotenv import load_dotenv
from fastworker import Client

# Load environment variables from .env file
load_dotenv()

client = Client()  # Uses variables from .env
```
