from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

import yaml
from reportlab.lib import colors


# H11 fix (deep-check 2026-05-13): ReportLab's Paragraph parses an HTML-like markup.
# Any `<` or `&` in PDF-extracted text crashes rendering or produces garbled output.
# Wrap every dynamic interpolation through this helper before it lands in a Paragraph.
def _esc(s: Any) -> str:
    return _xml_escape(str(s)) if s is not None else ""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from polaris.agents.reader import PolicyTree


# Phase-10 T1.4: regulatory urgency callouts. Map source-document substrings to a
# short reminder line printed on the cover page. Triggers if any requirement's
# `section` contains a key (case-insensitive).
_REGULATORY_DEADLINES: list[tuple[str, str]] = [
    ("eu ai act", "EU AI Act high-risk obligations take effect August 2026."),
    ("gdpr", "GDPR enforcement is continuous; pseudonymisation and erasure obligations apply."),
    ("hipaa", "HIPAA Security Rule requires audit logs of all PHI access (45 CFR 164.312)."),
    ("colorado ai act", "Colorado AI Act (CAIA) enforceable June 2026."),
    ("nist ai rmf", "NIST AI RMF GOVERN-3.2 / MEASURE-2.6 require human-in-the-loop on high-risk."),
    ("soc 2", "SOC 2 Type II audit windows are typically 6-12 months — start enforcement now."),
    ("owasp llm", "OWASP LLM Top 10 (2025) — LLM01-LLM10 directly addressed by ingress + egress DPI."),
]


def _collect_rules(policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ingress_rules + egress_rules as a flat list, preserving direction in a 'kind' key."""
    rules: list[dict[str, Any]] = []
    for kind in ("ingress_rules", "egress_rules"):
        for r in policy.get(kind) or []:
            if isinstance(r, dict):
                rules.append({**r, "_kind": kind})
    return rules


def _rule_fields(rule: dict[str, Any]) -> set[str]:
    """All metadata fields referenced in any of a rule's conditions."""
    fields: set[str] = set()
    for cond in rule.get("conditions") or []:
        if isinstance(cond, dict):
            f = cond.get("field")
            if isinstance(f, str):
                fields.add(f)
    return fields


def _map_requirements_to_rules(tree: PolicyTree, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """For each requirement, find rule(s) whose condition fields overlap with the
    requirement's `lobster_trap_fields`. Returns one row dict per requirement."""
    rows: list[dict[str, Any]] = []
    for req in tree.requirements:
        wanted = set(req.lobster_trap_fields)
        mapped: list[str] = []
        for r in rules:
            if wanted & _rule_fields(r):
                mapped.append(f"{r.get('name', '?')} ({r.get('_kind', '').replace('_rules', '')})")
        rows.append({
            "id": req.id,
            "section": req.section,
            "requirement": req.human_text[:140] + ("…" if len(req.human_text) > 140 else ""),
            "severity": req.severity,
            "suggested_action": req.suggested_action,
            "mapped_rules": mapped,
        })
    return rows


def _regulatory_urgency_lines(tree: PolicyTree) -> list[str]:
    needles = " ".join([tree.policy_name.lower(), tree.source_document.lower(),
                        " ".join(r.section.lower() for r in tree.requirements)])
    return [line for key, line in _REGULATORY_DEADLINES if key in needles]


def render_compliance_report(
    tree: PolicyTree,
    audit_entries: list[dict],
    out_path: Path,
    policy_yaml: str | None = None,
) -> None:
    """Render a compliance PDF showing control→rule mapping, coverage %, gap report,
    and regulatory urgency callouts. Phase-10 T1.2 rewrite — was a flat dump of
    requirements + denied audit lines; now answers the auditor's actual question
    ('which controls are addressed by which rules, and what's missing?')."""
    styles = getSampleStyleSheet()
    callout = ParagraphStyle("Callout", parent=styles["Normal"], textColor=colors.HexColor("#b91c1c"))
    flow: list[Any] = []

    # ───── Cover ──────────────────────────────────────────────────────────
    flow.append(Paragraph("<b>POLARIS COMPLIANCE REPORT</b>", styles["Title"]))
    flow.append(Paragraph(f"Policy: <b>{_esc(tree.policy_name)}</b>", styles["Normal"]))
    flow.append(Paragraph(f"Source: {_esc(tree.source_document)}", styles["Normal"]))
    flow.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        styles["Normal"],
    ))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph("Estimated cost replaced: <b>$15,000–$36,000</b> per policy "
                          "(1–3 wks of compliance counsel + paralegal review at blended $150–300/hr)",
                          styles["Normal"]))

    urgency = _regulatory_urgency_lines(tree)
    if urgency:
        flow.append(Spacer(1, 12))
        flow.append(Paragraph("<b>Regulatory deadlines</b>", styles["Heading3"]))
        for line in urgency:
            flow.append(Paragraph(f"• {line}", callout))

    flow.append(Spacer(1, 24))

    # ───── Coverage summary + control→rule mapping ────────────────────────
    rules: list[dict[str, Any]] = []
    if policy_yaml:
        try:
            parsed = yaml.safe_load(policy_yaml)
            if isinstance(parsed, dict):
                rules = _collect_rules(parsed)
        except yaml.YAMLError:
            rules = []

    rows = _map_requirements_to_rules(tree, rules)
    n_total = len(rows)
    n_mapped = sum(1 for r in rows if r["mapped_rules"])
    coverage_pct = int(round(100 * n_mapped / max(n_total, 1)))

    flow.append(Paragraph(
        f"<b>Coverage:</b> {n_mapped}/{n_total} requirements addressed "
        f"(<b>{coverage_pct}%</b>) by {len(rules)} deployed rule(s).",
        styles["Heading2"],
    ))
    flow.append(Spacer(1, 8))

    if rows:
        table_rows: list[list[str]] = [["ID", "Section", "Severity", "Mapped rule(s)"]]
        for row in rows:
            mapped = "\n".join(row["mapped_rules"]) if row["mapped_rules"] else "— GAP —"
            # H11 fix (deep-check): escape <, & in PDF-extracted strings.
            table_rows.append([_esc(row["id"]), _esc(row["section"]), _esc(row["severity"].upper()), _esc(mapped)])
        t = Table(table_rows, hAlign="LEFT", colWidths=[55, 140, 60, 245])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        flow.append(t)

    # ───── Gap report ─────────────────────────────────────────────────────
    flow.append(Spacer(1, 24))
    flow.append(Paragraph("<b>Gap report</b>", styles["Heading2"]))
    gaps = [r for r in rows if not r["mapped_rules"]]
    if gaps:
        for g in gaps:
            flow.append(Paragraph(
                f"<b>{_esc(g['id'])}</b> ({_esc(g['section'])}, {_esc(g['severity'])}): {_esc(g['requirement'])}",
                styles["Normal"],
            ))
    else:
        flow.append(Paragraph("(no gaps — every requirement maps to at least one deployed rule)", styles["Normal"]))

    # ───── Enforcement evidence ───────────────────────────────────────────
    flow.append(Spacer(1, 24))
    flow.append(Paragraph("<b>Enforcement evidence (last 10 DENYs)</b>", styles["Heading2"]))
    # L6 fix (deep-check): sort by timestamp desc so the report shows the MOST recent
    # 10 DENYs, not whichever 10 happen to be at the head/tail of the caller's order.
    all_denies = [a for a in audit_entries if a.get("verdict") == "DENY"]
    denies = sorted(all_denies, key=lambda d: d.get("timestamp", ""), reverse=True)[:10]
    if not denies:
        flow.append(Paragraph("(none yet — system has not blocked any traffic)", styles["Normal"]))
    for d in denies:
        flow.append(Paragraph(
            f"{_esc(d.get('timestamp', ''))} — rule={_esc(d.get('matched_rule', ''))}",
            styles["Code"],
        ))

    doc = SimpleDocTemplate(str(out_path), pagesize=letter)
    doc.build(flow)


class AuditorAgent:
    """Renders compliance PDF reports mapping requirements to deployed rules.

    Per CLAUDE.md §6, every agent in polaris/agents/ is a class with a single
    async process() method. The actual rendering remains in render_compliance_report
    (used by polaris.api.routes); process() is a thin async shim so the four-agent
    set (Reader, Synthesizer, RedTeam, Auditor) is consistent.
    """

    async def process(
        self,
        tree: PolicyTree,
        audit_entries: list[dict],
        out_path: Path,
        policy_yaml: str | None = None,
    ) -> None:
        render_compliance_report(tree, audit_entries, out_path, policy_yaml=policy_yaml)
