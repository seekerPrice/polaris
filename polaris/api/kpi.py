"""Phase 12 T2/T3 — risk-reduction and attack-bucket metrics.

Bonus criteria the hackathon brief lists verbatim:
  - "measurable risk reduction"     → compute_risk_reduction
  - "caught exfiltration"           → bucket_blocks split exfiltration vs injection

Server-side reference logic. The dashboard mirrors this in TypeScript for
instant updates on each audit SSE event; this module is the canonical source.
"""
from __future__ import annotations


_MITIGATING = frozenset({"DENY", "QUARANTINE"})
_RESOLVED = frozenset({"DENY", "ALLOW", "QUARANTINE", "LOG"})

_EXFIL_DOMAINS = frozenset({
    "pastebin.com", "transfer.sh", "requestbin.com", "requestbin.net",
})


def compute_risk_reduction(audit_entries: list[dict]) -> float:
    """Percentage (0.0..100.0) of RESOLVED policy decisions that mitigated risk.

    Resolved = DENY / ALLOW / QUARANTINE / LOG (excludes HUMAN_REVIEW which is
    in-flight). Mitigated = DENY or QUARANTINE (the verdicts that actually
    prevent execution). Empty list → 0.0. Rounded to one decimal."""
    resolved = [e for e in audit_entries if e.get("verdict") in _RESOLVED]
    if not resolved:
        return 0.0
    mitigated = sum(1 for e in resolved if e["verdict"] in _MITIGATING)
    return round(100.0 * mitigated / len(resolved), 1)


def _metadata_of(entry: dict) -> dict:
    """LT format uses `detected` for DPI metadata; some versions emit `metadata`.
    Mirror the fallback chain used by _compute_mismatches in routes.py:356."""
    md = entry.get("detected") or entry.get("metadata") or {}
    return md if isinstance(md, dict) else {}


def bucket_blocks(audit_entries: list[dict]) -> dict[str, int]:
    """Split DENY entries by attack class for the per-bucket KPI tiles.
    Exfiltration is identified by contains_exfiltration flag OR target_domains
    listing a known paste-site. Injection by contains_injection_patterns OR
    contains_role_impersonation. Everything else lands in 'other'."""
    out = {"exfiltration": 0, "injection": 0, "other": 0, "total_blocked": 0}
    for e in audit_entries:
        if e.get("verdict") != "DENY":
            continue
        out["total_blocked"] += 1
        md = _metadata_of(e)
        target_doms = md.get("target_domains") or []
        if md.get("contains_exfiltration") or any(d in _EXFIL_DOMAINS for d in target_doms):
            out["exfiltration"] += 1
        elif md.get("contains_injection_patterns") or md.get("contains_role_impersonation"):
            out["injection"] += 1
        else:
            out["other"] += 1
    return out
