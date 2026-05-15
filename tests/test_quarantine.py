"""Phase 12 T4 — QUARANTINE Review Queue tests.

Closes the 6/6 LT action coverage gap. Verifies:
- record_quarantine_decision is APPEND-ONLY-with-first-wins (UNIQUE on
  audit_entry_id; second insertion is a no-op signalled by False return).
- Synthesizer injects the QUARANTINE supplementary rule with the right
  conditions + threshold so LT-corpus benign prompts don't trip it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from polaris.agents.synthesizer import Synthesizer
from polaris.utils.db import (
    fetch_quarantine_decisions,
    init_db,
    record_quarantine_decision,
)


# ---------- DB layer ----------

@pytest.mark.asyncio
async def test_first_decision_wins(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    await init_db(db)

    inserted_1 = await record_quarantine_decision(db, 42, "RELEASE", "op@polaris", 1000.0)
    inserted_2 = await record_quarantine_decision(db, 42, "BLOCK",   "op@polaris", 1001.0)

    assert inserted_1 is True, "first decision should insert"
    assert inserted_2 is False, "second decision on same entry must be no-op"

    rows = await fetch_quarantine_decisions(db)
    assert len(rows) == 1
    assert rows[0]["decision"] == "RELEASE"


@pytest.mark.asyncio
async def test_decision_validation(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    await init_db(db)
    with pytest.raises(ValueError):
        await record_quarantine_decision(db, 1, "MAYBE", "op@polaris", 100.0)


@pytest.mark.asyncio
async def test_decisions_are_reverse_chronological(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    await init_db(db)
    await record_quarantine_decision(db, 1, "RELEASE", "op@polaris", 1000.0)
    await record_quarantine_decision(db, 2, "BLOCK",   "op@polaris", 1100.0)
    await record_quarantine_decision(db, 3, "RELEASE", "op@polaris",  900.0)

    rows = await fetch_quarantine_decisions(db)
    decided_ats = [r["decided_at"] for r in rows]
    assert decided_ats == sorted(decided_ats, reverse=True)


# ---------- Synthesizer rule injection ----------

def test_synthesizer_supplementary_rules_include_quarantine() -> None:
    """The QUARANTINE rule must be in the supplementary set so EVERY synthesised
    policy exercises the 6th LT action — independent of what the LLM emits."""
    names = {r["name"] for r in Synthesizer._SUPPLEMENTARY_RULES}
    assert "polaris_baseline_quarantine_borderline_credential" in names


def test_quarantine_rule_uses_quarantine_action() -> None:
    rule = next(
        r for r in Synthesizer._SUPPLEMENTARY_RULES
        if r["name"] == "polaris_baseline_quarantine_borderline_credential"
    )
    assert rule["action"] == "QUARANTINE"
    # Two AND'd conditions: credentials present AND risk_score elevated.
    fields = {c["field"] for c in rule["conditions"]}
    assert fields == {"contains_credentials", "risk_score"}
    # Threshold tuned to skip LT corpus benign prompts.
    risk_cond = next(c for c in rule["conditions"] if c["field"] == "risk_score")
    assert risk_cond["match_type"] == "threshold"
    assert risk_cond["value"] >= 0.65, "threshold must stay high enough for LT corpus"
