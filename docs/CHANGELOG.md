# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-09-05

### Added

- Initial release of FastQueue
- Brokerless task queue using nng patterns
- Support for task prioritization (CRITICAL, HIGH, NORMAL, LOW)
- Automatic service discovery with no manual configuration
- Load balancing across multiple workers
- Reliable delivery with retry mechanisms
- CLI interface for starting workers and submitting tasks
- FastAPI integration
- Comprehensive documentation
- Example applications and usage patterns

### Features

- **Surveyor/Respondent Pattern**: For load balancing tasks to workers
- **Bus Pattern**: For automatic service discovery
- **Req/Rep Pattern**: For synchronous communication
- **Task Decorator**: Simple decorator-based task registration
- **Priority Queues**: Four priority levels with automatic routing
- **Built-in Retry**: Exponential backoff retry mechanisms
- **Timeout Handling**: Configurable timeouts for task execution
- **Multiple Serialization**: Support for JSON and Pickle serialization

### Implementation Details

- Fully asynchronous implementation using asyncio
- Built-in service discovery eliminates need for separate processes
- Workers automatically discover each other on the network
- Clients automatically discover available workers
- Graceful shutdown handling for both workers and clients
- Comprehensive error handling and logging
- Pydantic models for type safety and validation