"""Phase 8 A1 — live Red Team closed-loop verification.

Demo beats 7-10:
  - probe 1: indirect injection in customer feedback → DENY (existing rule catches it)
  - probe 2: base64-encoded variant → ALLOW (gap, initial policy lacks obfuscation rule)
  - probe 3: same base64 AFTER Synthesizer regenerated + LT hot-reloaded → DENY (new rule)

Asserts: 3 probe results published, probe 2 is_gap=True, probe 3 is_gap=False, ≥1 reload event.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("POLARIS_LIVE_E2E"),
    reason="needs full stack on :8000/:8080/:11434 (set POLARIS_LIVE_E2E=1)",
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_redteam_finds_gap_and_synth_patches():
    async with httpx.AsyncClient(timeout=420) as client:
        # 1. Deploy initial policy from SOC 2
        with open(_REPO_ROOT / "examples" / "soc2_excerpt.md", "rb") as f:
            r = await client.post(
                "http://localhost:8000/api/policies/generate",
                files={"file": ("soc2.md", f, "text/markdown")},
            )
        job_id = r.json()["job_id"]
        for _ in range(120):
            j = (await client.get(f"http://localhost:8000/api/policies/{job_id}")).json()
            if "policy.yaml" in j:
                break
            await asyncio.sleep(2)
        assert "policy.yaml" in j, f"policy never generated for job {job_id}"

        events: list[dict] = []

        async def collect() -> None:
            async with client.stream("GET", "http://localhost:8000/api/events") as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        ev = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    events.append(ev)
                    results = [e for e in events if e.get("type") == "redteam_probe_result"]
                    if len(results) >= 3:
                        return

        sse_task = asyncio.create_task(collect())
        await asyncio.sleep(2)
        await client.post(f"http://localhost:8000/api/redteam/start?job_id={job_id}")

        try:
            await asyncio.wait_for(sse_task, timeout=300)
        except asyncio.TimeoutError:
            sse_task.cancel()

        results = [e for e in events if e.get("type") == "redteam_probe_result"]
        reloads = [e for e in events if e.get("type") == "lobstertrap_reloaded"]
        assert len(results) >= 3, f"got {len(results)} probe results, expected 3. events={[e.get('type') for e in events]}"
        # Probe 2 is the engineered gap (base64-encoded exfiltration; initial policy has no obfuscation rule)
        assert results[1]["result"]["is_gap"], f"probe 2 should have been a gap: {results[1]}"
        # Probe 3 is the same payload AFTER Synthesizer added the obfuscation rule
        assert not results[2]["result"]["is_gap"], f"probe 3 should have been blocked post-patch: {results[2]}"
        assert len(reloads) >= 1, f"Synthesizer never patched + reloaded; events: {[e.get('type') for e in events]}"
