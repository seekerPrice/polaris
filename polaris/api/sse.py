from __future__ import annotations

import json
from typing import AsyncIterator

from sse_starlette.sse import EventSourceResponse

from polaris.api.state import BUS


async def event_stream() -> AsyncIterator[dict]:
    q = BUS.subscribe()
    try:
        while True:
            ev = await q.get()
            # IMPORTANT: do NOT set "event" — browser EventSource.onmessage only fires for
            # default-named events. The frontend discriminates on JSON.parse(e.data).type.
            yield {"data": json.dumps(ev)}
    finally:
        BUS.unsubscribe(q)


def sse_response() -> EventSourceResponse:
    # Phase-11 deep-review I7 (api): 15s heartbeats keep idle connections alive through
    # intermediate proxies/load balancers. Without `ping`, a 30+ second pause (e.g., the
    # presenter talking before dragging the PDF) can drop the SSE silently — the browser
    # auto-reconnects with a fresh subscriber queue and events emitted during the gap
    # are lost.
    return EventSourceResponse(event_stream(), ping=15)
