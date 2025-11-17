# FastQueue Documentation

A brokerless task queue for Python applications with automatic worker discovery and priority handling.

## Overview

FastQueue eliminates the complexity of traditional task queues by removing the need for message brokers like Redis or RabbitMQ. The system uses a **Control Plane Architecture** where:

- **Control Plane Worker**: Central coordinator that manages subworkers and processes tasks
- **Subworkers**: Additional workers that register with the control plane for load distribution
- **Clients**: Connect to the control plane for task submission

### Key Features

- **Fault Tolerance** - No single point of failure
- **Auto-Discovery** - Workers find each other automatically
- **Priority Queues** - Critical, high, normal, and low priority tasks
- **Load Balancing** - Tasks distributed to least-loaded subworkers
- **Result Caching** - Results cached with expiration and memory limits

## Quick Start

1. **Install FastQueue**
   pip install fastqueue
   
2. **Define Tasks**hon
   # mytasks.py
   from fastqueue import task

   @task
   def process_data(data: dict):
       return {"processed": data}
   3. **Start Control Plane**
   fastqueue control-plane --task-modules mytasks
   4. **Start Subworkers (Optional)**
   fastqueue subworker --worker-id sw1 --control-plane-address tcp://127.0.0.1:5555 --base-address tcp://127.0.0.1:5561 --task-modules mytasks
   5. **Submit Tasks**thon
   from fastqueue import Client

   client = Client()
   await client.start()
   task_id = await client.delay("process_data", {"key": "value"})
   result = await client.get_task_result(task_id)
   client.stop()
   ## Documentation Sections

### Core Components
- [**API Reference**](api.md) - Complete API documentation
- [**Control Plane**](control_plane.md) - Control plane architecture and configuration
- [**Workers**](workers.md) - Worker configuration and management
- [**Clients**](clients.md) - Client usage and configuration

### Integration Guides
- [**FastAPI Integration**](fastapi.md) - Comprehensive FastAPI integration guide
- [**Framework Integration**](frameworks.md) - Flask, Django, Sanic, and other frameworks
- [**NNG Patterns**](nng_patterns.md) - Network communication details

## Architecture

FastQueue uses a **Control Plane Architecture**:

1. **Control Plane Worker** coordinates all task distribution
2. **Subworkers** register with control plane and receive tasks
3. **Clients** connect only to the control plane
4. **Results** are cached in the control plane with expiration

### Benefits

- **Centralized Management**: Single point of coordination
- **Load Balancing**: Automatic distribution to least-loaded workers
- **High Availability**: Control plane processes tasks if subworkers fail
- **Result Persistence**: Results cached and queryable
- **Scalability**: Add subworkers dynamically

## Key Features

- **Zero Configuration** - Works out of the box
- **High Performance** - Direct peer-to-peer communication
- **Scalable** - Add subworkers dynamically
- **Reliable** - Built-in retries and error handling
- **Python Native** - Type hints and async/await support

## Requirements

- Python 3.12+
- pynng (network communication)
- pydantic (data validation)

## Support

- [GitHub Issues](https://github.com/dipankar/fastqueue/issues) - Bug reports and feature requests
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines