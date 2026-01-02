# Troubleshooting

Common issues and solutions when using FastWorker.

## Connection Issues

### Workers Not Discovering Each Other

**Symptoms:**

- Client shows "No workers available"
- Tasks timeout or fail immediately

**Solutions:**

1. **Same Discovery Address** - All components must use the same discovery address:

```python
# Control plane
worker = ControlPlaneWorker(discovery_address="tcp://127.0.0.1:5550")

# Client - must match!
client = Client(discovery_address="tcp://127.0.0.1:5550")
```

2. **Start Control Plane First**:

```bash
# Terminal 1: Start control plane first
fastworker control-plane --task-modules tasks

# Terminal 2: Then start client application
python app.py
```

3. **Check Firewall**:

```bash
netstat -an | grep 5550
telnet 127.0.0.1 5550
```

### Client Timeout Errors

**Solutions:**

1. **Increase Timeout**:

```python
client = Client(timeout=120)  # 2 minutes
```

2. **Check Worker Health**:

```python
print(f"Available workers: {len(client.workers)}")
```

---

## Task Execution Problems

### Tasks Not Being Executed

**Solutions:**

1. **Verify Task Registration**:

```bash
# Specify task modules
fastworker control-plane --task-modules mytasks
```

2. **Check Task Name**:

```python
# Task definition
@task
def process_data(data):
    return data

# Use exact function name
await client.delay("process_data", data)  # Correct
await client.delay("processData", data)   # Wrong!
```

3. **Check Task Registry**:

```python
from fastworker.tasks.registry import task_registry

for task_name in task_registry.list_tasks():
    print(f"  - {task_name}")
```

### Task Execution Errors

**Solutions:**

1. **Add Error Handling**:

```python
@task
def safe_task(x):
    try:
        return x / 0
    except ZeroDivisionError as e:
        logger.error(f"Error: {e}")
        raise
```

2. **Enable Debug Logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Configuration Problems

### Environment Variables Not Applied

**Solutions:**

1. **Verify Variables Are Set**:

```bash
echo $FASTWORKER_DISCOVERY_ADDRESS
export FASTWORKER_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
```

2. **Load .env Files**:

```python
from dotenv import load_dotenv
load_dotenv()

client = Client()  # Now uses .env variables
```

### Port Already in Use

**Solutions:**

1. **Find Process Using Port**:

```bash
lsof -i :5555
kill -9 <PID>
```

2. **Use Different Ports**:

```bash
export FASTWORKER_BASE_ADDRESS=tcp://127.0.0.1:6555
```

3. **Ensure Clean Shutdown**:

```python
worker.stop()
client.stop()
```

---

## Serialization Errors

### JSON Serialization Errors

**Symptoms:**

- "Object of type X is not JSON serializable"

**Solutions:**

```python
from datetime import datetime

# Bad - datetime not JSON serializable
@task
def bad_task():
    return {"timestamp": datetime.now()}

# Good - convert to string
@task
def good_task():
    return {"timestamp": datetime.now().isoformat()}
```

### Pickle Errors

**Symptoms:**

- `PicklingError` or `UnpicklingError`

**Solutions:**

1. **Use JSON Instead**:

```bash
export FASTWORKER_SERIALIZATION_FORMAT=JSON
```

2. **Avoid Unpicklable Types** (lambdas, file handles, database connections)

---

## Network Issues

### Cannot Connect to Remote Workers

**Solutions:**

1. **Bind to All Interfaces**:

```bash
export FASTWORKER_BASE_ADDRESS=tcp://0.0.0.0:5555
```

2. **Check Firewall**:

```bash
sudo ufw allow 5550:5560/tcp
```

3. **Verify Connectivity**:

```bash
nc -zv worker-host 5555
```

### Docker Networking Issues

**Solutions:**

1. **Use Docker Network**:

```yaml
services:
  control-plane:
    environment:
      FASTWORKER_BASE_ADDRESS: tcp://0.0.0.0:5555

  subworker:
    environment:
      FASTWORKER_CONTROL_PLANE_ADDRESS: tcp://control-plane:5555
```

---

## Performance Issues

### Slow Task Processing

**Solutions:**

1. **Add More Subworkers**:

```bash
fastworker subworker --worker-id sw2 \
  --control-plane-address tcp://127.0.0.1:5555 \
  --base-address tcp://127.0.0.1:5565 \
  --task-modules tasks
```

2. **Use Async I/O**:

```python
# Bad - blocks
@task
async def slow_task():
    time.sleep(10)

# Good - non-blocking
@task
async def fast_task():
    await asyncio.sleep(10)
```

### High Memory Usage

**Solutions:**

1. **Reduce Cache Size**:

```bash
export FASTWORKER_RESULT_CACHE_SIZE=5000
export FASTWORKER_RESULT_CACHE_TTL=1800
```

2. **Process Data in Chunks**:

```python
# Bad
@task
def process_file(file_path):
    data = open(file_path).read()  # Loads entire file
    return process(data)

# Good
@task
def process_file(file_path):
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            process(chunk)
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No workers available" | Client can't find workers | Start control plane, verify discovery addresses |
| "Address already in use" | Port in use | Use different port or stop conflicting process |
| "Task 'name' not found" | Task not registered | Use `--task-modules` flag |
| "Connection refused" | Cannot connect | Verify worker is running, check firewall |
| "Not JSON serializable" | Non-JSON type in result | Convert to JSON-compatible types |

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Test Connection

```python
import pynng

try:
    socket = pynng.Req0(dial="tcp://127.0.0.1:5555")
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Check Task Result

```python
task_id = await client.delay("my_task", arg1, arg2)
await asyncio.sleep(2)

result = await client.get_task_result(task_id)
if result:
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")
```

---

## Getting Help

1. **Check Documentation** - [API Reference](api.md), [Configuration](../getting-started/configuration.md)
2. **Enable Debug Logging**
3. **Report Issues** - [GitHub Issues](https://github.com/neul-labs/fastworker/issues)

When reporting issues, include:

- FastWorker version
- Python version
- Error messages
- Logs with DEBUG level enabled
