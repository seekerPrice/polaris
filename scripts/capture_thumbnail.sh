#!/usr/bin/env bash
# Phase-11 T1.B7 — capture docs/img/demo_thumbnail.png from a live mid-demo dashboard.
# This thumbnail is referenced by README.md (image badge) and PITCH_DECK.md slide 1.
#
# Usage:
#   1. Bring up the stack: ./scripts/run_demo.sh
#   2. In another terminal: bash scripts/capture_thumbnail.sh
#   3. The script uploads the demo PDF, triggers Red Team, waits for the "money frame"
#      (audit panel populated + Red Team probes visible + compliance card ready), then
#      captures localhost:3000 to docs/img/demo_thumbnail.png.
#
# Manual fallback (if Chrome MCP isn't available):
#   - Cmd+Shift+4 (macOS) to draw a screenshot region over the dashboard at the right moment.
#   - Save as docs/img/demo_thumbnail.png at 1920x1080 or larger.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

OUT="docs/img/demo_thumbnail.png"
mkdir -p "$(dirname "$OUT")"

# Sanity checks
if ! curl -sf http://localhost:3000 >/dev/null 2>&1; then
  echo "[capture_thumbnail] dashboard not up on :3000 — start ./scripts/run_demo.sh first" >&2
  exit 1
fi
if ! curl -sf http://localhost:8000/api/audit-log >/dev/null 2>&1; then
  echo "[capture_thumbnail] Polaris API not up on :8000" >&2
  exit 1
fi

# Drive a full demo cycle so the dashboard is in its most photogenic state.
echo "[capture_thumbnail] uploading examples/soc2_excerpt.pdf…"
JOB=$(curl -sf -F "file=@examples/soc2_excerpt.pdf" http://localhost:8000/api/policies/generate \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "[capture_thumbnail] job=$JOB; waiting ~20s for pipeline + Red Team…"

# Wait for policy.yaml to land
for _ in $(seq 1 60); do
  if curl -sf "http://localhost:8000/api/policies/$JOB" \
       | python3 -c "import sys,json; sys.exit(0 if 'policy.yaml' in json.load(sys.stdin) else 1)"; then
    break
  fi
  sleep 1
done

# Trigger Red Team so probes appear
curl -sf -X POST "http://localhost:8000/api/redteam/start?job_id=$JOB" >/dev/null

# Wait long enough that probe 2 GAP + auto-patch + probe 3 DENY all land in the UI
sleep 35

# Capture. macOS native screencapture is most reliable; falls back to advice if not macOS.
if command -v screencapture >/dev/null 2>&1; then
  echo "[capture_thumbnail] capturing localhost:3000 to $OUT (please bring Chrome to focus and stay still)…"
  echo "[capture_thumbnail] 3 seconds to focus Chrome dashboard window…"
  sleep 3
  screencapture -t png -x -m "$OUT"
  echo "[capture_thumbnail] saved $OUT ($(du -h "$OUT" | cut -f1))"
else
  cat <<EOF >&2
[capture_thumbnail] screencapture not available (non-macOS host). Manual steps:
  1. Open http://localhost:3000 in Chrome with the dashboard mid-demo.
  2. Take a screenshot of the four panels (KPI row + upload + audit + Red Team + compliance).
  3. Save as $OUT at 1920x1080 or larger.
EOF
  exit 2
fi
