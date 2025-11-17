"""Main module for FastWorker."""
from fastworker.tasks.registry import task, task_registry
from fastworker.workers.worker import Worker
from fastworker.clients.client import Client

__all__ = ["task", "task_registry", "Worker", "Client"]