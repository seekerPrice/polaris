from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from polaris.agents.auditor import render_compliance_report
from polaris.agents.reader import PolicyTree, Reader
from polaris.agents.redteam import RedTeam
from polaris.agents.synthesizer import Synthesizer
from polaris.api.state import BUS
from polaris.api.sse import sse_response
from polaris.lobster.client import LobsterTrap
from polaris.utils.db import (
    fetch_audit_entries,
    record_audit_entry,
    record_job,
    update_job,
)
from polaris.utils.pdf_extractor import extract_text


router = APIRouter()
DB_PATH = Path("./polaris.db")
ARTIFACTS = Path("./artifacts")
LT = LobsterTrap()
# Track the audit-log tail task so we can cancel before reloading Lobster Trap.
_AUDIT_TASK: asyncio.Task | None = None
# Serialise _redeploy across concurrent uploads — two browser tabs uploading
# back-to-back would otherwise fight for _AUDIT_TASK + LT.reload sequencing.
_REDEPLOY_LOCK = asyncio.Lock()
_ATTEMPTED: list[str] = []


@router.get("/api/events")
async def events():
    return sse_response()


@router.post("/api/policies/generate")
async def generate(bg: BackgroundTasks, file: UploadFile = File(...)):
    job_id = uuid.uuid4().hex[:12]
    job_dir = ARTIFACTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    raw_path = job_dir / (file.filename or "upload.bin")
    raw_path.write_bytes(await file.read())
    await record_job(DB_PATH, job_id, file.filename or "upload.bin", status="reading")
    bg.add_task(_pipeline, job_id, raw_path)
    return {"job_id": job_id}


@router.get("/api/policies/{job_id}")
async def get_job(job_id: str):
    job_dir = ARTIFACTS / job_id
    out: dict[str, Any] = {"job_id": job_id}
    for name in ("policy_tree.json", "policy.yaml", "declared_intents.json", "test_results.txt"):
        p = job_dir / name
        if p.exists():
            out[name] = p.read_text(encoding="utf-8")
    return out


@router.post("/api/policies/{job_id}/deploy")
async def deploy(job_id: str):
    pol = ARTIFACTS / job_id / "policy.yaml"
    if not pol.exists():
        raise HTTPException(404, "policy.yaml not generated yet")
    gen = await _redeploy(job_id, pol)
    return {"deployed": True, "generation": gen}


@router.get("/api/audit-log")
async def audit_log(limit: int = 100, offset: int = 0):
    return await fetch_audit_entries(DB_PATH, limit=limit, offset=offset)


@router.get("/api/compliance-report/{job_id}")
async def compliance_report(job_id: str):
    job_dir = ARTIFACTS / job_id
    tree_path = job_dir / "policy_tree.json"
    if not tree_path.exists():
        raise HTTPException(404, "policy tree not generated yet")
    tree = PolicyTree.model_validate_json(tree_path.read_text())
    audits = await fetch_audit_entries(DB_PATH, limit=200)
    # Phase-10 T1.2: pass deployed policy YAML so the renderer can compute control→rule mapping.
    policy_path = job_dir / "policy.yaml"
    policy_yaml = policy_path.read_text() if policy_path.exists() else None
    pdf = job_dir / "compliance_report.pdf"
    render_compliance_report(tree, [a["raw"] for a in audits], pdf, policy_yaml=policy_yaml)
    return FileResponse(pdf, media_type="application/pdf", filename="polaris_compliance_report.pdf")


@router.post("/api/redteam/start")
async def redteam_start(job_id: str):
    job_dir = ARTIFACTS / job_id
    pol_path = job_dir / "policy.yaml"
    if not pol_path.exists():
        raise HTTPException(404, "policy.yaml not generated yet")
    pol = pol_path.read_text()
    audits = await fetch_audit_entries(DB_PATH, limit=20)
    asyncio.create_task(_redteam_loop(job_id, pol, audits))
    return {"started": True}


# ---------------- internals ----------------

async def _redeploy(job_id: str, policy_path: Path) -> int:
    """Cancel any prior audit-tail task, reload Lobster Trap to a new generation,
    then start a fresh audit-tail bound to that generation. Serialised so concurrent
    uploads don't fight for the same singleton LT/audit task."""
    global _AUDIT_TASK
    async with _REDEPLOY_LOCK:
        if _AUDIT_TASK and not _AUDIT_TASK.done():
            _AUDIT_TASK.cancel()
            try:
                await _AUDIT_TASK
            except (asyncio.CancelledError, Exception):
                pass
        gen = await LT.reload(policy_path)
        _AUDIT_TASK = asyncio.create_task(_pump_audit_log(job_id, gen))
        await BUS.publish({"type": "lobstertrap_deployed", "job_id": job_id, "generation": gen})
        return gen


async def _pipeline(job_id: str, file_path: Path) -> None:
    job_dir = ARTIFACTS / job_id
    text = (
        file_path.read_text(encoding="utf-8")
        if file_path.suffix in (".md", ".txt")
        else await extract_text(file_path)
    )

    await BUS.publish({"type": "reader_progress", "job_id": job_id, "status": "started"})
    tree: PolicyTree = await Reader().process(text)
    (job_dir / "policy_tree.json").write_text(tree.model_dump_json(indent=2))
    await BUS.publish({
        "type": "reader_progress", "job_id": job_id, "status": "completed",
        "n_requirements": len(tree.requirements),
    })
    await update_job(DB_PATH, job_id, policy_tree_json=tree.model_dump_json(), status="synthesizing")

    await BUS.publish({"type": "synthesizer_progress", "job_id": job_id, "status": "started"})
    syn = await Synthesizer().process(tree)
    (job_dir / "policy.yaml").write_text(syn.output.yaml_text)
    (job_dir / "declared_intents.json").write_text(
        json.dumps({k: v.model_dump() for k, v in syn.output.declared_intents.items()}, indent=2)
    )
    (job_dir / "test_results.txt").write_text(syn.test_results_summary)
    await BUS.publish({
        "type": "synthesizer_progress", "job_id": job_id, "status": "completed",
        "passed": syn.passed,
    })
    await update_job(
        DB_PATH, job_id,
        policy_yaml=syn.output.yaml_text,
        status="validated" if syn.passed else "failed",
    )

    if syn.passed:
        await _redeploy(job_id, job_dir / "policy.yaml")


async def _pump_audit_log(job_id: str, generation: int) -> None:
    async for entry in LT.tail_audit_log(generation=generation):
        await record_audit_entry(DB_PATH, job_id, entry.raw)
        await BUS.publish({"type": "audit_log_entry", "job_id": job_id, "entry": entry.raw})


async def _redteam_loop(job_id: str, policy_yaml: str, audits: list[dict]) -> None:
    rt = RedTeam()
    probes = await rt.demo_sequence()
    for probe in probes:
        await BUS.publish({"type": "redteam_probe_started", "job_id": job_id, "probe": probe.model_dump()})
        result = await rt.fire(probe)
        await BUS.publish({
            "type": "redteam_probe_result", "job_id": job_id,
            "result": {
                "probe": probe.model_dump(),
                "actual_verdict": result.actual_verdict,
                "is_gap": result.is_gap,
            },
        })
        _ATTEMPTED.append(probe.prompt[:200])
        if result.is_gap:
            await _patch_policy(job_id, gap_evidence={
                "attack_prompt": probe.prompt,
                "expected": probe.expected_verdict,
                "actual": result.actual_verdict,
            })
            # Give LT a moment to fully come up after the hot-reload before firing
            # the next probe — otherwise probe 3 races against LT.spawn() and gets
            # a ConnectError instead of the expected DENY.
            await asyncio.sleep(2)


async def _patch_policy(job_id: str, gap_evidence: dict) -> None:
    job_dir = ARTIFACTS / job_id
    tree = PolicyTree.model_validate_json((job_dir / "policy_tree.json").read_text())
    prev_yaml = (job_dir / "policy.yaml").read_text()
    await BUS.publish({"type": "synthesizer_progress", "job_id": job_id, "status": "regenerating"})
    syn = await Synthesizer().regenerate(tree, gap_evidence, prev_yaml)
    if not syn.passed:
        await BUS.publish({
            "type": "synthesizer_progress", "job_id": job_id, "status": "regen_failed",
            "summary": syn.test_results_summary,
        })
        return
    (job_dir / "policy.yaml").write_text(syn.output.yaml_text)
    await _redeploy(job_id, job_dir / "policy.yaml")
    await BUS.publish({"type": "lobstertrap_reloaded", "job_id": job_id})
