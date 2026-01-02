# OpenTelemetry Integration

FastWorker includes optional OpenTelemetry integration for distributed tracing and metrics collection.

## Installation

```bash
pip install fastworker[telemetry]
```

Or install dependencies separately:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

## Configuration

Enable telemetry using environment variables:

```bash
# Enable telemetry
export FASTWORKER_TELEMETRY_ENABLED=true

# Configure OpenTelemetry
export OTEL_SERVICE_NAME=my-fastworker-service
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTWORKER_TELEMETRY_ENABLED` | Enable/disable telemetry | `false` |
| `OTEL_SERVICE_NAME` | Service name in traces | `fastworker` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `OTEL_TRACES_SAMPLER` | Trace sampling strategy | `always_on` |

## What Gets Instrumented

### Traces (Spans)

- **`client.submit_task`** - Task submission
- **`worker.execute_task`** - Task execution with attributes like task ID, name, priority, worker ID

### Metrics

#### Counters

- **`fastworker.tasks.submitted`** - Tasks submitted
- **`fastworker.tasks.completed`** - Tasks completed successfully
- **`fastworker.tasks.failed`** - Tasks failed

#### Histograms

- **`fastworker.tasks.duration`** - Task execution duration

#### Gauges

- **`fastworker.workers.active`** - Active workers
- **`fastworker.queue.size`** - Queue size by priority

## Basic Usage

```python
import os

os.environ["FASTWORKER_TELEMETRY_ENABLED"] = "true"
os.environ["OTEL_SERVICE_NAME"] = "my-service"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://jaeger:4317"

from fastworker import Client

# Telemetry automatically enabled
client = Client()
await client.start()

# This task submission will be traced
await client.delay("process_data", data, priority="high")
```

## Custom Task Tracing

```python
from fastworker import task
from fastworker.telemetry import trace_task

@task
@trace_task
def process_data(data: dict) -> dict:
    """Process data with tracing."""
    return {"processed": data}
```

## Manual Instrumentation

```python
from fastworker.telemetry import trace_operation, record_task_metric

# Custom span
with trace_operation("custom_operation", attributes={"key": "value"}):
    # Your code here
    pass

# Custom metrics
record_task_metric("submitted", "my_task", priority="high")
record_task_metric("completed", "my_task", worker_id="worker1", duration_ms=150.5)
```

## Integration Examples

### Jaeger

```bash
docker run -d --name jaeger \
  -p 4317:4317 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

```bash
export FASTWORKER_TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=fastworker-app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

View traces at: http://localhost:16686

### Grafana + Tempo

```yaml
# docker-compose.yml
services:
  tempo:
    image: grafana/tempo:latest
    ports:
      - "4317:4317"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

### Prometheus Metrics

Example queries:

```promql
# Task submission rate
rate(fastworker_tasks_submitted_total[5m])

# Task failure rate
rate(fastworker_tasks_failed_total[5m])

# Average task duration
rate(fastworker_tasks_duration_sum[5m]) / rate(fastworker_tasks_duration_count[5m])

# P95 task duration
histogram_quantile(0.95, rate(fastworker_tasks_duration_bucket[5m]))
```

## Docker Compose with Telemetry

```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"

  control-plane:
    build: .
    command: fastworker control-plane --task-modules tasks
    environment:
      FASTWORKER_TELEMETRY_ENABLED: "true"
      OTEL_SERVICE_NAME: "fastworker-control-plane"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
    depends_on:
      - otel-collector

  worker:
    build: .
    command: fastworker subworker --task-modules tasks
    environment:
      FASTWORKER_TELEMETRY_ENABLED: "true"
      OTEL_SERVICE_NAME: "fastworker-worker"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
    depends_on:
      - control-plane
```

## Performance Considerations

### Overhead

- **Traces**: ~0.1-0.5ms per span
- **Metrics**: ~0.01ms per recording
- **Memory**: ~10-50MB depending on batch size

### Sampling

For high-throughput systems:

```bash
# Sample 10% of traces
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
```

## Best Practices

1. **Use Consistent Service Names**

```bash
export OTEL_SERVICE_NAME=myapp-control-plane
export OTEL_SERVICE_NAME=myapp-worker
```

2. **Add Custom Attributes**

```python
with trace_operation("custom_op", attributes={
    "user.id": user_id,
    "environment": "production"
}):
    pass
```

3. **Set Up Alerts**

```yaml
# Prometheus alert rules
groups:
  - name: fastworker
    rules:
      - alert: HighTaskFailureRate
        expr: rate(fastworker_tasks_failed_total[5m]) > 0.1
        annotations:
          summary: "High task failure rate"
```

4. **Use Sampling in Production**

```bash
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.05  # Sample 5%
```
