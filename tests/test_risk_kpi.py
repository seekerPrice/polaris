"""Phase 12 T2 — risk-reduction KPI tests.

Bonus criterion verbatim: "measurable risk reduction" (Veea brief).
"""
from __future__ import annotations

import pytest

from polaris.api.kpi import bucket_blocks, compute_risk_reduction


# ---------- compute_risk_reduction ----------

def test_risk_reduction_zero_when_no_audits():
    assert compute_risk_reduction([]) == 0.0


def test_risk_reduction_handles_all_allow():
    entries = [{"verdict": "ALLOW"}] * 5
    assert compute_risk_reduction(entries) == 0.0


def test_risk_reduction_handles_all_deny():
    entries = [{"verdict": "DENY"}] * 5
    assert compute_risk_reduction(entries) == 100.0


def test_risk_reduction_counts_quarantine_as_mitigated():
    entries = [
        {"verdict": "DENY"}, {"verdict": "QUARANTINE"},
        {"verdict": "ALLOW"}, {"verdict": "ALLOW"},
    ]
    # 2 of 4 resolved → 50%
    assert compute_risk_reduction(entries) == 50.0


def test_risk_reduction_excludes_human_review_from_denominator():
    """HUMAN_REVIEW is in-flight, not yet a resolved attempt."""
    entries = [{"verdict": "DENY"}, {"verdict": "ALLOW"}, {"verdict": "HUMAN_REVIEW"}]
    assert compute_risk_reduction(entries) == 50.0


def test_risk_reduction_ignores_unknown_verdicts():
    entries = [{"verdict": "DENY"}, {"verdict": "WEIRD"}, {"verdict": "ALLOW"}]
    # Only DENY + ALLOW resolved → 1 of 2 mitigated → 50%
    assert compute_risk_reduction(entries) == 50.0


def test_risk_reduction_rounds_to_one_decimal():
    entries = [{"verdict": "DENY"}, {"verdict": "DENY"}, {"verdict": "ALLOW"}]
    # 2/3 = 66.666… → 66.7
    assert compute_risk_reduction(entries) == 66.7


# ---------- bucket_blocks (T3 prep) ----------

def test_bucket_blocks_separates_exfiltration_via_flag():
    entries = [
        {"verdict": "DENY", "detected": {"contains_exfiltration": True}},
        {"verdict": "DENY", "detected": {"contains_injection_patterns": True}},
        {"verdict": "DENY", "detected": {"contains_system_commands": True}},
        {"verdict": "ALLOW", "detected": {}},
    ]
    b = bucket_blocks(entries)
    assert b["exfiltration"] == 1
    assert b["injection"] == 1
    assert b["other"] == 1
    assert b["total_blocked"] == 3


def test_bucket_blocks_separates_exfiltration_via_paste_domain():
    entries = [
        {"verdict": "DENY", "detected": {"target_domains": ["pastebin.com"]}},
        {"verdict": "DENY", "detected": {"target_domains": ["transfer.sh"]}},
        {"verdict": "DENY", "detected": {"target_domains": ["api.openai.com"]}},
    ]
    b = bucket_blocks(entries)
    assert b["exfiltration"] == 2
    assert b["other"] == 1


def test_bucket_blocks_falls_back_to_metadata_key():
    """Some LT versions emit `metadata` instead of `detected` (reviewer Issue 3)."""
    entries = [
        {"verdict": "DENY", "metadata": {"contains_exfiltration": True}},
    ]
    b = bucket_blocks(entries)
    assert b["exfiltration"] == 1


def test_bucket_blocks_handles_role_impersonation_as_injection():
    entries = [
        {"verdict": "DENY", "detected": {"contains_role_impersonation": True}},
    ]
    b = bucket_blocks(entries)
    assert b["injection"] == 1
