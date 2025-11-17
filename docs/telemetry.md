# OpenTelemetry Integration

FastQueue includes optional OpenTelemetry integration for distributed tracing and metrics collection, making it production-ready with full observability.

## Installation

Install FastQueue with telemetry support:

```bash
pip install fastqueue[telemetry]
```

Or install OpenTelemetry dependencies separately:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

## Configuration

Enable telemetry using environment variables:

```bash
# Enable telemetry
export FASTQUEUE_TELEMETRY_ENABLED=true

# Configure OpenTelemetry (standard OTEL env vars)
export OTEL_SERVICE_NAME=my-fastqueue-service
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Optional: Configure sampling, headers, etc.
export OTEL_TRACES_SAMPLER=always_on
export OTEL_METRICS_EXPORTER=otlp
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTQUEUE_TELEMETRY_ENABLED` | Enable/disable telemetry | `false` |
| `OTEL_SERVICE_NAME` | Service name in traces/metrics | `fastqueue` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `OTEL_TRACES_SAMPLER` | Trace sampling strategy | `always_on` |
| `OTEL_METRICS_EXPORTER` | Metrics exporter type | `otlp` |

## What Gets Instrumented

### Traces (Spans)

FastQueue automatically creates spans for:

1. **Client Operations**
   - `client.submit_task` - Task submission
   - Includes attributes: task name, priority

2. **Worker Operations**
   - `worker.execute_task` - Task execution
   - Includes attributes: task ID, task name, priority, worker ID
   - Records exceptions and status

3. **Custom Task Tracing**
   - Use `@trace_task` decorator for detailed task tracing

### Metrics

FastQueue emits the following metrics:

#### Counters

- **`fastqueue.tasks.submitted`** - Number of tasks submitted
  - Labels: `task.name`, `task.priority`

- **`fastqueue.tasks.completed`** - Number of successfully completed tasks
  - Labels: `task.name`, `task.priority`, `worker.id`

- **`fastqueue.tasks.failed`** - Number of failed tasks
  - Labels: `task.name`, `task.priority`, `worker.id`

#### Histograms

- **`fastqueue.tasks.duration`** - Task execution duration in milliseconds
  - Labels: `task.name`, `task.priority`, `worker.id`

#### Gauges

- **`fastqueue.workers.active`** - Number of active workers
  - Labels: `worker.id`

- **`fastqueue.queue.size`** - Number of tasks in queue
  - Labels: `worker.id`, `queue.priority`

## Usage Examples

### Basic Setup

```python
# No code changes needed! Just enable via environment variables
import os

os.environ["FASTQUEUE_TELEMETRY_ENABLED"] = "true"
os.environ["OTEL_SERVICE_NAME"] = "my-service"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://jaeger:4317"

from fastqueue import Client

# Telemetry automatically enabled
client = Client()
await client.start()

# This task submission will be traced and metered
await client.delay("process_data", data, priority="high")
```

### Custom Task Tracing

Add detailed tracing to your tasks:

```python
from fastqueue import task
from fastqueue.telemetry import trace_task

@task
@trace_task  # Add detailed task tracing
def process_data(data: dict) -> dict:
    """Process data with tracing."""
    # Your task logic here
    return {"processed": data}

@task
@trace_task
async def async_process_data(data: dict) -> dict:
    """Async task with tracing."""
    # Your async task logic
    return {"processed": data}
```

### Manual Instrumentation

For custom operations:

```python
from fastqueue.telemetry import trace_operation, record_task_metric

# Custom span
with trace_operation("custom_operation", attributes={"key": "value"}):
    # Your code here
    pass

# Custom metrics
record_task_metric("submitted", "my_task", priority="high")
record_task_metric("completed", "my_task", worker_id="worker1", duration_ms=150.5)
record_task_metric("failed", "my_task", worker_id="worker1")
```

## Integration with Observability Platforms

### Jaeger

Run Jaeger all-in-one:

```bash
docker run -d --name jaeger \
  -p 4317:4317 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

Configure FastQueue:

```bash
export FASTQUEUE_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastqueue-app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

View traces at: http://localhost:16686

### Grafana + Tempo

```yaml
# docker-compose.yml
version: '3.8'

services:
  tempo:
    image: grafana/tempo:latest
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "3200:3200"  # Tempo query

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
```

Configure FastQueue:

```bash
export FASTQUEUE_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastqueue-app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
```

### Prometheus + Grafana

For metrics visualization:

```yaml
# docker-compose.yml
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "8889:8889"  # Prometheus exporter

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

OTEL Collector config:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"

  logging:
    loglevel: debug

service:
  pipelines:
    metrics:
      receivers: [otlp]
      exporters: [prometheus, logging]
    traces:
      receivers: [otlp]
      exporters: [logging]
```

Prometheus config:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

### Datadog

```bash
export FASTQUEUE_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastqueue-app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://datadog-agent:4317
export DD_API_KEY=your_api_key
```

### New Relic

```bash
export FASTQUEUE_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastqueue-app
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.nr-data.net:4317
export NEW_RELIC_API_KEY=your_api_key
```

### Honeycomb

```bash
export FASTQUEUE_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastqueue-app
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io:443
export HONEYCOMB_API_KEY=your_api_key
```

## Metrics Dashboard

### Grafana Dashboard Example

Here's a sample Prometheus query for key metrics:

**Task Submission Rate:**
```promql
rate(fastqueue_tasks_submitted_total[5m])
```

**Task Completion Rate by Priority:**
```promql
rate(fastqueue_tasks_completed_total[5m]) by (task_priority)
```

**Task Failure Rate:**
```promql
rate(fastqueue_tasks_failed_total[5m])
```

**Average Task Duration:**
```promql
rate(fastqueue_tasks_duration_sum[5m]) / rate(fastqueue_tasks_duration_count[5m])
```

**P95 Task Duration:**
```promql
histogram_quantile(0.95, rate(fastqueue_tasks_duration_bucket[5m]))
```

**Active Workers:**
```promql
fastqueue_workers_active
```

**Queue Size by Priority:**
```promql
fastqueue_queue_size by (queue_priority)
```

## Trace Examples

### Successful Task Execution

```
Span: client.submit_task
├─ task.name: process_data
├─ task.priority: high
└─ duration: 2ms

Span: worker.execute_task
├─ task.id: 123e4567-e89b-12d3-a456-426614174000
├─ task.name: process_data
├─ task.priority: high
├─ worker.id: worker1
└─ duration: 150ms
```

### Failed Task Execution

```
Span: worker.execute_task [ERROR]
├─ task.id: 123e4567-e89b-12d3-a456-426614174000
├─ task.name: process_data
├─ worker.id: worker1
├─ status: ERROR
├─ exception.type: ValueError
└─ exception.message: Invalid data format
```

## Production Deployment

### Docker Compose with Telemetry

```yaml
# docker-compose.yml
version: '3.8'

services:
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"

  # FastQueue App
  app:
    build: .
    environment:
      FASTQUEUE_TELEMETRY_ENABLED: "true"
      OTEL_SERVICE_NAME: "my-fastqueue-app"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
    depends_on:
      - otel-collector
      - control-plane

  # FastQueue Control Plane
  control-plane:
    build: .
    command: fastqueue control-plane --task-modules tasks
    environment:
      FASTQUEUE_TELEMETRY_ENABLED: "true"
      OTEL_SERVICE_NAME: "fastqueue-control-plane"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
    depends_on:
      - otel-collector

  # FastQueue Workers
  worker:
    build: .
    command: fastqueue subworker --task-modules tasks
    environment:
      FASTQUEUE_TELEMETRY_ENABLED: "true"
      OTEL_SERVICE_NAME: "fastqueue-worker"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
      FASTQUEUE_CONTROL_PLANE_ADDRESS: "tcp://control-plane:5555"
    depends_on:
      - control-plane
      - otel-collector
    deploy:
      replicas: 3
```

### Kubernetes with Telemetry

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastqueue-telemetry-config
data:
  FASTQUEUE_TELEMETRY_ENABLED: "true"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastqueue-worker
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: worker
        image: myapp:latest
        envFrom:
        - configMapRef:
            name: fastqueue-telemetry-config
        env:
        - name: OTEL_SERVICE_NAME
          value: "fastqueue-worker"
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: FASTQUEUE_WORKER_ID
          value: "$(POD_NAME)"
```

## Performance Considerations

### Overhead

OpenTelemetry adds minimal overhead:

- **Traces**: ~0.1-0.5ms per span
- **Metrics**: ~0.01ms per metric recording
- **Memory**: ~10-50MB depending on batch size

### Sampling

For high-throughput systems, use sampling:

```bash
# Sample 10% of traces
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
```

### Batching

Configure batch size for better performance:

```python
# In custom OTEL configuration
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,
    max_export_batch_size=512,
    schedule_delay_millis=5000
)
```

## Troubleshooting

### Telemetry Not Working

**Check if enabled:**
```python
import os
print(os.getenv("FASTQUEUE_TELEMETRY_ENABLED"))  # Should be "true"
```

**Check dependencies:**
```bash
pip list | grep opentelemetry
```

**Check logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Look for "OpenTelemetry tracer initialized" message
```

### No Spans in Jaeger/Tempo

**Verify collector endpoint:**
```bash
curl -v http://localhost:4317
```

**Check exporter configuration:**
```bash
echo $OTEL_EXPORTER_OTLP_ENDPOINT
```

### Metrics Not Appearing

**Verify metrics exporter:**
```bash
echo $OTEL_METRICS_EXPORTER  # Should be "otlp"
```

**Check collector receives metrics:**
```bash
# Enable debug logging in collector
```

## Best Practices

### 1. Use Consistent Service Names

```bash
# Application
export OTEL_SERVICE_NAME=myapp-api

# Control Plane
export OTEL_SERVICE_NAME=myapp-control-plane

# Workers
export OTEL_SERVICE_NAME=myapp-worker
```

### 2. Add Custom Attributes

```python
from fastqueue.telemetry import trace_operation

with trace_operation("custom_op", attributes={
    "user.id": user_id,
    "tenant.id": tenant_id,
    "environment": "production"
}):
    # Your code
    pass
```

### 3. Monitor Key Metrics

- Task submission rate
- Task completion rate
- Task failure rate
- Task duration (P50, P95, P99)
- Active worker count
- Queue size

### 4. Set Up Alerts

```yaml
# Prometheus alert rules
groups:
  - name: fastqueue
    rules:
      - alert: HighTaskFailureRate
        expr: rate(fastqueue_tasks_failed_total[5m]) > 0.1
        annotations:
          summary: "High task failure rate"

      - alert: LongTaskDuration
        expr: histogram_quantile(0.95, rate(fastqueue_tasks_duration_bucket[5m])) > 5000
        annotations:
          summary: "Task P95 duration > 5s"

      - alert: NoActiveWorkers
        expr: fastqueue_workers_active == 0
        annotations:
          summary: "No active workers"
```

### 5. Use Sampling in Production

For very high-throughput systems:

```bash
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.05  # Sample 5%
```

## See Also

- [Configuration Guide](configuration.md) - Environment variable configuration
- [Troubleshooting](troubleshooting.md) - Common issues
- [API Reference](api.md) - Complete API documentation
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/) - Official OTEL docs
