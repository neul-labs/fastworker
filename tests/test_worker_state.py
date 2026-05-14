"""Tests for WorkerStateMachine — full worker lifecycle."""

import pytest
from fastworker.workers.state import WorkerStateMachine, WorkerState


@pytest.fixture
def wsm():
    return WorkerStateMachine()


def test_initial_state(wsm):
    assert wsm.state == WorkerState.INIT


@pytest.mark.asyncio
async def test_full_lifecycle(wsm):
    assert await wsm.start()
    assert wsm.state == WorkerState.STARTING

    assert await wsm.ready()
    assert wsm.state == WorkerState.RUNNING

    assert await wsm.drain()
    assert wsm.state == WorkerState.DRAINING

    assert await wsm.force_stop()
    assert wsm.state == WorkerState.STOPPING

    assert await wsm.complete_stop()
    assert wsm.state == WorkerState.STOPPED


@pytest.mark.asyncio
async def test_startup_failure(wsm):
    await wsm.start()
    assert await wsm.fail_start()
    assert wsm.state == WorkerState.STOPPING


@pytest.mark.asyncio
async def test_direct_force_stop_from_running(wsm):
    await wsm.start()
    await wsm.ready()
    assert await wsm.force_stop()
    assert wsm.state == WorkerState.STOPPING


@pytest.mark.asyncio
async def test_cannot_ready_from_init(wsm):
    assert not await wsm.ready()
    assert wsm.state == WorkerState.INIT


@pytest.mark.asyncio
async def test_cannot_drain_from_init(wsm):
    assert not await wsm.drain()
    assert wsm.state == WorkerState.INIT


@pytest.mark.asyncio
async def test_cannot_start_twice(wsm):
    await wsm.start()
    assert not await wsm.start()
    assert wsm.state == WorkerState.STARTING


@pytest.mark.asyncio
async def test_cannot_complete_stop_before_force_stop(wsm):
    assert not await wsm.complete_stop()
    assert wsm.state == WorkerState.INIT


@pytest.mark.asyncio
async def test_terminal_stopped_is_immutable(wsm):
    await wsm.start()
    await wsm.ready()
    await wsm.force_stop()
    await wsm.complete_stop()
    assert wsm.state == WorkerState.STOPPED
    assert not await wsm.start()
    assert not await wsm.ready()
    assert not await wsm.drain()
