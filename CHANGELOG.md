# Changelog

## [0.2.0] - Unreleased

### Added
- Formal state machines for task lifecycle, worker lifecycle, subworker registry, and client connections
- Task cancellation support (CLI + API)
- Scheduled/delayed tasks with ETA and countdown
- Worker concurrency via `asyncio.Semaphore` with `--concurrency` CLI flag
- Batch task submission in single NNG message
- SSE real-time updates for management GUI
- GUI authentication via `FASTWORKER_GUI_API_KEY` env var
- GUI dark mode toggle with persistent preference
- `POST /api/tasks/{id}/cancel` and `POST /api/tasks/{id}/retry` endpoints
- Generic `StateMachine` utility in `fastworker.utils`
- EventBus for pub/sub state transition events

### Changed
- `Task` model rewritten with Pydantic v2 `model_dump()` and `default_factory`
- Worker lifecycle managed by `WorkerStateMachine` (replaces `self.running` bool)
- Control plane uses decoupled recv/process to avoid serial bottleneck
- Replaced `black`/`flake8` with `ruff` for linting and formatting
- CORS origins configurable via `FASTWORKER_GUI_CORS_ORIGIN` env var

### Fixed
- `SecurityWarning` → `RuntimeWarning` in serializer PICKLE path (was `NameError`)
- `MANIFEST.in` references to non-existent `fastqueue` directory
- Hardcoded paths in integration test
- `delay()` return handling in integration test

## [0.1.1] - 2025-12-02

### Added
- Initial release with brokerless task queue
- Control plane architecture with NNG messaging
- Built-in management GUI (Vue.js + TailwindCSS)
- Priority-based task processing
- Result caching with LRU eviction
- Optional OpenTelemetry integration
