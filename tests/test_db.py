from pathlib import Path

import pytest
from polaris.utils.db import (
    fetch_audit_entries,
    init_db,
    record_audit_entry,
    record_job,
    update_job,
)


@pytest.mark.asyncio
async def test_db_round_trip(tmp_path: Path):
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
