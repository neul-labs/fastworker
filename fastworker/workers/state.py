"""Worker lifecycle state machine."""

from enum import Enum

from fastworker.utils.state_machine import StateMachine


class WorkerState(str, Enum):
    """Worker lifecycle states."""

    INIT = "init"
    STARTING = "starting"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPING = "stopping"
    STOPPED = "stopped"


_WORKER_TRANSITIONS: dict[WorkerState, set[WorkerState]] = {
    WorkerState.INIT: {WorkerState.STARTING},
    WorkerState.STARTING: {WorkerState.RUNNING, WorkerState.STOPPING},
    WorkerState.RUNNING: {WorkerState.DRAINING, WorkerState.STOPPING},
    WorkerState.DRAINING: {WorkerState.STOPPING, WorkerState.RUNNING},
    WorkerState.STOPPING: {WorkerState.STOPPED},
    WorkerState.STOPPED: set(),
}


class WorkerStateMachine(StateMachine[WorkerState]):
    """State machine for worker lifecycle management."""

    def __init__(self):
        super().__init__(WorkerState.INIT, _WORKER_TRANSITIONS)

    async def start(self) -> bool:
        return await self.transition(WorkerState.STARTING)

    async def ready(self) -> bool:
        return await self.transition(WorkerState.RUNNING)

    async def drain(self) -> bool:
        return await self.transition(WorkerState.DRAINING)

    async def resume(self) -> bool:
        return await self.transition(WorkerState.RUNNING)

    async def force_stop(self) -> bool:
        return await self.transition(WorkerState.STOPPING)

    async def complete_stop(self) -> bool:
        return await self.transition(WorkerState.STOPPED)

    async def fail_start(self) -> bool:
        """STARTING → STOPPING on startup failure."""
        return await self.transition(WorkerState.STOPPING)
