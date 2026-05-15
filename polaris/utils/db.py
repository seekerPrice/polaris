from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import aiosqlite

log = logging.getLogger(__name__)

# update_job() builds SQL from caller kwargs; restrict to known mutable columns so a
# stray kwarg name can't accidentally update `id` / `created_at` or hit a non-existent
# column. Defense-in-depth — values are still parameterised, so this guards intent not
# injection.
_UPDATABLE_JOB_FIELDS = frozenset({
    "source_filename", "policy_tree_json", "policy_yaml",
    "declared_intents_json", "status", "policy_sha256",
})


@asynccontextmanager
async def _connect(path: Path) -> AsyncIterator[aiosqlite.Connection]:
    """Open aiosqlite with WAL-friendly settings every caller needs.

    busy_timeout is connection-scoped; if record_job / record_audit_entry / update_job
    each opened plain connections they wouldn't inherit init_db's pragma and would hit
    'database is locked' under Red Team burst load.

    Usage:  async with _connect(path) as db: ...
    (The previous `async with await _connect(...) as db` shape started the connection's
    background thread twice — once via the `await`, once via `__aenter__` — and aiosqlite
    raised `threads can only be started once`. Wrapping in `@asynccontextmanager` ensures
    the connection lifecycle is owned by exactly one `async with`.)
    """
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA busy_timeout=30000")
        yield db


_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  source_filename TEXT NOT NULL,
  policy_tree_json TEXT,
  policy_yaml TEXT,
  declared_intents_json TEXT,
  status TEXT NOT NULL,
  policy_sha256 TEXT
);
-- Phase-11 T1.B4: add policy_sha256 column to existing tables (no-op if column already exists).
-- SQLite doesn't have ADD COLUMN IF NOT EXISTS, so we run conditionally below in init_db.
CREATE TABLE IF NOT EXISTS audit_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT,
  ts TEXT NOT NULL,
  verdict TEXT,
  matched_rule TEXT,
  raw_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gaps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  detected_at INTEGER NOT NULL,
  attack_category TEXT,
  prompt TEXT,
  resolved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_audit_job ON audit_entries(job_id);
-- L32 fix (deep-check 2026-05-13): gap queries filter by job_id; add the index.
CREATE INDEX IF NOT EXISTS idx_gaps_job ON gaps(job_id);
-- Phase-12 T1: SOC 2 CC8.1 chain of custody. APPEND-ONLY — each approve/reject
-- is its own row. Critical-reviewer 2026-05-15 Issue 1: prior draft used
-- INSERT OR REPLACE + UNIQUE(job_id, policy_sha) which silently overwrote
-- rejections, breaking the regulator-readable audit chain.
CREATE TABLE IF NOT EXISTS policy_deploys (
  deploy_id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  policy_sha TEXT NOT NULL,
  approver TEXT NOT NULL,
  approved INTEGER NOT NULL,           -- 1=approved, 0=rejected
  reason TEXT,                          -- non-null only on rejection
  decided_at REAL NOT NULL,
  deployed_at REAL                      -- non-null only on approved
);
CREATE INDEX IF NOT EXISTS idx_policy_deploys_job ON policy_deploys(job_id, decided_at);
"""


async def init_db(path: Path) -> None:
    async with aiosqlite.connect(path) as db:
        # Phase-11 deep-review I2 (api): enable WAL mode + busy_timeout so concurrent
        # writes from `record_audit_entry` + `record_job` + `update_job` don't deadlock
        # under Red Team burst load. Without these, SQLite uses journal mode with file
        # locks and bursts can produce "database is locked" errors that the audit pump
        # would swallow silently (now logged, but better not to hit them at all).
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=30000")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.executescript(_SCHEMA)
        # Phase-11 T1.B4: idempotently add policy_sha256 column to pre-existing DBs.
        # SQLite doesn't have IF NOT EXISTS for columns; only swallow the specific
        # "duplicate column" error so disk-full / DB-locked errors surface.
        try:
            await db.execute("ALTER TABLE jobs ADD COLUMN policy_sha256 TEXT")
        except aiosqlite.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
        await db.commit()


async def record_job(path: Path, job_id: str, source_filename: str, status: str = "pending") -> None:
    # INSERT OR IGNORE (not REPLACE): if a job_id collides we keep the original row
    # rather than wiping policy_tree_json / policy_yaml / policy_sha256 to NULL.
    async with _connect(path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO jobs(id, created_at, source_filename, status) VALUES (?,?,?,?)",
            (job_id, int(time.time()), source_filename, status),
        )
        await db.commit()


async def update_job(path: Path, job_id: str, **fields: Any) -> None:
    if not fields:
        return
    invalid = set(fields) - _UPDATABLE_JOB_FIELDS
    if invalid:
        raise ValueError(f"update_job rejects unknown column(s): {sorted(invalid)}")
    keys = ", ".join(f"{k}=?" for k in fields)
    async with _connect(path) as db:
        await db.execute(f"UPDATE jobs SET {keys} WHERE id=?", (*fields.values(), job_id))
        await db.commit()


async def record_audit_entry(path: Path, job_id: str | None, raw: dict) -> None:
    # L31 fix (deep-check 2026-05-13): `default=str` so a stray Path / datetime / set in
    # the raw payload doesn't crash the insert. Falls back to repr-ish string.
    async with _connect(path) as db:
        await db.execute(
            "INSERT INTO audit_entries(job_id, ts, verdict, matched_rule, raw_json) VALUES (?,?,?,?,?)",
            (job_id, raw.get("timestamp", ""), raw.get("verdict"), raw.get("matched_rule"), json.dumps(raw, default=str)),
        )
        await db.commit()


async def record_policy_deploy(
    path: Path,
    job_id: str,
    policy_sha: str,
    approver: str,
    approved: bool,
    decided_at: float,
    deployed_at: float | None,
    reason: str | None,
) -> None:
    """Append-only. Each approval/rejection is its own row in the chain of custody."""
    async with _connect(path) as db:
        await db.execute(
            "INSERT INTO policy_deploys "
            "(job_id, policy_sha, approver, approved, reason, decided_at, deployed_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (job_id, policy_sha, approver, int(approved), reason, decided_at, deployed_at),
        )
        await db.commit()


async def fetch_policy_deploys(path: Path, job_id: str | None = None, limit: int = 100) -> list[dict]:
    """Read the chain of custody. Filter by job_id when set; else most-recent first."""
    async with _connect(path) as db:
        if job_id is not None:
            sql = (
                "SELECT deploy_id, job_id, policy_sha, approver, approved, reason, "
                "decided_at, deployed_at FROM policy_deploys "
                "WHERE job_id = ? ORDER BY decided_at DESC LIMIT ?"
            )
            args = (job_id, limit)
        else:
            sql = (
                "SELECT deploy_id, job_id, policy_sha, approver, approved, reason, "
                "decided_at, deployed_at FROM policy_deploys "
                "ORDER BY decided_at DESC LIMIT ?"
            )
            args = (limit,)
        async with db.execute(sql, args) as cur:
            rows = await cur.fetchall()
    return [
        {
            "deploy_id": r[0],
            "job_id": r[1],
            "policy_sha": r[2],
            "approver": r[3],
            "approved": bool(r[4]),
            "reason": r[5],
            "decided_at": r[6],
            "deployed_at": r[7],
        }
        for r in rows
    ]


async def fetch_audit_entries(path: Path, limit: int = 100, offset: int = 0) -> list[dict]:
    async with _connect(path) as db:
        async with db.execute(
            "SELECT job_id, ts, verdict, matched_rule, raw_json FROM audit_entries "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cur:
            rows = await cur.fetchall()
    return [
        {
            "job_id": r[0],
            "ts": r[1],
            "verdict": r[2],
            "matched_rule": r[3],
            "raw": json.loads(r[4]),
        }
        for r in rows
    ]
