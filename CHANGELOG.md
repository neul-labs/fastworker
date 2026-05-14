# Changelog

## [0.3.0] - 2026-05-14

### Added
- **FastAPI Native Integration**: `FastWorker(app)` — one line to wire everything. Auto-registers lifespan, chains with existing lifespans, delegates all Client methods.
- **Periodic/Cron Tasks**: `@task(repeat_interval=60)` and `@task(cron="*/5 * * * *")` for declarative recurring task scheduling.
- Pure Python 5-field cron parser (`*`, `*/N`, ranges, lists, steps) with `cron_next()` and `compute_next_eta()`.
- **Project structure examples**: 4 progressive levels — single file, package, organized, FastAPI integration.
- `fastworker list --tree` CLI command showing task module structure with discovered tasks.
- `fastworker list --list-periodic` CLI flag for periodic task listing.
- **Task middleware hooks**: `@task(before=..., after=...)` on decorator and `task_registry.add_middleware()`.
- `TaskHook` protocol and `TaskContext` class in `fastworker/utils/hooks.py`.
- EventBus subscribe API for external listeners.
- **6 documentation guides**: periodic-tasks, project-structure, why-fastworker, extending, internals, benchmarks.

### Changed
- `TaskRegistry` stores `TaskInfo` dataclass (func, name, module, schedule, before, after) instead of raw Callable.
- Control plane heap extended to 4-tuple `(eta, task_id, task, meta)` for periodic task support.
- Worker `_execute_task` uses `get_task_info()` for hook resolution.
- **README rewritten**: 6 badges, comparison table (Celery/RabbitMQ/SQS), side-by-side code comparison, quick start, GUI screenshot, progressive roadmap.
- `fastworker` package exports `Client` at top level.
- Documentation updated: new nav structure, expanded architecture and FastAPI docs.

### Fixed
- CI disconnected from automatic release tagging — `check-version` job removed.
- CI workflows use `ruff` instead of `black`/`flake8`.
- Removed fragile `lint-frontend` CI job.
- Ruff lint issues resolved across all files (F841, B011, B023, F821).

## [0.2.0] - 2025-12-15

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
