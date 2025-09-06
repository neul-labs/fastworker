# FastQueue - Ready for PyPI Release

## Project Summary

FastQueue is a brokerless task queue system built using nng patterns. It provides a drop-in async replacement for Celery without requiring a broker.

## Key Features

1. **Truly Brokerless**: No central broker required, eliminating single points of failure
2. **Automatic Service Discovery**: Workers and clients automatically discover each other
3. **Priority Queues**: Four priority levels (CRITICAL, HIGH, NORMAL, LOW)
4. **Load Balancing**: Automatic distribution of tasks across available workers
5. **Reliable Delivery**: Built-in retry mechanisms with exponential backoff
6. **FastAPI Integration**: Seamless integration with FastAPI applications
7. **NNG Patterns**: Leverages nng's native patterns for performance and reliability

## Directory Structure

```
fastqueue/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── MANIFEST.in
├── docs/
│   ├── index.md
│   ├── api.md
│   ├── workers.md
│   ├── clients.md
│   ├── fastapi.md
│   └── nng_patterns.md
├── fastqueue/
│   ├── __init__.py
│   ├── cli.py
│   ├── main.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   └── nng_patterns.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── models.py
│   │   └── serializer.py
│   ├── workers/
│   │   ├── __init__.py
│   │   └── worker.py
│   ├── clients/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── examples/
│   │   ├── __init__.py
│   │   └── tasks.py
│   └── tests/
│       ├── __init__.py
│       └── test_fastqueue.py
└── start_example.sh
```

## PyPI Release Instructions

1. **Update Version**: Update the version in `pyproject.toml`
   ```toml
   [tool.poetry]
   name = "fastqueue"
   version = "0.1.0"  # Update this
   ```

2. **Build the Package**:
   ```bash
   poetry build
   ```

3. **Publish to PyPI**:
   ```bash
   poetry publish
   ```

   Or for Test PyPI first:
   ```bash
   poetry publish -r testpypi
   ```

## Testing the Package

1. **Run Tests**:
   ```bash
   poetry run pytest
   ```

2. **Test CLI**:
   ```bash
   poetry run fastqueue --help
   ```

3. **Test Installation**:
   ```bash
   pip install dist/fastqueue-0.1.0.tar.gz
   ```

## Documentation

All documentation is included in the `docs/` directory and is also available in the README.md.

## Examples

Example usage is provided in `fastqueue/examples/` and in the documentation.

## Requirements

- Python 3.12+
- pynng >= 0.8.1
- pydantic >= 2.0.0

## License

MIT License - see LICENSE file for details.