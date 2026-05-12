#!/usr/bin/env bash
# Copy the demo SOC 2 PDF into the dashboard's public/ so the "Load demo SOC 2"
# button can fetch /sample-soc2.pdf without an extra API route.
set -euo pipefail
SRC="examples/soc2_excerpt.pdf"
DST="dashboard/public/sample-soc2.pdf"
if [[ ! -f "$SRC" ]]; then
  echo "[copy_demo_pdf] missing $SRC — run pyproject demo rendering first" >&2
  exit 1
fi
cp "$SRC" "$DST"
echo "[copy_demo_pdf] $SRC → $DST"
