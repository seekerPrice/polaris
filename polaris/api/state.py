from __future__ import annotations

import asyncio
from typing import Any


class EventBus:
    """Tiny in-process pub/sub for SSE fan-out. One queue per subscriber."""

    def __init__(self) -> None:
        self._subs: list[asyncio.Queue[dict[str, Any]]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue = asyncio.Queue(maxsize=512)
        self._subs.append(q)
        return q

    async def publish(self, event: dict[str, Any]) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # drop on slow consumer; SSE is best-effort
                pass


BUS = EventBus()
