from pathlib import Path

import pytest
from polaris.utils.db import (
    fetch_audit_entries,
    fetch_policy_deploys,
    init_db,
    record_audit_entry,
    record_job,
    record_policy_deploy,
    update_job,
)


@pytest.mark.asyncio
async def test_db_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    await init_db(db)
    await record_job(db, "job-1", "soc2.md", status="reading")
    await update_job(db, "job-1", policy_yaml="version: '1.0'", status="validated")
    await record_audit_entry(
        db,
        "job-1",
        {"timestamp": "2026-05-15T10:00:00Z", "verdict": "DENY", "matched_rule": "block_x"},
    )
    rows = await fetch_audit_entries(db)
    assert len(rows) == 1
    assert rows[0]["verdict"] == "DENY"
    assert rows[0]["raw"]["matched_rule"] == "block_x"


@pytest.mark.asyncio
async def test_policy_deploys_is_append_only(tmp_path: Path) -> None:
    """Reviewer-caught regression (2026-05-15 Issue 1): rejection-then-re-approval
    must preserve BOTH rows for the SOC 2 CC8.1 chain of custody."""
    db = tmp_path / "p.db"
    await init_db(db)

    # Same (job_id, policy_sha) — first rejected, then re-approved.
    await record_policy_deploy(
        db, "job-1", "deadbeef", "operator@polaris.demo",
        approved=False, decided_at=100.0, deployed_at=None, reason="missing CC7.2",
    )
    await record_policy_deploy(
        db, "job-1", "deadbeef", "operator@polaris.demo",
        approved=True, decided_at=200.0, deployed_at=200.5, reason=None,
    )

    rows = await fetch_policy_deploys(db, job_id="job-1")
    # Both rows preserved (NOT overwritten). Reverse-chronological order.
    assert len(rows) == 2
    assert rows[0]["approved"] is True
    assert rows[0]["decided_at"] == 200.0
    assert rows[1]["approved"] is False
    assert rows[1]["reason"] == "missing CC7.2"
