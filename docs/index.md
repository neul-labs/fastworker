# FastQueue Documentation

A brokerless task queue for Python applications with automatic worker discovery and priority handling.

## Overview

FastQueue eliminates the complexity of traditional task queues by removing the need for message brokers like Redis or RabbitMQ. Workers communicate directly using NNG (Next Generation Networking) patterns, providing:

- **Fault Tolerance** - No single point of failure
- **Auto-Discovery** - Workers find each other automatically
- **Priority Queues** - Critical, high, normal, and low priority tasks
- **Load Balancing** - Tasks distributed across available workers

## Quick Start

1. **Install FastQueue**
   ```bash
   pip install fastqueue
   ```

2. **Define Tasks**
   ```python
   # tasks.py
   from fastqueue import task

   @task
   def process_data(data: dict):
       return {"processed": data}
   ```

3. **Start Workers**
   ```bash
   fastqueue worker --worker-id worker1 --task-modules tasks
   ```

4. **Submit Tasks**
   ```python
   from fastqueue import Client

   client = Client()
   await client.start()
   result = await client.delay("process_data", {"key": "value"})
   client.stop()
   ```

## Documentation Sections

### Core Components
- [**API Reference**](api.md) - Complete API documentation
- [**Workers**](workers.md) - Worker configuration and management
- [**Clients**](clients.md) - Client usage and configuration

### Integration Guides
- [**FastAPI Integration**](fastapi.md) - Web application integration
- [**NNG Patterns**](nng_patterns.md) - Network communication details

## Architecture

FastQueue uses a distributed architecture where:

1. **Workers** register themselves and listen for tasks
2. **Clients** discover workers and submit tasks
3. **Tasks** are distributed based on priority and worker availability
4. **Results** are returned directly to the client

No central coordinator or message broker is required.

## Key Features

- **Zero Configuration** - Works out of the box
- **High Performance** - Direct peer-to-peer communication
- **Scalable** - Add workers dynamically
- **Reliable** - Built-in retries and error handling
- **Python Native** - Type hints and async/await support

## Requirements

- Python 3.12+
- pynng (network communication)
- pydantic (data validation)

## Support

- [GitHub Issues](https://github.com/dipankar/fastqueue/issues) - Bug reports and feature requests
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines