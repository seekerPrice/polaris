from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Annotated

# C4 fix (deep-check 2026-05-13): all job_id path params and the upload filename are
# attacker-controlled. Validate at the boundary so traversal vectors can't reach the
# filesystem. job_id format is `uuid.uuid4().hex[:12]` (12 hex chars).
_JOB_ID_RE = re.compile(r"^[a-f0-9]{12}$")
_UPLOAD_SUFFIX_ALLOWLIST = {".pdf", ".md", ".txt"}


def _validate_job_id(job_id: str) -> str:
    if not _JOB_ID_RE.match(job_id):
        raise HTTPException(404, "job not found")
    return job_id


def _safe_upload_path(job_dir: Path, raw_filename: str | None) -> Path:
    """Strip directory components, allowlist suffix, and confirm resolved path stays
    inside job_dir. Returns a safe absolute path to write the upload to."""
    base = Path(raw_filename or "upload.bin").name  # drops any "../" / leading "/"
    suffix = Path(base).suffix.lower()
    if suffix not in _UPLOAD_SUFFIX_ALLOWLIST:
        # Reject rather than rename — keeps the failure mode loud.
        raise HTTPException(415, f"unsupported file type: {suffix or '(none)'}")
    target = (job_dir / base).resolve()
    if not target.is_relative_to(job_dir.resolve()):
        raise HTTPException(400, "invalid filename")
    return target

log = logging.getLogger(__name__)

# Phase-11 T1.B3: default baseline policy deployed on Synth failure / startup before
# any compliance doc is uploaded. Known-safe; LT corpus 11/11 PASS verified.
# Anchored off this file's location, not CWD, so the API still works if uvicorn is
# launched from a non-root directory (Phase-11 deep-review I1).
_DEFAULT_BASELINE_POLICY = Path(__file__).resolve().parents[2] / "policies" / "default_baseline.yaml"

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from pydantic import BaseModel

from polaris.agents.auditor import render_compliance_report
from polaris.agents.reader import PolicyTree, Reader
from polaris.agents.redteam import RedTeam
from polaris.agents.synthesizer import Synthesizer, SynthesizerGateError
from polaris.api.approval import ApprovalGate, ApprovalState
from polaris.api.state import BUS
from polaris.api.sse import sse_response
from polaris.lobster.client import LobsterTrap
from polaris.utils.db import (
    fetch_audit_entries,
    record_audit_entry,
    record_job,
    record_policy_deploy,
    record_quarantine_decision,
    update_job,
)
from polaris.utils.pdf_extractor import extract_text


router = APIRouter()
DB_PATH = Path("./polaris.db")
ARTIFACTS = Path("./artifacts")
LT = LobsterTrap()
# Phase-12 T6: pre-built policy packs anchored off this file's location so
# uvicorn launched from anywhere still finds them.
_BUILTIN_PACKS_DIR = Path(__file__).resolve().parents[2] / "policies" / "builtin"
# Pack name must be a-z0-9_ only — defeats path traversal even though we
# resolve+containment-check below as belt-and-suspenders.
_PACK_NAME_RE = re.compile(r"^[a-z0-9_]{1,32}$")
# Track the audit-log tail task so we can cancel before reloading Lobster Trap.
_AUDIT_TASK: asyncio.Task | None = None
# Serialise _redeploy across concurrent uploads — two browser tabs uploading
# back-to-back would otherwise fight for _AUDIT_TASK + LT.reload sequencing.
_REDEPLOY_LOCK = asyncio.Lock()
# Phase-11 deep-review C2 (api): keep strong references to fire-and-forget tasks
# (red team loops, regen pipelines) so asyncio doesn't GC them mid-execution.
_BACKGROUND_TASKS: set[asyncio.Task] = set()
# Phase-12 T1: pending consent gates keyed by job_id. POST /approve and /reject
# look up the gate here and release it. Cleared as soon as the gate resolves.
#
# IMPORTANT: SINGLE-WORKER MODE ONLY. Like BUS (polaris/api/state.py), this dict
# is process-local. A gate inserted by worker A is invisible to worker B
# receiving /approve. scripts/run_demo.sh and polaris/api/server.py both pin
# uvicorn to one worker. Do NOT raise --workers without first moving this
# (and BUS) to redis or a shared store.
_APPROVAL_GATES: dict[str, ApprovalGate] = {}


def _count_rules(yaml_text: str) -> int:
    """Phase-12 T1: rule count surfaced in awaiting_approval event so the operator
    sees policy depth at a glance ('14 rules ready to deploy').

    Returns -1 on malformed YAML so the UI can render '?' instead of '0' — at
    this point the YAML has already passed Synthesizer validation, so a parse
    failure here is suspicious and worth a log line (reviewer I5)."""
    import yaml
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        log.warning("count_rules: post-validation YAML parse failed: %r", exc)
        return -1
    if not isinstance(data, dict):
        log.warning("count_rules: YAML root is not a mapping (got %s)", type(data).__name__)
        return -1
    ingress = data.get("ingress_rules") or []
    egress = data.get("egress_rules") or []
    return len(ingress) + len(egress)


def _spawn_background(coro, label: str) -> asyncio.Task:
    """Create a task we will not await, but keep a strong ref + log failures."""
    t = asyncio.create_task(coro, name=label)
    _BACKGROUND_TASKS.add(t)

    def _done(task: asyncio.Task) -> None:
        _BACKGROUND_TASKS.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            log.error("background task %s failed: %r", label, exc)

    t.add_done_callback(_done)
    return t


@router.get("/api/events")
async def events():
    return sse_response()


@router.post("/api/policies/generate")
async def generate(file: UploadFile = File(...)):
    job_id = uuid.uuid4().hex[:12]
    job_dir = ARTIFACTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    # C4 fix (deep-check 2026-05-13): sanitize attacker-controlled file.filename
    # before joining onto job_dir. Without this, `filename="/etc/cron.d/x"` would
    # write arbitrary content thanks to Python's Path-with-absolute-RHS semantics.
    raw_path = _safe_upload_path(job_dir, file.filename)
    raw_path.write_bytes(await file.read())
    await record_job(DB_PATH, job_id, raw_path.name, status="reading")
    # Phase-12 reviewer I1: prefer _spawn_background over FastAPI BackgroundTasks
    # so the pipeline doesn't hold the request handler open while waiting on the
    # 3 s consent gate (FastAPI awaits BackgroundTasks before freeing the worker).
    # Strong-ref pattern in _spawn_background keeps the task alive against asyncio GC.
    _spawn_background(_pipeline(job_id, raw_path), label=f"pipeline:{job_id}")
    return {"job_id": job_id}


@router.get("/api/policies/{job_id}")
async def get_job(job_id: str):
    _validate_job_id(job_id)
    job_dir = ARTIFACTS / job_id
    out: dict[str, Any] = {"job_id": job_id}
    for name in ("policy_tree.json", "policy.yaml", "declared_intents.json", "test_results.txt"):
        p = job_dir / name
        if p.exists():
            out[name] = p.read_text(encoding="utf-8")
    return out


@router.post("/api/policies/{job_id}/deploy")
async def deploy(job_id: str):
    _validate_job_id(job_id)
    pol = ARTIFACTS / job_id / "policy.yaml"
    if not pol.exists():
        raise HTTPException(404, "policy.yaml not generated yet")
    gen = await _redeploy(job_id, pol)
    return {"deployed": True, "generation": gen}


# Phase-12 T1: pre-deploy consent endpoints (SOC 2 CC8.1 change management).
class _ApprovalReq(BaseModel):
    approver: str = "operator@polaris.demo"


class _RejectionReq(BaseModel):
    approver: str = "operator@polaris.demo"
    reason: str = "manual reject"


@router.post("/api/policies/{job_id}/approve")
async def approve_policy(job_id: str, req: _ApprovalReq):
    _validate_job_id(job_id)
    gate = _APPROVAL_GATES.get(job_id)
    if gate is None:
        raise HTTPException(404, "no pending approval for this job")
    if gate.state is not ApprovalState.AWAITING:
        raise HTTPException(409, f"already {gate.state.value}")
    gate.approve(req.approver)
    return {"approved": True, "approver": req.approver}


@router.post("/api/policies/{job_id}/reject")
async def reject_policy(job_id: str, req: _RejectionReq):
    _validate_job_id(job_id)
    gate = _APPROVAL_GATES.get(job_id)
    if gate is None:
        raise HTTPException(404, "no pending approval for this job")
    if gate.state is not ApprovalState.AWAITING:
        raise HTTPException(409, f"already {gate.state.value}")
    gate.reject(req.approver, req.reason)
    return {"rejected": True, "reason": req.reason}


# Phase-12 T4: QUARANTINE Review Queue actions. Body is intentionally tiny — the
# operator identity is hardcoded for the demo (no auth in scope).
class _QuarantineDecisionReq(BaseModel):
    approver: str = "operator@polaris.demo"


@router.post("/api/audit/{entry_id}/release")
async def release_quarantine(entry_id: int, req: _QuarantineDecisionReq):
    if entry_id <= 0:
        raise HTTPException(400, "invalid entry_id")
    inserted = await record_quarantine_decision(
        DB_PATH, entry_id, "RELEASE", req.approver, time.time(),
    )
    if not inserted:
        raise HTTPException(409, "already decided")
    await BUS.publish({
        "type": "quarantine_decision",
        "entry_id": entry_id, "decision": "RELEASE", "approver": req.approver,
    })
    return {"released": True}


@router.post("/api/audit/{entry_id}/block")
async def block_quarantine(entry_id: int, req: _QuarantineDecisionReq):
    if entry_id <= 0:
        raise HTTPException(400, "invalid entry_id")
    inserted = await record_quarantine_decision(
        DB_PATH, entry_id, "BLOCK", req.approver, time.time(),
    )
    if not inserted:
        raise HTTPException(409, "already decided")
    await BUS.publish({
        "type": "quarantine_decision",
        "entry_id": entry_id, "decision": "BLOCK", "approver": req.approver,
    })
    return {"blocked": True}


# Phase-12 T6: pre-built policy pack endpoints. Packs skip the Reader+Synthesizer
# pipeline (no PDF to parse, no Gemini call) and deploy a pre-validated YAML
# through the same consent gate. Demo insurance against PDF parse failure;
# also matches Veea brief verbatim ("policy packs for HIPAA, SOC2, or finance").
@router.get("/api/policies/packs")
async def list_packs():
    if not _BUILTIN_PACKS_DIR.exists():
        return {"packs": []}
    packs = []
    for p in sorted(_BUILTIN_PACKS_DIR.glob("*.yaml")):
        if _PACK_NAME_RE.match(p.stem):
            packs.append({"name": p.stem, "filename": p.name})
    return {"packs": packs}


@router.post("/api/policies/packs/{name}/deploy")
async def deploy_pack(name: str):
    if not _PACK_NAME_RE.match(name):
        raise HTTPException(400, "invalid pack name")
    safe_path = (_BUILTIN_PACKS_DIR / f"{name}.yaml").resolve()
    if not safe_path.is_file() or safe_path.parent != _BUILTIN_PACKS_DIR.resolve():
        raise HTTPException(404, f"pack '{name}' not found")
    job_id = uuid.uuid4().hex[:12]
    job_dir = ARTIFACTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    pol_path = job_dir / "policy.yaml"
    # Explicit encoding on both ends (reviewer M2).
    pol_path.write_text(safe_path.read_text(encoding="utf-8"), encoding="utf-8")
    await record_job(DB_PATH, job_id, f"pack:{name}", status="validated")
    # Reviewer I1 — same rationale as /generate above.
    _spawn_background(_pack_deploy_pipeline(job_id, pol_path, name), label=f"pack_deploy:{job_id}")
    return {"job_id": job_id, "pack": name}


async def _pack_deploy_pipeline(job_id: str, pol_path: Path, pack_name: str) -> None:
    """Pack deploys skip Reader+Synthesizer but still flow through the consent
    gate so chain-of-custody audit trail is identical to a PDF-generated job."""
    yaml_text = pol_path.read_text(encoding="utf-8")
    policy_sha = hashlib.sha256(yaml_text.encode("utf-8")).hexdigest()[:12]
    await update_job(DB_PATH, job_id, policy_yaml=yaml_text, policy_sha256=policy_sha)
    # Synthesize a no-op reader_progress so the Pipeline UI doesn't stay at "idle".
    await BUS.publish({
        "type": "reader_progress", "job_id": job_id, "status": "completed",
        "n_requirements": 0,
    })
    await BUS.publish({
        "type": "synthesizer_progress", "job_id": job_id, "status": "completed",
        "passed": True, "summary": f"pre-built pack: {pack_name}",
    })

    gate = ApprovalGate(job_id, policy_sha, auto_approve_after=3.0)
    _APPROVAL_GATES[job_id] = gate
    await BUS.publish({
        "type": "awaiting_approval",
        "job_id": job_id, "policy_sha": policy_sha,
        "n_requirements": 0, "n_rules": _count_rules(yaml_text),
        "auto_approve_after_s": 3.0,
    })
    try:
        decision = await gate.wait_for_decision()
    finally:
        _APPROVAL_GATES.pop(job_id, None)

    await record_policy_deploy(
        DB_PATH, job_id, policy_sha,
        approver=decision.approver, approved=decision.approved,
        decided_at=decision.decided_at,
        deployed_at=decision.decided_at if decision.approved else None,
        reason=decision.reason,
    )
    if not decision.approved:
        await BUS.publish({
            "type": "policy_rejected",
            "job_id": job_id, "policy_sha": policy_sha,
            "approver": decision.approver, "reason": decision.reason,
        })
        await update_job(DB_PATH, job_id, status="rejected")
        return
    await _redeploy(job_id, pol_path)
    await BUS.publish({
        "type": "policy_approved",
        "job_id": job_id, "policy_sha": policy_sha,
        "approver": decision.approver, "decided_at": decision.decided_at,
    })
    await BUS.publish({"type": "policy_hash", "job_id": job_id, "sha256": policy_sha})


@router.get("/api/audit-log")
async def audit_log(
    # L24 fix (deep-check 2026-05-13): bound limit/offset so `?limit=99999999` can't
    # serialise a multi-MB JSON response and peg the event loop. Negative values now
    # reject with 422 instead of propagating to SQLite.
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await fetch_audit_entries(DB_PATH, limit=limit, offset=offset)


@router.get("/api/compliance-report/{job_id}")
async def compliance_report(job_id: str):
    _validate_job_id(job_id)
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
    # L30 fix (deep-check 2026-05-13): reportlab renders synchronously and can take
    # 1-2s on a busy policy. Push to a thread so it doesn't pin the event loop and
    # block SSE flushes for other clients during the demo.
    await asyncio.to_thread(
        render_compliance_report,
        tree, [a["raw"] for a in audits], pdf, policy_yaml,
    )
    return FileResponse(pdf, media_type="application/pdf", filename="polaris_compliance_report.pdf")


@router.post("/api/redteam/start")
async def redteam_start(job_id: str):
    _validate_job_id(job_id)
    job_dir = ARTIFACTS / job_id
    pol_path = job_dir / "policy.yaml"
    if not pol_path.exists():
        raise HTTPException(404, "policy.yaml not generated yet")
    pol = pol_path.read_text()
    audits = await fetch_audit_entries(DB_PATH, limit=20)
    _spawn_background(_redteam_loop(job_id, pol, audits), label=f"redteam_loop:{job_id}")
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
            except asyncio.CancelledError:
                pass  # expected when we cancel
            except Exception as exc:
                # Phase-11 deep-review C1 (api): log instead of silently swallowing.
                # A crashed audit pump used to take the dashboard dark with no signal.
                log.error("prior audit pump crashed: %r", exc)
        gen = await LT.reload(policy_path)
        _AUDIT_TASK = asyncio.create_task(_pump_audit_log(job_id, gen), name=f"audit:{job_id}:{gen}")
        await BUS.publish({"type": "lobstertrap_deployed", "job_id": job_id, "generation": gen})
        return gen


async def _pipeline(job_id: str, file_path: Path) -> None:
    # H2 fix (deep-check 2026-05-13): wrap the whole pipeline in try/except so a Gemini
    # failure / corrupt PDF / SynthesizerGateError publishes pipeline_error to SSE
    # instead of leaving the dashboard spinning at "reading" forever (CLAUDE.md §6).
    #
    # Code-review bug-1 fix (deep-check 2026-05-14): stage tracking is now a one-element
    # list mutated by _pipeline_inner as it advances through stages. A bare local in this
    # scope couldn't be reassigned from inside the inner function and always reported
    # "extract_text" no matter where the failure occurred.
    stage: list[str] = ["extract_text"]
    try:
        await _pipeline_inner(job_id, file_path, stage)
    except SynthesizerGateError as e:
        log.exception("synthesizer gate failed for job %s", job_id)
        await update_job(DB_PATH, job_id, status="failed")
        await BUS.publish({
            "type": "pipeline_error", "job_id": job_id,
            "stage": "synthesizer",
            "error": str(e),
            "test_summary": e.test_summary,
        })
        # Fall back to baseline if available so the firewall isn't left bare.
        if _DEFAULT_BASELINE_POLICY.exists():
            await BUS.publish({
                "type": "synthesizer_progress", "job_id": job_id,
                "status": "fell_back_to_baseline",
                "summary": f"Synth gate failed; deploying default_baseline.yaml. {e.test_summary[:200]}",
            })
            try:
                await _redeploy(job_id, _DEFAULT_BASELINE_POLICY)
            except Exception:
                log.exception("baseline-fallback _redeploy failed for job %s", job_id)
    except Exception as e:
        # Code-review bug-1 fix (deep-check 2026-05-14): also run the baseline fallback
        # here so a non-SynthesizerGateError failure (e.g. unexpected exception during
        # synth/deploy, or a future code path that throws something other than the
        # typed error) doesn't leave LT bare. The fallback is idempotent.
        log.exception("pipeline crashed for job %s at stage=%s", job_id, stage[0])
        await update_job(DB_PATH, job_id, status="failed")
        await BUS.publish({
            "type": "pipeline_error", "job_id": job_id,
            "stage": stage[0],
            "error": f"{type(e).__name__}: {e}"[:500],
        })
        if _DEFAULT_BASELINE_POLICY.exists():
            try:
                await _redeploy(job_id, _DEFAULT_BASELINE_POLICY)
                await BUS.publish({
                    "type": "synthesizer_progress", "job_id": job_id,
                    "status": "fell_back_to_baseline",
                    "summary": f"Pipeline failed at {stage[0]}; baseline redeployed.",
                })
            except Exception:
                log.exception("baseline-fallback _redeploy failed for job %s", job_id)


async def _pipeline_inner(job_id: str, file_path: Path, stage: list[str]) -> None:
    """Pipeline body. `stage` is a one-element list mutated as we advance so the
    caller's generic exception handler can report the right stage to the dashboard."""
    job_dir = ARTIFACTS / job_id
    stage[0] = "extract_text"
    text = (
        file_path.read_text(encoding="utf-8")
        if file_path.suffix in (".md", ".txt")
        else await extract_text(file_path)
    )

    stage[0] = "reader"
    await BUS.publish({"type": "reader_progress", "job_id": job_id, "status": "started"})
    tree: PolicyTree = await Reader().process(text)
    (job_dir / "policy_tree.json").write_text(tree.model_dump_json(indent=2))
    await BUS.publish({
        "type": "reader_progress", "job_id": job_id, "status": "completed",
        "n_requirements": len(tree.requirements),
    })
    await update_job(DB_PATH, job_id, policy_tree_json=tree.model_dump_json(), status="synthesizing")

    stage[0] = "synthesizer"
    await BUS.publish({"type": "synthesizer_progress", "job_id": job_id, "status": "started"})
    syn = await Synthesizer().process(tree)   # raises SynthesizerGateError on terminal failure
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

    stage[0] = "deploy"
    if syn.passed:
        # Phase-11 T1.B4: compute SHA-256 of the deployed YAML for audit-defensibility.
        # Phase-11 deep-review I5: publish policy_hash AFTER successful deploy so the
        # dashboard's "audit-defensible" claim only renders when the proxy is actually live.
        policy_sha = hashlib.sha256(syn.output.yaml_text.encode("utf-8")).hexdigest()[:12]
        await update_job(DB_PATH, job_id, policy_sha256=policy_sha)

        # Phase-12 T1: SOC 2 CC8.1 consent gate. Pipeline pauses here until the
        # operator clicks Approve/Reject OR the 3s auto-approve timer fires
        # (demo-mode safety). Chain of custody (approver + decided_at + SHA-256)
        # appended to policy_deploys for regulator-readable audit trail.
        gate = ApprovalGate(job_id, policy_sha, auto_approve_after=3.0)
        _APPROVAL_GATES[job_id] = gate
        await BUS.publish({
            "type": "awaiting_approval",
            "job_id": job_id,
            "policy_sha": policy_sha,
            "n_requirements": len(tree.requirements),
            "n_rules": _count_rules(syn.output.yaml_text),
            "auto_approve_after_s": 3.0,
        })
        try:
            decision = await gate.wait_for_decision()
        finally:
            _APPROVAL_GATES.pop(job_id, None)

        await record_policy_deploy(
            DB_PATH, job_id, policy_sha,
            approver=decision.approver,
            approved=decision.approved,
            decided_at=decision.decided_at,
            deployed_at=decision.decided_at if decision.approved else None,
            reason=decision.reason,
        )

        if not decision.approved:
            await BUS.publish({
                "type": "policy_rejected",
                "job_id": job_id,
                "policy_sha": policy_sha,
                "approver": decision.approver,
                "reason": decision.reason,
            })
            await update_job(DB_PATH, job_id, status="rejected")
            return

        await _redeploy(job_id, job_dir / "policy.yaml")
        await BUS.publish({
            "type": "policy_approved",
            "job_id": job_id,
            "policy_sha": policy_sha,
            "approver": decision.approver,
            "decided_at": decision.decided_at,
        })
        await BUS.publish({"type": "policy_hash", "job_id": job_id, "sha256": policy_sha})
    else:
        # Phase-11 T1.B3: Synth validation failed. Deploy the default baseline so the
        # proxy doesn't end up in an undefined state. Surfaced to the dashboard so the
        # operator knows we fell back.
        if _DEFAULT_BASELINE_POLICY.exists():
            await BUS.publish({
                "type": "synthesizer_progress", "job_id": job_id,
                "status": "fell_back_to_baseline",
                "summary": "Synth validation failed; deploying policies/default_baseline.yaml",
            })
            await _redeploy(job_id, _DEFAULT_BASELINE_POLICY)
        else:
            # Phase-11 deep-review I1 (api): explicit signal when the fallback file is missing.
            log.error("Synth failed AND default baseline missing at %s — proxy left in undefined state", _DEFAULT_BASELINE_POLICY)
            await BUS.publish({
                "type": "synthesizer_progress", "job_id": job_id,
                "status": "fallback_unavailable",
                "summary": f"Synth failed; baseline missing at {_DEFAULT_BASELINE_POLICY}",
            })


# Intent categories whose detection should trip a mismatch alarm if the agent's
# declared intent was the generic "general" or "communication" envelope. Narrowed to
# high-signal cases to avoid false-positive cascades on benign traffic (see Phase-11
# risk register 11.1b).
_HIGH_RISK_DETECTED_INTENTS: frozenset[str] = frozenset({
    "code_execution", "system", "credential_access", "data_access", "file_io", "network",
})
_LOW_DECLARED_INTENTS: frozenset[str] = frozenset({"general", "communication"})


def _compute_mismatches(raw: dict) -> list[str]:
    """Compare declared_headers from the agent (sent in `_lobstertrap` request body)
    against LT's detected metadata. Phase-11 T1.B1 — closes the dead-UI loop where
    `a.mismatches` was rendered but never populated by any producer. Returns a list
    of human-readable mismatch strings; empty list means no mismatch.

    Note: when LT itself emits structured `mismatches` (its own native producer),
    `_pump_audit_log` skips calling this function — LT's emit is strictly more
    informative. This function is the FALLBACK for entries LT doesn't pre-classify."""
    out: list[str] = []
    declared = raw.get("declared_headers") or raw.get("declared") or {}
    detected = raw.get("metadata") or raw.get("detected") or {}
    if not isinstance(declared, dict) or not isinstance(detected, dict):
        return out

    dec_intent = (declared.get("declared_intent") or "").strip().lower()
    det_intent = (detected.get("intent_category") or "").strip().lower()
    if (
        dec_intent
        and det_intent
        and dec_intent != det_intent
        and dec_intent in _LOW_DECLARED_INTENTS
        and det_intent in _HIGH_RISK_DETECTED_INTENTS
    ):
        risk = detected.get("risk_score")
        risk_str = f" (risk {risk:.2f})" if isinstance(risk, (int, float)) else ""
        out.append(f"declared_intent={dec_intent} but detected={det_intent}{risk_str}")

    # Smuggled targets: detected paths/domains the agent DIDN'T declare. Catches the
    # case where the agent says "I'll read /home/x" but LT-detected output mentions
    # /etc/shadow. Case-fold domain comparison (RFC 1035 domain names are case-insensitive);
    # paths stay case-sensitive (POSIX semantics).
    dec_paths = set(declared.get("declared_paths") or [])
    det_paths = set(detected.get("target_paths") or [])
    smuggled_paths = det_paths - dec_paths
    if smuggled_paths:
        out.append(f"undeclared target_paths: {sorted(smuggled_paths)[:3]}")

    dec_domains = {d.lower() for d in (declared.get("declared_domains") or []) if isinstance(d, str)}
    det_domains = {d.lower() for d in (detected.get("target_domains") or []) if isinstance(d, str)}
    smuggled_domains = det_domains - dec_domains
    if smuggled_domains and detected.get("contains_urls"):
        out.append(f"undeclared target_domains: {sorted(smuggled_domains)[:3]}")

    return out


def _normalize_mismatches(value: Any) -> list[str]:
    """LT can emit `mismatches` either as plain strings or as objects with
    `{field, declared, detected, severity}` keys. Normalize to plain strings so the
    dashboard's `mismatches: string[]` type renders correctly."""
    if not value:
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            field = item.get("field", "?")
            declared = item.get("declared")
            detected = item.get("detected")
            sev = item.get("severity")
            sev_tag = f" [{sev}]" if sev else ""
            out.append(f"{field}: declared={declared} detected={detected}{sev_tag}")
        else:
            out.append(str(item))
    return out


async def _pump_audit_log(job_id: str, generation: int) -> None:
    """Stream LT audit JSONL → DB + SSE bus. Each iteration is wrapped so one bad
    line can't kill the whole pump (Phase-11 deep-review C1)."""
    async for entry in LT.tail_audit_log(generation=generation):
        try:
            # Shallow-copy so downstream mutation (alias, mismatch) can't leak into
            # tail_audit_log's internal state (Phase-11 deep-review C3).
            raw = dict(entry.raw)
            # Phase-11 deep-review C1 (dashboard): the demo's "DENY flash" beat depended
            # on the dashboard reading `verdict` + `matched_rule`, but LT actually emits
            # `action` + `rule_name`. Alias here so the existing TS `AuditEntry` type
            # renders correctly AND `record_audit_entry`'s `raw.get("verdict")` populates
            # the DB column (was always NULL before). This unblocks demo beat 6.
            if "action" in raw and "verdict" not in raw:
                raw["verdict"] = raw["action"]
            if "rule_name" in raw and "matched_rule" not in raw:
                raw["matched_rule"] = raw["rule_name"]
            # Phase-11: alias LT's snake-cased field names so the dashboard's TypeScript
            # `AuditEntry` type renders them. LT emits `metadata` + `declared_headers`;
            # dashboard expects `detected` + `declared`.
            if "metadata" in raw and "detected" not in raw:
                raw["detected"] = raw["metadata"]
            if "declared_headers" in raw and "declared" not in raw:
                raw["declared"] = raw["declared_headers"]
            # Phase-11 T1.B1: augment with mismatches BEFORE persistence + publish.
            # LT-native (structured-object) emit takes priority — it's strictly more
            # informative than the Polaris fallback string format.
            lt_raw = raw.get("mismatches")
            if lt_raw:
                raw["mismatches"] = _normalize_mismatches(lt_raw)
            else:
                polaris_computed = _compute_mismatches(raw)
                if polaris_computed:
                    raw["mismatches"] = polaris_computed
            entry_id = await record_audit_entry(DB_PATH, job_id, raw)
            # Phase-12 T4: thread the auto-increment id onto the SSE payload so
            # the Quarantine Queue UI can identify which row an operator
            # release/block targets. Stamped after persistence so client and DB
            # agree on the id.
            raw["entry_id"] = entry_id
            await BUS.publish({"type": "audit_log_entry", "job_id": job_id, "entry": raw})
        except Exception as exc:
            # Phase-11 deep-review C1 (api): one bad line must not kill the pump.
            log.error("audit pump skipped malformed entry: %r", exc)
            continue


async def _redteam_loop(job_id: str, policy_yaml: str, audits: list[dict]) -> None:
    """Bounded iterative red-team loop.

    Iteration 1: deterministic `demo_sequence()` — pinned for the recorded demo.
    Iterations 2..N: `generate_batch()` — true autonomous probe generation against
    the patched policy, with `previously_attempted` short-circuiting duplicates.

    Terminates on (a) zero gaps in an iteration (saturation), (b) regen failure,
    or (c) hitting `POLARIS_RT_MAX_ITERATIONS` (default 3). The recording sets
    this to 1 so the demo stays deterministic; judges running live get the full
    continuous loop.
    """
    # C1 fix (code review 2026-05-14): guard env-var parse so a typo doesn't kill the
    # spawned task silently. Defaults to 3 on any parse error.
    try:
        max_iterations = max(1, int(os.environ.get("POLARIS_RT_MAX_ITERATIONS", "3")))
    except ValueError:
        log.warning("POLARIS_RT_MAX_ITERATIONS not parseable as int; defaulting to 3")
        max_iterations = 3
    rt = RedTeam()
    previously_attempted: list[str] = []
    # I3 fix (code review 2026-05-14): client-side dedup so a Gemini-emitted repeat
    # probe (the model ignores `previously_attempted` ~10-20% of the time on
    # 3.1-pro-preview) doesn't burn a regen cycle.
    attempted_hashes: set[str] = set()
    # I1 fix (code review 2026-05-14): coverage denominator counts ONLY probes whose
    # `expected_verdict` was in the blocked class. ERROR probes (HTTP 5xx / LT crash)
    # are excluded — infrastructure failure, not a gap. Correctly-handled ALLOW probes
    # are also excluded (they aren't attacks). This matches the demo narrative
    # "coverage = % of attacks the firewall caught."
    eligible_probes = 0
    eligible_blocked = 0
    total_probes = 0
    total_gaps_closed = 0
    _BLOCKED_CLASS = {"DENY", "HUMAN_REVIEW", "RATE_LIMIT"}

    def _coverage_pct() -> int:
        return int(round(100 * eligible_blocked / max(eligible_probes, 1)))

    for iteration in range(1, max_iterations + 1):
        # Pick probe source for this iteration.
        if iteration == 1:
            probes = await rt.demo_sequence()
        else:
            # C2 fix (code review 2026-05-14): guard policy.yaml read. If the file is
            # missing/truncated between iterations, publish failure instead of dying silently.
            try:
                current_policy = (ARTIFACTS / job_id / "policy.yaml").read_text(encoding="utf-8")
            except OSError as exc:
                log.error("policy.yaml read failed at iteration %d: %r", iteration, exc)
                await BUS.publish({
                    "type": "redteam_iteration_failed", "job_id": job_id,
                    "iteration": iteration,
                    "reason": f"policy_read_failed: {type(exc).__name__}: {exc}"[:200],
                })
                break
            fresh_audits = await fetch_audit_entries(DB_PATH, limit=20)
            try:
                probes = await rt.generate_batch(
                    current_policy,
                    [a.get("raw", a) for a in fresh_audits],
                    previously_attempted,
                )
            except Exception as exc:
                log.error("generate_batch failed at iteration %d: %r", iteration, exc)
                await BUS.publish({
                    "type": "redteam_iteration_failed", "job_id": job_id,
                    "iteration": iteration, "reason": f"{type(exc).__name__}: {exc}"[:200],
                })
                break
            if not probes:
                # Saturation: model couldn't propose new attacks.
                await BUS.publish({
                    "type": "redteam_iteration_summary", "job_id": job_id,
                    "iteration": iteration, "n_probes": 0, "n_gaps": 0, "n_blocked": 0,
                    "cumulative_probes": total_probes, "cumulative_blocked": eligible_blocked,
                    "cumulative_gaps_closed": total_gaps_closed,
                    "coverage_pct": _coverage_pct(),
                })
                break

        await BUS.publish({
            "type": "redteam_iteration_started", "job_id": job_id,
            "iteration": iteration, "n_probes": len(probes),
            "source": "demo_sequence" if iteration == 1 else "generate_batch",
        })

        iter_gaps = 0
        iter_blocked = 0
        regen_failed = False
        for probe in probes:
            # I3 fix: client-side dedup. Hash the full prompt (not truncated) so two
            # attacks that share a 200-char prefix but differ later aren't conflated.
            key = hashlib.sha256(probe.prompt.encode("utf-8")).hexdigest()[:16]
            if key in attempted_hashes:
                log.info("redteam skipping duplicate probe (iter %d, hash %s)", iteration, key)
                continue
            attempted_hashes.add(key)
            previously_attempted.append(probe.prompt[:200])
            total_probes += 1
            is_attack = probe.expected_verdict in _BLOCKED_CLASS
            await BUS.publish({
                "type": "redteam_probe_started", "job_id": job_id,
                "iteration": iteration, "probe": probe.model_dump(),
            })
            result = await rt.fire(probe)
            await BUS.publish({
                "type": "redteam_probe_result", "job_id": job_id,
                "iteration": iteration,
                "result": {
                    "probe": probe.model_dump(),
                    "actual_verdict": result.actual_verdict,
                    "is_gap": result.is_gap,
                },
            })
            # Count toward coverage only for attack-class probes that the firewall
            # actually got a verdict on (i.e. not infrastructure ERROR).
            if is_attack and result.actual_verdict != "ERROR":
                eligible_probes += 1
            if result.is_gap:
                iter_gaps += 1
                patched = await _patch_policy(job_id, gap_evidence={
                    "attack_prompt": probe.prompt,
                    "expected": probe.expected_verdict,
                    "actual": result.actual_verdict,
                })
                if not patched:
                    # Phase-11 deep-review I10: don't fire the next probe against
                    # the OLD vulnerable policy.
                    await BUS.publish({
                        "type": "redteam_aborted", "job_id": job_id,
                        "reason": "regen_failed", "iteration": iteration,
                    })
                    regen_failed = True
                    break
                total_gaps_closed += 1
                # Give LT a moment to fully come up after hot-reload.
                await asyncio.sleep(2)
            elif is_attack and result.actual_verdict in _BLOCKED_CLASS:
                iter_blocked += 1
                eligible_blocked += 1

        coverage_pct = _coverage_pct()
        await BUS.publish({
            "type": "redteam_iteration_summary", "job_id": job_id,
            "iteration": iteration,
            "n_probes": len(probes), "n_gaps": iter_gaps, "n_blocked": iter_blocked,
            "cumulative_probes": total_probes, "cumulative_blocked": eligible_blocked,
            "cumulative_gaps_closed": total_gaps_closed,
            "coverage_pct": coverage_pct,
        })

        if regen_failed:
            return
        if iter_gaps == 0:
            log.info("redteam saturated at iteration %d, coverage=%d%%", iteration, coverage_pct)
            await BUS.publish({
                "type": "redteam_loop_complete", "job_id": job_id,
                "reason": "saturated", "iterations": iteration,
                "coverage_pct": coverage_pct,
                "cumulative_probes": total_probes, "cumulative_blocked": eligible_blocked,
                "cumulative_gaps_closed": total_gaps_closed,
            })
            return

    # Reached max_iterations with gaps still being closed each round.
    coverage_pct = _coverage_pct()
    log.info("redteam hit max_iterations=%d, coverage=%d%%", max_iterations, coverage_pct)
    await BUS.publish({
        "type": "redteam_loop_complete", "job_id": job_id,
        "reason": "max_iterations", "iterations": max_iterations,
        "coverage_pct": coverage_pct,
        "cumulative_probes": total_probes, "cumulative_blocked": eligible_blocked,
        "cumulative_gaps_closed": total_gaps_closed,
    })


async def _patch_policy(job_id: str, gap_evidence: dict) -> bool:
    """Regenerate the policy with gap evidence, redeploy if validation passes.
    Returns True if the regen succeeded and a fresh policy is live; False otherwise.
    Caller should not fire the next probe on False (Phase-11 deep-review I10)."""
    job_dir = ARTIFACTS / job_id
    tree = PolicyTree.model_validate_json((job_dir / "policy_tree.json").read_text())
    prev_yaml = (job_dir / "policy.yaml").read_text()
    await BUS.publish({"type": "synthesizer_progress", "job_id": job_id, "status": "regenerating"})
    # C2 fix (deep-check 2026-05-13): regenerate() now raises SynthesizerGateError on
    # terminal validation failure (previously returned passed=False which we then
    # deployed). Catch it, surface to dashboard, keep the previous policy live.
    try:
        syn = await Synthesizer().regenerate(tree, gap_evidence, prev_yaml)
    except SynthesizerGateError as e:
        log.exception("regen gate failed for job %s", job_id)
        await BUS.publish({
            "type": "synthesizer_progress", "job_id": job_id, "status": "regen_failed",
            "summary": e.test_summary,
        })
        await BUS.publish({
            "type": "pipeline_error", "job_id": job_id,
            "stage": "regenerate", "error": str(e)[:300], "test_summary": e.test_summary,
        })
        return False
    if not syn.passed:
        # Belt-and-braces: regenerate() should now raise instead of returning passed=False,
        # but keep this branch in case a future caller bypasses the raise contract.
        await BUS.publish({
            "type": "synthesizer_progress", "job_id": job_id, "status": "regen_failed",
            "summary": syn.test_results_summary,
        })
        return False
    (job_dir / "policy.yaml").write_text(syn.output.yaml_text)
    # Phase-11 deep-review C2 (dashboard): clear prior YAML + emit a second
    # `synthesizer_progress.completed` so the dashboard's YAML streamer re-fires
    # for the regenerated policy (demo beat 9 — "auto-patch visible"). Also bump
    # the policy hash so the audit-defensibility badge shows the new SHA.
    await BUS.publish({"type": "yaml_reset", "job_id": job_id})
    await BUS.publish({
        "type": "synthesizer_progress", "job_id": job_id, "status": "completed",
        "passed": True,
    })
    new_sha = hashlib.sha256(syn.output.yaml_text.encode("utf-8")).hexdigest()[:12]
    await update_job(DB_PATH, job_id, policy_sha256=new_sha)
    await _redeploy(job_id, job_dir / "policy.yaml")
    await BUS.publish({"type": "policy_hash", "job_id": job_id, "sha256": new_sha})
    await BUS.publish({"type": "lobstertrap_reloaded", "job_id": job_id})
    return True
