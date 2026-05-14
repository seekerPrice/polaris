#!/usr/bin/env bash
# Capture one full successful SSE event stream from a live run into
# dashboard/public/precomputed_run.json so Cmd+Shift+R can replay it
# offline if Gemini or Lobster Trap fails on stage.
#
# Usage:
#   1. Start the stack: ./scripts/run_demo.sh
#   2. In another terminal: bash scripts/capture_replay.sh examples/soc2_excerpt.pdf
#   3. Wait ~30s for Reader → Synthesizer → LT deploy → Red Team → reload
#   4. Press Ctrl-C to stop the capture; the JSON will be saved.
#
# The JSON file is consumed by dashboard/app/page.tsx's Cmd+Shift+R handler.

set -euo pipefail

PDF="${1:-examples/soc2_excerpt.pdf}"
OUT="dashboard/public/precomputed_run.json"

if [[ ! -f "$PDF" ]]; then
  echo "[capture_replay] missing input PDF: $PDF" >&2
  exit 1
fi

if ! curl -sf http://localhost:8000/api/audit-log >/dev/null; then
  echo "[capture_replay] Polaris API not up on :8000 — start the stack first (./scripts/run_demo.sh)" >&2
  exit 1
fi

echo "[capture_replay] uploading $PDF…"
JOB=$(curl -sf -F "file=@${PDF}" http://localhost:8000/api/policies/generate | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
if [ -z "${JOB:-}" ]; then
  echo "[capture_replay] failed to extract job_id from upload response" >&2
  exit 1
fi
echo "[capture_replay] job_id=$JOB"

mkdir -p "$(dirname "$OUT")"
TMP="$(mktemp)"
trap 'echo "[capture_replay] saving capture…"; python3 -c "import json,sys; raw=open(sys.argv[1]).read(); events=[json.loads(l[6:]) for l in raw.splitlines() if l.startswith(\"data: \")]; json.dump({\"job_id\": sys.argv[2], \"events\": events}, open(sys.argv[3], \"w\"), indent=2)" "$TMP" "$JOB" "$OUT"; rm -f "$TMP"; echo "[capture_replay] wrote $OUT ($(wc -l < "$OUT") lines)"' EXIT

echo "[capture_replay] streaming SSE → $TMP (Ctrl-C when Red Team finishes)…"
curl -N --no-buffer "http://localhost:8000/api/events" > "$TMP"
