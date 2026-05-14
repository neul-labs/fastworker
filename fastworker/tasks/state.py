"""Task state machine — formal lifecycle for FastWorker tasks."""

from fastworker.tasks.models import TaskStatus
from fastworker.utils.state_machine import StateMachine

# Allowed transitions for the task state machine
_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.QUEUED, TaskStatus.SCHEDULED},
    TaskStatus.QUEUED: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
    TaskStatus.SCHEDULED: {TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.ASSIGNED: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.CANCELLED},
    TaskStatus.FAILURE: {TaskStatus.RETRYING},
    TaskStatus.RETRYING: {TaskStatus.QUEUED},
    # Terminal states — no outgoing transitions
    TaskStatus.SUCCESS: set(),
    TaskStatus.CANCELLED: set(),
}


class TaskStateMachine(StateMachine[TaskStatus]):
    """Per-task state machine enforcing the formal task lifecycle."""

    def __init__(self):
        super().__init__(TaskStatus.PENDING, _TASK_TRANSITIONS)

    async def submit(self, scheduled: bool = False) -> bool:
        target = TaskStatus.SCHEDULED if scheduled else TaskStatus.QUEUED
        return await self.transition(target)

    async def assign(self) -> bool:
        return await self.transition(TaskStatus.ASSIGNED)

    async def start(self) -> bool:
        return await self.transition(TaskStatus.RUNNING)

    async def complete(self) -> bool:
        return await self.transition(TaskStatus.SUCCESS)

    async def fail(self) -> bool:
        return await self.transition(TaskStatus.FAILURE)

    async def cancel(self) -> bool:
        return await self.transition(TaskStatus.CANCELLED)

    async def prepare_retry(self) -> bool:
        return await self.transition(TaskStatus.RETRYING)

    async def enqueue_from_retry(self) -> bool:
        return await self.transition(TaskStatus.QUEUED)

    async def enqueue_from_scheduled(self) -> bool:
        return await self.transition(TaskStatus.QUEUED)

    @property
    def is_terminal(self) -> bool:
        return self.state in (TaskStatus.SUCCESS, TaskStatus.CANCELLED) or (
            self.state == TaskStatus.FAILURE and not self.can_transition(TaskStatus.RETRYING)
        )
