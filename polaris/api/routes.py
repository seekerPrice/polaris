from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

# Phase-11 T1.B3: default baseline policy deployed on Synth failure / startup before
# any compliance doc is uploaded. Known-safe; LT corpus 11/11 PASS verified.
_DEFAULT_BASELINE_POLICY = Path("./policies/default_baseline.yaml")

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
        # Phase-11 T1.B4: compute SHA-256 of the deployed YAML for audit-defensibility.
        policy_sha = hashlib.sha256(syn.output.yaml_text.encode("utf-8")).hexdigest()[:12]
        await update_job(DB_PATH, job_id, policy_sha256=policy_sha)
        await BUS.publish({"type": "policy_hash", "job_id": job_id, "sha256": policy_sha})
        await _redeploy(job_id, job_dir / "policy.yaml")
    else:
        # Phase-11 T1.B3: Synth validation failed (3 retries exhausted). Deploy the
        # default baseline so the proxy doesn't end up in an undefined state. Surfaced
        # to the dashboard so the operator knows we fell back.
        if _DEFAULT_BASELINE_POLICY.exists():
            await BUS.publish({
                "type": "synthesizer_progress", "job_id": job_id,
                "status": "fell_back_to_baseline",
                "summary": "Synth validation failed; deploying policies/default_baseline.yaml",
            })
            await _redeploy(job_id, _DEFAULT_BASELINE_POLICY)


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
    async for entry in LT.tail_audit_log(generation=generation):
        raw = entry.raw
        # Phase-11: alias LT's snake-cased field names so the dashboard's TypeScript
        # `AuditEntry` type renders them. LT emits `metadata` + `declared_headers`; the
        # dashboard expects `detected` + `declared`. Pre-existing bug — the audit panel's
        # detected/declared sections never rendered because the field names didn't match.
        if "metadata" in raw and "detected" not in raw:
            raw["detected"] = raw["metadata"]
        if "declared_headers" in raw and "declared" not in raw:
            raw["declared"] = raw["declared_headers"]
        # Phase-11 T1.B1: augment with mismatches BEFORE persistence + publish so both
        # the DB row and the SSE event carry the field (was previously None always).
        # Two sources: LT's native (structured-object) emit, and our _compute_mismatches
        # fallback. LT-native is strictly more informative (severity tag, structured
        # declared/detected pair), so when it fires we use it AS-IS — skip the Polaris
        # fallback to avoid surfacing the same fact twice on the dashboard.
        lt_raw = raw.get("mismatches")
        if lt_raw:
            raw["mismatches"] = _normalize_mismatches(lt_raw)
        else:
            polaris_computed = _compute_mismatches(raw)
            if polaris_computed:
                raw["mismatches"] = polaris_computed
        await record_audit_entry(DB_PATH, job_id, raw)
        await BUS.publish({"type": "audit_log_entry", "job_id": job_id, "entry": raw})


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
