"""FastWorker - A brokerless task queue using nng patterns."""

__version__ = "0.3.0"

from fastworker.clients.client import Client
from fastworker.tasks.registry import task

__all__ = ["task", "Client", "__version__"]
