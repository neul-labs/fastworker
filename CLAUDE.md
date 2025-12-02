# CLAUDE.md - FastWorker Project Guide

This document helps Claude Code and other AI assistants understand the FastWorker codebase structure, architecture, and development practices.

## Project Overview

**FastWorker** is a brokerless task queue for Python applications with automatic worker discovery, priority handling, and built-in management GUI. It eliminates the need for external message brokers like Redis or RabbitMQ by using a control plane architecture with NNG (nanomsg-next-generation) for messaging.

**Target Use Case**: Moderate-scale Python applications (1K-10K tasks/min)
**Language**: Python 3.12+
**Key Dependencies**: pynng, pydantic
**Frontend**: Vue.js 3, TailwindCSS (for management GUI)
**License**: MIT

## Architecture

### Control Plane Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ TCP (via control plane)
       │
┌──────▼──────────────┐
│  Control Plane      │ (Coordinator + Task Processor)
│  - Task distribution│
│  - Result caching   │
│  - Worker registry  │
└──────┬──────────────┘
       │
   ┌───┴───┬────────┐
   │       │        │
┌──▼───┐ ┌▼────┐ ┌─▼────┐
│Sub-  │ │Sub- │ │Sub-  │
│worker│ │worker│ │worker│
└──────┘ └─────┘ └──────┘
```

**Key Components**:
1. **Control Plane Worker**: Central coordinator that manages task distribution and also processes tasks
2. **Subworkers**: Additional workers that register with control plane for load distribution
3. **Clients**: Connect to control plane for task submission and result retrieval
4. **Discovery Service**: Enables workers to find the control plane automatically
5. **Management GUI**: Built-in web dashboard for monitoring (Vue.js + TailwindCSS)

## Directory Structure

```
fastworker/
├── fastworker/              # Main package
│   ├── __init__.py         # Package exports (task, Client, etc.)
│   ├── cli.py              # CLI commands (control-plane, subworker, submit, etc.)
│   ├── main.py             # Main entry point
│   │
│   ├── clients/            # Client implementations
│   │   ├── client.py       # Main client for task submission
│   │   └── discovery.py    # Discovery service client
│   │
│   ├── workers/            # Worker implementations
│   │   ├── control_plane.py # Control plane worker
│   │   └── subworker.py    # Subworker implementation
│   │
│   ├── tasks/              # Task management
│   │   ├── models.py       # Task models (Task, TaskResult, TaskPriority)
│   │   ├── registry.py     # Task registry and decorator
│   │   └── serializer.py   # Task serialization
│   │
│   ├── patterns/           # NNG communication patterns
│   │   └── nng_patterns.py # REQ/REP, PUSH/PULL patterns
│   │
│   ├── telemetry/          # Optional OpenTelemetry integration
│   │   ├── tracer.py       # Distributed tracing
│   │   └── metrics.py      # Metrics collection
│   │
│   ├── gui/                # Management GUI
│   │   ├── __init__.py     # Package exports
│   │   ├── server.py       # HTTP server with REST API
│   │   ├── static/         # Pre-built Vue.js frontend
│   │   └── frontend/       # Vue.js source code
│   │       ├── src/        # Vue components
│   │       ├── package.json
│   │       └── build.sh    # Build script
│   │
│   └── examples/           # Example code
│       ├── tasks.py        # Example task definitions
│       ├── fastapi_example.py  # FastAPI integration example
│       └── callback_example.py # Task completion callbacks
│
├── tests/                  # Test suite
├── docs/                   # Documentation
│   ├── index.md           # Documentation index
│   ├── api.md             # API reference
│   ├── gui.md             # Management GUI guide
│   ├── limitations.md     # Scope and limitations
│   ├── fastapi.md         # FastAPI integration guide
│   └── telemetry.md       # OpenTelemetry guide
│
├── pyproject.toml         # uv/PEP 621 configuration
├── README.md              # User-facing documentation
└── CONTRIBUTING.md        # Contribution guidelines
```

## Key Files and Their Purposes

### Core Files

- **`fastworker/__init__.py`**: Package exports - defines public API (`task`, `Client`, `TaskPriority`)
- **`fastworker/cli.py`**: CLI commands implementation (typer-based)
- **`fastworker/tasks/registry.py`**: Task decorator and registration system
- **`fastworker/tasks/models.py`**: Core data models (Task, TaskResult, TaskPriority, TaskStatus)
- **`fastworker/workers/control_plane.py`**: Control plane implementation with result caching and GUI integration
- **`fastworker/workers/subworker.py`**: Subworker that registers with control plane
- **`fastworker/clients/client.py`**: Client for task submission (blocking and non-blocking)

### Management GUI

- **`fastworker/gui/server.py`**: HTTP server that serves the GUI and provides REST API
- **`fastworker/gui/static/`**: Pre-built Vue.js frontend (HTML, CSS, JS)
- **`fastworker/gui/frontend/`**: Vue.js source code for customization
- Default address: http://127.0.0.1:8080

### Communication

- **`fastworker/patterns/nng_patterns.py`**: NNG socket patterns (REQ/REP, PUSH/PULL)
- Uses TCP sockets for inter-process communication
- Default addresses: tcp://127.0.0.1:5555 (control plane), tcp://127.0.0.1:5550 (discovery)

## Key Concepts

### 1. Task Definition

Tasks are defined using the `@task` decorator:

```python
from fastworker import task

@task
def add(x: int, y: int) -> int:
    return x + y
```

### 2. Task Priorities

Four priority levels (defined in `fastworker/tasks/models.py`):
- `CRITICAL` (0) - Highest priority
- `HIGH` (1)
- `NORMAL` (2) - Default
- `LOW` (3) - Lowest priority

### 3. Result Caching

The control plane maintains an LRU cache for task results:
- Default size: 10,000 results
- Default TTL: 1 hour (3600 seconds)
- Automatic cleanup every 60 seconds
- Configurable via CLI flags

### 4. Worker Discovery

- Control plane broadcasts its address on discovery port (5550)
- Subworkers and clients discover control plane automatically
- No manual configuration needed for basic setup

### 5. Management GUI

The control plane includes a built-in web dashboard:
- **Enabled by default** on http://127.0.0.1:8080
- **Real-time monitoring** with auto-refresh every 5 seconds
- **REST API** for programmatic access (`/api/status`, `/api/workers`, `/api/tasks`, etc.)
- **Vue.js + TailwindCSS** frontend (pre-built, no Node.js required at runtime)

Configuration:
```bash
# Custom host/port
fastworker control-plane --gui-host 0.0.0.0 --gui-port 9000 --task-modules mytasks

# Disable GUI
fastworker control-plane --no-gui --task-modules mytasks
```

Environment variables:
- `FASTWORKER_GUI_ENABLED` - Enable/disable GUI (default: `true`)
- `FASTWORKER_GUI_HOST` - GUI server host (default: `127.0.0.1`)
- `FASTWORKER_GUI_PORT` - GUI server port (default: `8080`)

## Development Workflow

### Setup

```bash
# Install dependencies
uv sync

# Or install with dev dependencies explicitly
uv sync --group dev
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=fastworker

# Run specific test file
uv run pytest tests/test_client.py
```

### Code Formatting

```bash
# Format code
uv run black .

# Check formatting
uv run black . --check

# Lint code
uv run flake8
```

### Local Testing

```bash
# Terminal 1: Start control plane
fastworker control-plane --worker-id control-plane --task-modules mytasks

# Terminal 2: Start subworker
fastworker subworker --worker-id subworker1 --control-plane-address tcp://127.0.0.1:5555 --task-modules mytasks

# Terminal 3: Submit tasks
fastworker submit --task-name add --args 5 3
```

## Common Development Tasks

### Adding a New Task Type

1. Define task in a module (e.g., `mytasks.py`)
2. Use `@task` decorator from `fastworker`
3. Load module with `--task-modules` flag
4. Task registry automatically discovers decorated functions

### Modifying Communication Patterns

- Edit `fastworker/patterns/nng_patterns.py`
- Be careful with socket lifecycle management
- Ensure proper error handling and cleanup

### Adding New CLI Commands

1. Edit `fastworker/cli.py`
2. Add new function with `@app.command()` decorator
3. Entry point is defined in `pyproject.toml` under `[project.scripts]`

### Extending Telemetry

- Modify `fastworker/telemetry/tracer.py` for tracing
- Modify `fastworker/telemetry/metrics.py` for metrics
- OpenTelemetry integration is optional

### Modifying the Management GUI

**Backend (Python):**
- Edit `fastworker/gui/server.py` for REST API changes
- Add new endpoints in `ManagementRequestHandler`

**Frontend (Vue.js):**
```bash
cd fastworker/gui/frontend

# Install dependencies
npm install

# Development mode with hot reload
npm run dev

# Build for production (outputs to ../static/)
npm run build
# or use the build script
./build.sh
```

**Key frontend files:**
- `src/App.vue` - Main application component
- `src/components/` - UI components (StatsCard, WorkersPanel, etc.)
- `tailwind.config.js` - TailwindCSS configuration

## Testing Strategy

### Test Structure

```
tests/
├── test_client.py          # Client functionality tests
├── test_tasks.py           # Task decorator and registry tests
├── test_workers.py         # Worker behavior tests
└── test_serializer.py      # Serialization tests
```

### Testing Guidelines

- Use pytest fixtures for setup/teardown
- Test async code with `pytest-asyncio`
- Mock NNG sockets for unit tests
- Integration tests should start actual workers
- Clean up resources (sockets, threads) in teardown

## Important Patterns and Conventions

### 1. Socket Management

Always close NNG sockets properly:
```python
socket = pynng.Rep0()
try:
    socket.listen(address)
    # ... use socket ...
finally:
    socket.close()
```

### 2. Async/Await

- Client methods are async (`await client.submit_task()`)
- Worker methods use asyncio for concurrency
- Use `asyncio.run()` for top-level execution

### 3. Error Handling

- Tasks can specify retry logic
- Workers handle task failures gracefully
- Clients timeout if control plane unreachable

### 4. Configuration

- CLI uses Typer for command-line parsing
- Configuration passed via command-line flags
- No config files - keep it simple

## Common Issues and Solutions

### Issue: Workers can't find control plane

**Solution**: Check that:
- Control plane is running first
- Discovery address matches (default: tcp://127.0.0.1:5550)
- No firewall blocking ports
- Same machine or network reachable

### Issue: Tasks not found

**Solution**: Verify:
- Task modules loaded with `--task-modules`
- Task decorated with `@task`
- Module importable (check PYTHONPATH)
- No import errors in task module

### Issue: Results not cached

**Solution**: Check:
- Using control plane (not standalone worker)
- Result cache size not zero
- TTL not expired
- Task completed successfully

## Building and Publishing

```bash
# Build package
uv build

# Publish to PyPI (requires credentials)
uv publish

# Version bumping (edit pyproject.toml manually)
# Change version = "0.1.1" in [project] section
```

## When Modifying This Codebase

### Keep in Mind

1. **Simplicity**: FastWorker aims to be simple and zero-config
2. **No External Dependencies**: Don't add Redis, database, or broker requirements
3. **Python-Only**: Stay within Python ecosystem
4. **Moderate Scale**: Optimize for 1K-10K tasks/min, not millions
5. **Documentation**: Update docs/ when adding features

### Before Making Changes

1. Read `docs/limitations.md` to understand scope
2. Check if feature aligns with project goals
3. Consider impact on simplicity and zero-config nature
4. Write tests for new functionality
5. Update relevant documentation

### Code Review Checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Code formatted (`uv run black .`)
- [ ] No new external dependencies unless critical
- [ ] Documentation updated (README.md, docs/)
- [ ] Examples still work
- [ ] Backward compatible or version bumped appropriately

## Resources

- **GitHub**: https://github.com/neul-labs/fastworker
- **PyPI**: https://pypi.org/project/fastworker/
- **Documentation**: docs/index.md
- **Issues**: https://github.com/neul-labs/fastworker/issues

## Contact

For questions or contributions, see CONTRIBUTING.md or open an issue on GitHub.

---

**Last Updated**: 2025-12-02
**Version**: 0.1.1
