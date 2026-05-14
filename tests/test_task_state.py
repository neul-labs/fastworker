"""Tests for TaskStateMachine — full task lifecycle."""

import pytest

from fastworker.tasks.models import TaskStatus
from fastworker.tasks.state import TaskStateMachine


@pytest.fixture
def tsm():
    return TaskStateMachine()


def test_initial_state(tsm):
    assert tsm.state == TaskStatus.PENDING


# --- valid transitions ---

@pytest.mark.asyncio
async def test_submit_to_queued(tsm):
    assert await tsm.submit(scheduled=False)
    assert tsm.state == TaskStatus.QUEUED


@pytest.mark.asyncio
async def test_submit_scheduled(tsm):
    assert await tsm.submit(scheduled=True)
    assert tsm.state == TaskStatus.SCHEDULED


@pytest.mark.asyncio
async def test_full_success_path(tsm):
    assert await tsm.submit(scheduled=False)
    assert await tsm.assign()
    assert await tsm.start()
    assert await tsm.complete()
    assert tsm.state == TaskStatus.SUCCESS
    assert tsm.is_terminal


@pytest.mark.asyncio
async def test_full_failure_retry_path(tsm):
    assert await tsm.submit(scheduled=False)
    assert await tsm.assign()
    assert await tsm.start()
    assert await tsm.fail()
    assert tsm.state == TaskStatus.FAILURE
    assert await tsm.prepare_retry()
    assert tsm.state == TaskStatus.RETRYING
    assert await tsm.enqueue_from_retry()
    assert tsm.state == TaskStatus.QUEUED


@pytest.mark.asyncio
async def test_cancel_from_queued(tsm):
    await tsm.submit(scheduled=False)
    assert await tsm.cancel()
    assert tsm.state == TaskStatus.CANCELLED
    assert tsm.is_terminal


@pytest.mark.asyncio
async def test_cancel_from_scheduled(tsm):
    await tsm.submit(scheduled=True)
    assert await tsm.cancel()
    assert tsm.state == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_from_assigned(tsm):
    await tsm.submit(scheduled=False)
    await tsm.assign()
    assert await tsm.cancel()
    assert tsm.state == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_from_running(tsm):
    await tsm.submit(scheduled=False)
    await tsm.assign()
    await tsm.start()
    assert await tsm.cancel()
    assert tsm.state == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_scheduled_enqueues(tsm):
    await tsm.submit(scheduled=True)
    assert await tsm.enqueue_from_scheduled()
    assert tsm.state == TaskStatus.QUEUED


# --- invalid transitions rejected ---

@pytest.mark.asyncio
async def test_cannot_cancel_from_pending(tsm):
    assert not await tsm.cancel()
    assert tsm.state == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_cannot_start_from_pending(tsm):
    assert not await tsm.start()
    assert tsm.state == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_cannot_complete_from_pending(tsm):
    assert not await tsm.complete()
    assert tsm.state == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_cannot_retry_from_pending(tsm):
    assert not await tsm.prepare_retry()
    assert tsm.state == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_terminal_success_is_immutable(tsm):
    await tsm.submit(scheduled=False)
    await tsm.assign()
    await tsm.start()
    await tsm.complete()
    assert tsm.is_terminal
    assert not await tsm.cancel()
    assert not await tsm.fail()
    assert not await tsm.start()
    assert tsm.state == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_terminal_cancelled_is_immutable(tsm):
    await tsm.submit(scheduled=False)
    await tsm.cancel()
    assert tsm.is_terminal
    assert not await tsm.assign()
    assert not await tsm.start()
    assert not await tsm.complete()
    assert tsm.state == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_cannot_cancel_from_success(tsm):
    await tsm.submit(scheduled=False)
    await tsm.assign()
    await tsm.start()
    await tsm.complete()
    assert not await tsm.cancel()


@pytest.mark.asyncio
async def test_cannot_assign_directly_from_pending(tsm):
    assert not await tsm.assign()
    assert tsm.state == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_failure_is_not_terminal_if_retry_possible(tsm):
    """FAILURE is not terminal since RETRYING is a valid outbound transition."""
    await tsm.submit(scheduled=False)
    await tsm.assign()
    await tsm.start()
    await tsm.fail()
    assert not tsm.is_terminal  # can still retry
    assert tsm.can_transition(TaskStatus.RETRYING)
