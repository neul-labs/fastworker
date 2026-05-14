"""asyncio.Queue-based event bus for state transition events."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EventBus:
    """Simple pub/sub event bus backed by asyncio.Queue.

    Publishers call :meth:`emit`. Subscribers iterate over :meth:`subscribe`,
    which yields events as they arrive.
    """

    def __init__(self, maxsize: int = 0):
        self._queues: list[asyncio.Queue] = []
        self._maxsize = maxsize

    async def emit(self, event_name: str, data: Optional[dict] = None) -> None:
        """Publish an event to all subscribers."""
        event = {"name": event_name, "data": data or {}}
        dead_queues = []
        for q in self._queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.debug(f"EventBus queue full, dropping event: {event_name}")
            except Exception:
                dead_queues.append(q)

        for q in dead_queues:
            if q in self._queues:
                self._queues.remove(q)

    async def subscribe(self):
        """Async generator that yields events as they arrive."""
        q: asyncio.Queue = asyncio.Queue(maxsize=self._maxsize)
        self._queues.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            if q in self._queues:
                self._queues.remove(q)

    def subscriber_count(self) -> int:
        return len(self._queues)
