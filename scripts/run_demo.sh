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

# L33 fix (deep-check 2026-05-13): probe ALL three ports we need (:3030 dashboard,
# :8000 api, :11434 shim). Previously only :3030 was checked; an Ollama install on
# :11434 (default) would silently take over our shim port and the demo would fail
# with the wrong stack listening on :11434.
if command -v lsof >/dev/null; then
  for port in 3030 8000 11434; do
    if lsof -ti:"$port" >/dev/null 2>&1; then
      pid=$(lsof -ti:"$port" | head -1)
      echo "[run_demo] WARNING: port :$port already in use by pid $pid — Polaris may bind elsewhere or fail to start."
    fi
  done
fi

trap 'kill 0' EXIT
# C3 fix (deep-check 2026-05-13): bind shim explicitly to 127.0.0.1 — never 0.0.0.0.
# The shim is the trust boundary; any non-loopback listener is a firewall bypass.
# The shim's middleware also rejects non-loopback peers; the explicit --host is
# defense in depth so a stray config can't expose it on conference Wi-Fi.
uv run uvicorn polaris.utils.openai_gemini_shim:app --host 127.0.0.1 --port 11434 &
uv run uvicorn polaris.api.server:app --port 8000 &
( cd dashboard && PORT=3030 npm run dev ) &

# H14 fix (deep-check 2026-05-13): poll each service's readiness before printing
# "stack ready". Previously the message fired the moment the processes spawned,
# meaning Lucas could open the browser before Next.js had bound :3030 and hit a
# 404 on the recording. Pattern lifted from scripts/verify_live.sh.
wait_for_http() {
  local label="$1"; local url="$2"; local tries=60
  for ((i=1; i<=tries; i++)); do
    if curl -sf -o /dev/null -m 1 "$url"; then
      echo "[run_demo] $label ready ($i)"
      return 0
    fi
    sleep 0.5
  done
  echo "[run_demo] WARNING: $label not ready at $url after $((tries/2))s"
  return 1
}
wait_for_http "shim    :11434" "http://127.0.0.1:11434/healthz"
wait_for_http "api     :8000"  "http://127.0.0.1:8000/api/audit-log?limit=1"
wait_for_http "dashboard :3030" "http://127.0.0.1:3030/"

echo "polaris stack ready — api :8000, shim :11434 (loopback-only), dashboard :3030"
wait
