from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)


class EventBus:
    """Tiny in-process pub/sub for SSE fan-out. One queue per subscriber.

    `unsubscribe` MUST be called when a subscriber disconnects, otherwise the
    subscriber list grows unbounded across browser reconnects (memory leak +
    `publish` slows linearly with stale queues).

    L26 NOTE (deep-check 2026-05-13): BUS is process-local. The uvicorn invocation in
    `polaris/api/server.py::main` and `scripts/run_demo.sh` runs a single worker on
    purpose — multi-worker would split SSE subscribers across workers that each have
    their own BUS, silently dropping events. Do NOT set `--workers N>1` without first
    swapping this for redis pub/sub or a single-process gateway.
    """

    def __init__(self) -> None:
        self._subs: list[asyncio.Queue[dict[str, Any]]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue = asyncio.Queue(maxsize=512)
        self._subs.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._subs.remove(q)
        except ValueError:
            pass

    async def publish(self, event: dict[str, Any]) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # drop on slow consumer; SSE is best-effort
                log.warning("eventbus.drop type=%s qsize=%d", event.get("type", "?"), q.qsize())


BUS = EventBus()
