"""Generic async state machine with atomic transitions and event emission."""

import asyncio
from enum import Enum
from typing import Awaitable, Callable, Generic, TypeVar

S = TypeVar("S", bound=Enum)


class StateMachine(Generic[S]):
    """Generic state machine with atomic transitions under asyncio.Lock.

    Transitions are validated against a transition table. Callbacks are invoked
    after every successful transition but cannot abort or reverse it — they are
    fire-and-forget observers.
    """

    def __init__(self, initial_state: S, transitions: dict[S, set[S]]):
        self._state: S = initial_state
        self._transitions: dict[S, set[S]] = transitions
        self._lock = asyncio.Lock()
        self._callbacks: list[Callable[[S, S], Awaitable[None]]] = []

    @property
    def state(self) -> S:
        return self._state

    def can_transition(self, to: S) -> bool:
        return to in self._transitions.get(self._state, set())

    async def transition(self, to: S) -> bool:
        """Attempt to transition to *to*. Returns True on success, False if disallowed."""
        async with self._lock:
            if not self.can_transition(to):
                return False
            from_state = self._state
            self._state = to
            await self._fire_callbacks(from_state, to)
            return True

    def on_transition(self, callback: Callable[[S, S], Awaitable[None]]) -> None:
        """Register an async callback invoked on every successful transition."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[S, S], Awaitable[None]]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _fire_callbacks(self, from_state: S, to: S) -> None:
        for cb in self._callbacks:
            try:
                await cb(from_state, to)
            except Exception:
                pass  # callbacks are observers, must not break the transition
