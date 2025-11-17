# Troubleshooting Guide

This guide covers common issues you might encounter when using FastQueue and how to resolve them.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Task Execution Problems](#task-execution-problems)
- [Performance Issues](#performance-issues)
- [Configuration Problems](#configuration-problems)
- [Serialization Errors](#serialization-errors)
- [Port and Network Issues](#port-and-network-issues)
- [Debugging Tips](#debugging-tips)

---

## Connection Issues

### Workers Not Discovering Each Other

**Symptoms:**
- Client shows "No workers available"
- `len(client.workers)` returns 0
- Tasks timeout or fail immediately

**Causes and Solutions:**

1. **Different Discovery Addresses**

   All components must use the same discovery address.

   ```python
   # WRONG - Different discovery addresses
   # Control plane
   worker = ControlPlaneWorker(discovery_address="tcp://127.0.0.1:5550")

   # Client
   client = Client(discovery_address="tcp://127.0.0.1:5551")  # Different!

   # CORRECT - Same discovery address
   worker = ControlPlaneWorker(discovery_address="tcp://127.0.0.1:5550")
   client = Client(discovery_address="tcp://127.0.0.1:5550")
   ```

2. **Control Plane Not Started**

   Start the control plane before starting clients:

   ```bash
   # Terminal 1: Start control plane first
   fastqueue control-plane --task-modules tasks

   # Terminal 2: Then start your client application
   python app.py
   ```

3. **Firewall Blocking Connections**

   Check if your firewall is blocking the ports:

   ```bash
   # Check if port is open
   netstat -an | grep 5550

   # Test connection
   telnet 127.0.0.1 5550
   ```

4. **Network Interface Issues**

   For distributed deployments, use `0.0.0.0` instead of `127.0.0.1`:

   ```bash
   # Listen on all interfaces
   export FASTQUEUE_DISCOVERY_ADDRESS=tcp://0.0.0.0:5550
   export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555
   ```

### Client Timeout Errors

**Symptoms:**
- `asyncio.TimeoutError` when submitting tasks
- Tasks take too long to complete

**Solutions:**

1. **Increase Client Timeout**

   ```python
   # Increase timeout for long-running tasks
   client = Client(timeout=120)  # 2 minutes

   # Or via environment variable
   export FASTQUEUE_TIMEOUT=120
   ```

2. **Check Worker Health**

   ```python
   # Check if workers are available
   print(f"Available workers: {len(client.workers)}")
   print(f"Worker addresses: {list(client.workers)}")
   ```

3. **Verify Task Execution Time**

   Make sure your tasks complete within the timeout period:

   ```python
   @task
   def long_task():
       time.sleep(200)  # Will timeout with default 30s timeout
       return "done"
   ```

---

## Task Execution Problems

### Tasks Not Being Executed

**Symptoms:**
- Tasks submitted but never complete
- No results returned
- Task status remains PENDING

**Causes and Solutions:**

1. **Task Not Registered**

   Ensure tasks are imported and loaded:

   ```bash
   # Specify task modules when starting workers
   fastqueue control-plane --task-modules mytasks

   # Or import explicitly
   from mytasks import my_task  # Registers via @task decorator
   ```

2. **Task Name Mismatch**

   ```python
   # Task definition
   @task
   def process_data(data):
       return data

   # WRONG - Using wrong name
   await client.delay("processData", data)  # Wrong!

   # CORRECT - Use exact function name
   await client.delay("process_data", data)  # Correct
   ```

3. **No Workers Processing That Priority**

   ```python
   # Check if workers are available for the priority
   result = await client.delay("my_task", priority=TaskPriority.CRITICAL)

   # If no workers on critical queue, task won't be processed
   ```

### Task Execution Errors

**Symptoms:**
- Tasks fail with errors
- Result status is FAILURE
- Error messages in logs

**Solutions:**

1. **Check Task Implementation**

   ```python
   @task
   def problematic_task(x):
       return x / 0  # Will fail!

   # Add error handling
   @task
   def safe_task(x):
       try:
           return x / 0
       except ZeroDivisionError as e:
           logger.error(f"Division error: {e}")
           raise  # Re-raise to mark task as failed
   ```

2. **Check Task Arguments**

   ```python
   @task
   def process_data(x: int, y: int) -> int:
       return x + y

   # WRONG - Incorrect argument types
   await client.delay("process_data", "1", "2")  # Strings!

   # CORRECT
   await client.delay("process_data", 1, 2)
   ```

3. **Enable Debug Logging**

   ```python
   import logging

   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger("fastqueue")
   logger.setLevel(logging.DEBUG)
   ```

### Tasks Stuck in Queue

**Symptoms:**
- Tasks remain in queue and don't get processed
- Control plane shows tasks queued but not distributed

**Solutions:**

1. **Check Subworker Status**

   ```python
   # In control plane
   status = control_plane.get_subworker_status()
   print(status)
   ```

2. **Verify Subworker Connection**

   Ensure subworkers are properly connected to control plane:

   ```bash
   # Subworker must specify control plane address
   fastqueue subworker \
     --worker-id sw1 \
     --control-plane-address tcp://127.0.0.1:5555 \
     --task-modules tasks
   ```

3. **Check Priority Queue**

   High-priority tasks are processed before low-priority tasks:

   ```python
   # Low priority tasks may be delayed if many high priority tasks exist
   await client.delay("task", priority=TaskPriority.LOW)
   ```

---

## Performance Issues

### Slow Task Processing

**Symptoms:**
- Tasks take longer than expected
- Low throughput

**Solutions:**

1. **Add More Subworkers**

   ```bash
   # Start additional subworkers
   fastqueue subworker --worker-id sw2 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5565 --task-modules tasks
   fastqueue subworker --worker-id sw3 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5569 --task-modules tasks
   ```

2. **Optimize Task Implementation**

   ```python
   # BAD - Synchronous I/O in async task
   @task
   async def slow_task():
       time.sleep(10)  # Blocks!
       return "done"

   # GOOD - Use async I/O
   @task
   async def fast_task():
       await asyncio.sleep(10)  # Non-blocking
       return "done"
   ```

3. **Use Appropriate Priority**

   ```python
   # Critical tasks processed first
   await client.delay("urgent_task", priority=TaskPriority.CRITICAL)
   await client.delay("normal_task", priority=TaskPriority.NORMAL)
   ```

### High Memory Usage

**Symptoms:**
- Workers consuming excessive memory
- Out of memory errors

**Solutions:**

1. **Adjust Result Cache Size**

   ```bash
   # Reduce cache size
   export FASTQUEUE_RESULT_CACHE_SIZE=5000
   export FASTQUEUE_RESULT_CACHE_TTL=1800  # 30 minutes
   ```

2. **Process Large Data in Chunks**

   ```python
   # BAD - Loading all data at once
   @task
   def process_large_file(file_path):
       data = open(file_path).read()  # Loads entire file!
       return process(data)

   # GOOD - Process in chunks
   @task
   def process_large_file(file_path):
       with open(file_path, 'rb') as f:
           for chunk in iter(lambda: f.read(4096), b''):
               process(chunk)
   ```

3. **Clear Task Results**

   ```python
   # Client stores results in memory
   # Clear old results periodically
   client.task_results.clear()
   ```

---

## Configuration Problems

### Environment Variables Not Being Applied

**Symptoms:**
- Configuration changes not taking effect
- Using default values instead of env vars

**Solutions:**

1. **Verify Environment Variables Are Set**

   ```bash
   # Check if variable is set
   echo $FASTQUEUE_DISCOVERY_ADDRESS

   # Export if needed
   export FASTQUEUE_DISCOVERY_ADDRESS=tcp://127.0.0.1:5550
   ```

2. **Load .env Files**

   ```python
   from dotenv import load_dotenv

   # Load before creating client
   load_dotenv()

   client = Client()  # Now uses .env variables
   ```

3. **Check Priority Order**

   Explicit arguments override environment variables:

   ```python
   # FASTQUEUE_TIMEOUT=60 is set

   # This uses 60 from env var
   client = Client()

   # This uses 120 (explicit argument has priority)
   client = Client(timeout=120)
   ```

### Port Already in Use

**Symptoms:**
- "Address already in use" errors
- Workers fail to start

**Solutions:**

1. **Check What's Using the Port**

   ```bash
   # Find process using port
   lsof -i :5555
   netstat -an | grep 5555

   # Kill the process if needed
   kill -9 <PID>
   ```

2. **Use Different Ports**

   ```bash
   # Control plane
   export FASTQUEUE_BASE_ADDRESS=tcp://127.0.0.1:6555

   # Subworker 1
   export FASTQUEUE_BASE_ADDRESS=tcp://127.0.0.1:6561

   # Subworker 2
   export FASTQUEUE_BASE_ADDRESS=tcp://127.0.0.1:6565
   ```

3. **Ensure Clean Shutdown**

   ```python
   # Properly stop workers to release ports
   worker.stop()
   client.stop()
   ```

---

## Serialization Errors

### Pickle Errors

**Symptoms:**
- `PicklingError` or `UnpicklingError`
- "Can't pickle <object>" errors

**Solutions:**

1. **Use JSON Instead**

   ```bash
   export FASTQUEUE_SERIALIZATION_FORMAT=JSON
   ```

2. **Make Objects Picklable**

   ```python
   # BAD - Lambda functions can't be pickled
   @task
   def bad_task():
       func = lambda x: x + 1  # Not picklable!
       return func

   # GOOD - Use regular functions
   @task
   def good_task():
       def func(x):
           return x + 1
       return func
   ```

3. **Avoid Unpicklable Types**

   Avoid returning:
   - Lambda functions
   - Generator objects
   - Thread locks
   - Open file handles
   - Database connections

### JSON Serialization Errors

**Symptoms:**
- "Object of type X is not JSON serializable"
- Datetime or custom object errors

**Solutions:**

1. **Convert to JSON-Compatible Types**

   ```python
   from datetime import datetime

   # BAD - datetime not JSON serializable
   @task
   def bad_task():
       return {"timestamp": datetime.now()}

   # GOOD - Convert to string
   @task
   def good_task():
       return {"timestamp": datetime.now().isoformat()}
   ```

2. **Use Dataclasses or Pydantic**

   ```python
   from pydantic import BaseModel
   from datetime import datetime

   class Result(BaseModel):
       timestamp: datetime
       value: int

   @task
   def my_task():
       result = Result(timestamp=datetime.now(), value=42)
       return result.dict()  # Converts to dict
   ```

---

## Port and Network Issues

### Cannot Connect to Remote Workers

**Symptoms:**
- Local workers work but remote workers don't
- Connection refused errors

**Solutions:**

1. **Use Correct Network Interface**

   ```bash
   # Listen on all interfaces (0.0.0.0, not 127.0.0.1)
   export FASTQUEUE_BASE_ADDRESS=tcp://0.0.0.0:5555
   ```

2. **Check Firewall Rules**

   ```bash
   # Allow incoming connections on required ports
   sudo ufw allow 5550:5560/tcp

   # Or for specific IP
   sudo ufw allow from 10.0.0.0/24 to any port 5550:5560
   ```

3. **Verify Network Connectivity**

   ```bash
   # Test connection from client to worker
   nc -zv worker-host 5555
   telnet worker-host 5555
   ```

### Docker Networking Issues

**Symptoms:**
- Workers can't connect in Docker
- Connection timeouts between containers

**Solutions:**

1. **Use Docker Network**

   ```yaml
   # docker-compose.yml
   version: '3.8'

   services:
     control-plane:
       environment:
         FASTQUEUE_BASE_ADDRESS: tcp://0.0.0.0:5555
       ports:
         - "5550-5560:5550-5560"

     subworker:
       environment:
         FASTQUEUE_CONTROL_PLANE_ADDRESS: tcp://control-plane:5555
   ```

2. **Use Host Network Mode** (Linux only)

   ```yaml
   services:
     control-plane:
       network_mode: host
   ```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

# Enable debug logging for FastQueue
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger
logger = logging.getLogger("fastqueue")
logger.setLevel(logging.DEBUG)
```

### Monitor Worker Status

```python
# Check worker discovery
print(f"Discovered workers: {len(client.workers)}")
print(f"Worker addresses: {list(client.workers)}")

# Check control plane status
status = control_plane.get_subworker_status()
print(f"Subworkers: {status}")
```

### Test Connection Manually

```python
# Test if you can connect to control plane
import pynng

try:
    socket = pynng.Req0(dial="tcp://127.0.0.1:5555")
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Inspect Task Registry

```python
from fastqueue.tasks.registry import task_registry

# List all registered tasks
print("Registered tasks:")
for task_name in task_registry.list_tasks():
    print(f"  - {task_name}")
```

### Check Task Result

```python
# Submit task and check result
task_id = await client.delay("my_task", arg1, arg2)
print(f"Task ID: {task_id}")

# Wait a bit
await asyncio.sleep(2)

# Check result
result = await client.get_task_result(task_id)
if result:
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")
else:
    print("Result not found")
```

### Profile Task Performance

```python
import time

@task
def slow_task():
    start = time.time()
    # Your task code
    time.sleep(1)
    duration = time.time() - start
    print(f"Task took {duration:.2f}s")
    return "done"
```

---

## Common Error Messages

### "No workers available"

**Cause:** Client cannot find any workers.

**Solution:**
1. Start the control plane
2. Verify discovery addresses match
3. Wait a few seconds for discovery

### "Address already in use"

**Cause:** Port is already in use by another process.

**Solution:**
1. Use different ports
2. Stop conflicting process
3. Ensure clean shutdown of previous workers

### "Task 'task_name' not found"

**Cause:** Task not registered with worker.

**Solution:**
1. Ensure task module is imported
2. Use `--task-modules` flag when starting workers
3. Verify task name matches function name exactly

### "Connection refused"

**Cause:** Cannot connect to specified address.

**Solution:**
1. Verify worker is running
2. Check address and port are correct
3. Check firewall settings

### "Object of type X is not JSON serializable"

**Cause:** Trying to serialize non-JSON-compatible object.

**Solution:**
1. Convert to JSON-compatible types (str, int, dict, list)
2. Use `.isoformat()` for datetime objects
3. Convert custom objects to dictionaries

---

## Getting Help

If you're still experiencing issues:

1. **Check the Documentation**
   - [API Reference](api.md)
   - [Configuration Guide](configuration.md)
   - [Client Guide](clients.md)

2. **Enable Debug Logging**
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Report Issues**
   - GitHub Issues: https://github.com/dipankar/fastqueue/issues
   - Include: FastQueue version, Python version, error messages, logs

4. **Provide Minimal Reproduction**
   - Create minimal example that reproduces the issue
   - Include configuration and environment details
   - Share relevant logs with DEBUG level enabled
