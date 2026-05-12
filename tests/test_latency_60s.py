import asyncio
import os
import time

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("POLARIS_LIVE_E2E"),
    reason="set POLARIS_LIVE_E2E=1 with stack running on :8000",
)


@pytest.mark.asyncio
async def test_upload_to_deploy_under_60s():
    """Hero metric: 'From SOC 2 PDF to live AI guardrail in 60 seconds.' If this assertion
    breaks, the README's headline lies — fix the metric or the headline before submission."""
    async with httpx.AsyncClient(timeout=180) as client:
        t0 = time.monotonic()
        with open("examples/soc2_excerpt.md", "rb") as f:
            r = await client.post(
                "http://localhost:8000/api/policies/generate",
                files={"file": ("soc2.md", f, "text/markdown")},
            )
        job = r.json()["job_id"]
        j: dict = {}
        for _ in range(90):
            j = (await client.get(f"http://localhost:8000/api/policies/{job}")).json()
            if "policy.yaml" in j:
                break
            await asyncio.sleep(1)
        elapsed = time.monotonic() - t0
        assert "policy.yaml" in j, f"no policy.yaml after {elapsed:.1f}s"
        assert elapsed <= 60, f"hero metric breached: {elapsed:.1f}s > 60s"
