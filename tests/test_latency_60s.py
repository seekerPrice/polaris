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
async def test_upload_to_deploy_under_90s():
    """SLA: upload → deployed-policy ≤90s (p95 budget). The README's '60 seconds' headline
    is the median we observe in practice (~50s); 90s is the hard ceiling that absorbs one
    Gemini transient retry. If THIS breaks, something structural regressed."""
    async with httpx.AsyncClient(timeout=180) as client:
        t0 = time.monotonic()
        with open("examples/soc2_excerpt.md", "rb") as f:
            r = await client.post(
                "http://localhost:8000/api/policies/generate",
                files={"file": ("soc2.md", f, "text/markdown")},
            )
        job = r.json()["job_id"]
        j: dict = {}
        for _ in range(120):
            j = (await client.get(f"http://localhost:8000/api/policies/{job}")).json()
            if "policy.yaml" in j:
                break
            await asyncio.sleep(1)
        elapsed = time.monotonic() - t0
        assert "policy.yaml" in j, f"no policy.yaml after {elapsed:.1f}s"
        assert elapsed <= 90, f"latency SLA breached: {elapsed:.1f}s > 90s"
        # informational — print actual time so the README claim can be re-validated
        print(f"\n[latency] upload→deploy elapsed: {elapsed:.1f}s")
