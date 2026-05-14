"""Main module for FastWorker."""

from fastworker.clients.client import Client
from fastworker.tasks.registry import task, task_registry
from fastworker.workers.worker import Worker

__all__ = ["task", "task_registry", "Worker", "Client"]
