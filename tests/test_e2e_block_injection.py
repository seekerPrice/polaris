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

        out = await client.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "model": "gemini-3-flash-preview",
                "messages": [{"role": "user", "content": Path("examples/customer_feedback_today.txt").read_text()}],
                "_lobstertrap": {"declared_intent": "file_io", "agent_id": "sales-ops-copilot-v1"},
            },
        )
        assert out.status_code in (403, 451) or "DENY" in out.text or "blocked" in out.text.lower(), (
            f"injection NOT blocked: status={out.status_code} body={out.text[:300]}"
        )
