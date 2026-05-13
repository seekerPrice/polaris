#!/usr/bin/env bash
# Phase-10 T2.4 — pre-recording / pre-submission preflight check.
# Run before every demo recording attempt, and one final time before lablab.ai submission.
# All three stages must pass; this script exits non-zero on first failure.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "[preflight] (1/3) uv pytest — unit tests (excludes live e2e)…"
uv run pytest tests/ -q \
  --ignore=tests/test_e2e_block_injection.py \
  --ignore=tests/test_latency_60s.py \
  --ignore=tests/test_synthesizer_e2e.py \
  --ignore=tests/test_reader_e2e.py \
  --ignore=tests/test_redteam_e2e.py \
  --ignore=tests/test_compliance_pdf.py

echo "[preflight] (2/3) dashboard build…"
( cd dashboard && npm run build )

echo "[preflight] (3/3) live verify (latency + injection block)…"
bash scripts/verify_live.sh

echo "[preflight] ✅ all stages passed — safe to record / submit."
