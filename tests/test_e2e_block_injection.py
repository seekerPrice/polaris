import asyncio
import os
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("POLARIS_LIVE_E2E"),
    reason="set POLARIS_LIVE_E2E=1 with stack running on :8000/:8080/:11434",
)


@pytest.mark.asyncio
async def test_indirect_injection_blocked():
    async with httpx.AsyncClient(timeout=180) as client:
        with open("examples/soc2_excerpt.md", "rb") as f:
            r = await client.post(
                "http://localhost:8000/api/policies/generate",
                files={"file": ("soc2.md", f, "text/markdown")},
            )
        job_id = r.json()["job_id"]

        for _ in range(60):
            j = (await client.get(f"http://localhost:8000/api/policies/{job_id}")).json()
            if "policy.yaml" in j:
                break
            await asyncio.sleep(2)
        assert "policy.yaml" in j, "policy never generated"

        # `policy.yaml` is written BEFORE _redeploy stops/respawns Lobster Trap. There's
        # a ~10s window after policy.yaml exists where :8080 is between stop and spawn.
        # Retry the LT call up to 10 times (20s total) to ride through that window.
        feedback = Path("examples/customer_feedback_today.txt").read_text()
        body = {
            "model": "gemini-3.1-flash-lite",
            "messages": [{"role": "user", "content": feedback}],
            "_lobstertrap": {"declared_intent": "file_io", "agent_id": "sales-ops-copilot-v1"},
        }
        last_exc: Exception | None = None
        out = None
        for _ in range(10):
            try:
                out = await client.post("http://localhost:8080/v1/chat/completions", json=body)
                break
            except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                await asyncio.sleep(2)
        assert out is not None, f"could not reach lobstertrap on :8080 after retries: {last_exc}"
        assert out.status_code in (403, 451) or "DENY" in out.text or "blocked" in out.text.lower(), (
            f"injection NOT blocked: status={out.status_code} body={out.text[:300]}"
        )
