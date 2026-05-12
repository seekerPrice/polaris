from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from polaris.agents.reader import PolicyTree


def render_compliance_report(tree: PolicyTree, audit_entries: list[dict], out_path: Path) -> None:
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("<b>POLARIS COMPLIANCE REPORT</b>", styles["Title"]),
        Paragraph(f"Policy: {tree.policy_name}", styles["Normal"]),
        Paragraph(f"Source: {tree.source_document}", styles["Normal"]),
        Paragraph(
            f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            styles["Normal"],
        ),
        Spacer(1, 24),
        Paragraph("<b>Control mapping</b>", styles["Heading2"]),
    ]
    rows: list[list[str]] = [["ID", "Section", "Control type", "Severity", "Suggested action"]]
    for r in tree.requirements:
        rows.append([r.id, r.section, r.control_type, r.severity, r.suggested_action])
    t = Table(rows, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    flow.append(t)

    flow.append(Spacer(1, 24))
    flow.append(Paragraph("<b>Enforcement evidence (last 10 DENYs)</b>", styles["Heading2"]))
    denies = [a for a in audit_entries if a.get("verdict") == "DENY"][:10]
    if not denies:
        flow.append(Paragraph("(none yet — system has not blocked any traffic)", styles["Normal"]))
    for d in denies:
        flow.append(Paragraph(
            f"{d.get('timestamp','')} — rule={d.get('matched_rule','')}",
            styles["Code"],
        ))

    doc = SimpleDocTemplate(str(out_path), pagesize=letter)
    doc.build(flow)
