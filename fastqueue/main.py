"""Main module for FastQueue."""
from fastqueue.tasks.registry import task, task_registry
from fastqueue.workers.worker import Worker
from fastqueue.clients.client import Client

__all__ = ["task", "task_registry", "Worker", "Client"]