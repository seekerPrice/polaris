"""Phase 8 A2 — live compliance PDF endpoint verification."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("POLARIS_LIVE_E2E"),
    reason="needs full stack on :8000/:8080/:11434",
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_compliance_report_pdf_renders():
    async with httpx.AsyncClient(timeout=180) as client:
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
        assert "policy.yaml" in j

        pdf_resp = await client.get(f"http://localhost:8000/api/compliance-report/{job_id}")
        assert pdf_resp.status_code == 200, f"status={pdf_resp.status_code} body={pdf_resp.text[:300]}"
        ct = pdf_resp.headers.get("content-type", "")
        assert ct.startswith("application/pdf"), f"content-type={ct!r}"
        assert pdf_resp.content[:4] == b"%PDF", f"not a valid PDF magic: {pdf_resp.content[:30]!r}"
        assert len(pdf_resp.content) > 1000, f"PDF suspiciously small ({len(pdf_resp.content)}b)"
