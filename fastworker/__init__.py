"""FastWorker - A brokerless task queue using nng patterns."""

__version__ = "0.1.0"

from fastworker.tasks.registry import task

__all__ = ["task", "__version__"]
