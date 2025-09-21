# Changelog

All notable changes to FastQueue will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of FastQueue
- Brokerless task queue using NNG patterns
- Automatic worker discovery and service registration
- Priority-based task handling (critical, high, normal, low)
- Built-in retry mechanisms with exponential backoff
- FastAPI integration support
- CLI interface for worker management and task submission
- Comprehensive test suite with 43+ test cases

### Technical Details
- Uses pynng for network communication
- Pydantic models for data validation
- Poetry for dependency management
- Supports Python 3.12+

## [0.1.0] - 2024-09-05

### Added
- Initial alpha release
- Core worker and client functionality
- Basic task registration and execution
- Network communication patterns