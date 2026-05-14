"""Tests for the generic StateMachine base class."""

import asyncio
from enum import Enum

import pytest

from fastworker.utils.state_machine import StateMachine


class TestState(str, Enum):
    A = "a"
    B = "b"
    C = "c"


TRANSITIONS = {
    TestState.A: {TestState.B},
    TestState.B: {TestState.C},
    TestState.C: set(),
}


@pytest.fixture
def sm():
    return StateMachine(TestState.A, TRANSITIONS)


def test_initial_state(sm):
    assert sm.state == TestState.A


def test_can_transition_valid(sm):
    assert sm.can_transition(TestState.B) is True


def test_can_transition_invalid(sm):
    assert sm.can_transition(TestState.C) is False


def test_can_transition_from_terminal():
    sm = StateMachine(TestState.C, TRANSITIONS)
    assert sm.can_transition(TestState.A) is False
    assert sm.can_transition(TestState.B) is False


@pytest.mark.asyncio
async def test_transition_success(sm):
    result = await sm.transition(TestState.B)
    assert result is True
    assert sm.state == TestState.B


@pytest.mark.asyncio
async def test_transition_rejected(sm):
    result = await sm.transition(TestState.C)
    assert result is False
    assert sm.state == TestState.A


@pytest.mark.asyncio
async def test_transition_through_chain(sm):
    assert await sm.transition(TestState.B)
    assert await sm.transition(TestState.C)
    assert sm.state == TestState.C
    # Terminal - cannot transition further
    assert await sm.transition(TestState.A) is False


@pytest.mark.asyncio
async def test_callbacks_fire_on_transition(sm):
    events = []

    async def cb(from_s, to_s):
        events.append((from_s, to_s))

    sm.on_transition(cb)
    await sm.transition(TestState.B)
    assert events == [(TestState.A, TestState.B)]


@pytest.mark.asyncio
async def test_callbacks_not_fired_on_rejected_transition(sm):
    events = []

    async def cb(from_s, to_s):
        events.append((from_s, to_s))

    sm.on_transition(cb)
    await sm.transition(TestState.C)  # invalid
    assert events == []


@pytest.mark.asyncio
async def test_callback_exception_does_not_break_transition(sm):
    async def bad_cb(from_s, to_s):
        raise RuntimeError("callback boom")

    sm.on_transition(bad_cb)
    result = await sm.transition(TestState.B)
    assert result is True
    assert sm.state == TestState.B


@pytest.mark.asyncio
async def test_remove_callback(sm):
    events = []

    async def cb(from_s, to_s):
        events.append((from_s, to_s))

    sm.on_transition(cb)
    sm.remove_callback(cb)
    await sm.transition(TestState.B)
    assert events == []


@pytest.mark.asyncio
async def test_lock_prevents_concurrent_mutation(sm):
    """Two concurrent transitions; second sees updated state."""
    # Transition to B
    t1 = asyncio.create_task(sm.transition(TestState.B))
    await t1
    # Now try transition to C (valid from B)
    t2 = asyncio.create_task(sm.transition(TestState.C))
    result = await t2
    assert result is True
    assert sm.state == TestState.C


@pytest.mark.asyncio
async def test_multiple_callbacks(sm):
    events = []

    async def cb1(from_s, to_s):
        events.append(("cb1", from_s, to_s))

    async def cb2(from_s, to_s):
        events.append(("cb2", from_s, to_s))

    sm.on_transition(cb1)
    sm.on_transition(cb2)
    await sm.transition(TestState.B)
    assert len(events) == 2
