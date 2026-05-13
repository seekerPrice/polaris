#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "--reset" ]] && rm -f polaris.db && rm -rf artifacts/*

# Pre-flight on fresh clones: install dashboard deps once if missing.
if [[ ! -d dashboard/node_modules ]]; then
  echo "[run_demo] installing dashboard deps (first run)…"
  ( cd dashboard && npm install --silent )
fi
# Stage the demo PDF for the dashboard's "Load demo SOC 2" button.
if [[ ! -f dashboard/public/sample-soc2.pdf && -f examples/soc2_excerpt.pdf ]]; then
  echo "[run_demo] staging examples/soc2_excerpt.pdf → dashboard/public/sample-soc2.pdf"
  cp examples/soc2_excerpt.pdf dashboard/public/sample-soc2.pdf
fi
if [[ ! -x ./bin/lobstertrap ]]; then
  echo "[run_demo] lobstertrap binary missing — running download script first"
  ./scripts/download_lobstertrap.sh
fi
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "[run_demo] WARNING: GEMINI_API_KEY is not set — agent calls will fail."
fi

# Warn if port 3000 is already taken — Next.js silently picks 3001 if the default is in
# use, which would break the dashboard URL during recording.
if command -v lsof >/dev/null && lsof -ti:3000 >/dev/null 2>&1; then
  echo "[run_demo] WARNING: port 3000 already in use — dashboard may bind elsewhere; recording will break."
fi

trap 'kill 0' EXIT
uv run uvicorn polaris.utils.openai_gemini_shim:app --port 11434 &
uv run uvicorn polaris.api.server:app --port 8000 &
( cd dashboard && PORT=3000 npm run dev ) &
echo "polaris stack: api 8000, shim 11434, dashboard 3000"
wait
