# Installation

## Requirements

- **Python 3.12+** - FastWorker requires Python 3.12 or later
- **pip or uv** - Package manager for installation

## Basic Installation

Install FastWorker from PyPI:

=== "pip"

    ```bash
    pip install fastworker
    ```

=== "uv"

    ```bash
    uv add fastworker
    ```

=== "poetry"

    ```bash
    poetry add fastworker
    ```

## Optional Dependencies

### Telemetry Support

For OpenTelemetry integration (distributed tracing and metrics):

```bash
pip install fastworker[telemetry]
```

Or install OpenTelemetry dependencies separately:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

## Verify Installation

After installation, verify FastWorker is working:

```bash
# Check version
fastworker --help

# List available commands
fastworker --help
```

## Development Installation

For contributing to FastWorker:

```bash
# Clone repository
git clone https://github.com/neul-labs/fastworker.git
cd fastworker

# Install with dev dependencies
uv sync

# Run tests
uv run pytest
```

## Dependencies

FastWorker has minimal dependencies:

| Package | Purpose |
|---------|---------|
| `pynng` | Network communication (nanomsg-next-generation) |
| `pydantic` | Data validation and serialization |
| `typer` | Command-line interface |

## What's Next?

- [Quick Start](quickstart.md) - Get your first task queue running
- [Configuration](configuration.md) - Environment variables and settings
