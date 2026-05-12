#!/usr/bin/env bash
# Bring up shim + API + Lobster Trap, run the live e2e tests, tear down.
# Used in Phase 6 + Phase 7 fresh-clone validation.
#
# NOTE: NOT using `set -e` because we want both tests to run even if one fails,
# so we can report the full picture instead of bailing on the first non-zero exit.
set -uo pipefail

cleanup() {
  echo "[verify_live] tearing down…"
  jobs -p | xargs -I{} kill {} 2>/dev/null || true
  pkill -f "polaris.utils.openai_gemini_shim" 2>/dev/null || true
  pkill -f "polaris.api.server" 2>/dev/null || true
  pkill -f "bin/lobstertrap serve" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Reset state
rm -f polaris.db
rm -rf artifacts/*
mkdir -p artifacts/audit_logs

# Make sure binary + key are present
if [[ ! -x ./bin/lobstertrap ]]; then
  echo "[verify_live] lobstertrap missing — running download script"
  ./scripts/download_lobstertrap.sh
fi
if ! grep -q "^GEMINI_API_KEY=." .env 2>/dev/null && [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "[verify_live] FATAL: GEMINI_API_KEY not set (env or .env). Aborting." >&2
  exit 1
fi

# Spawn the two FastAPI servers
echo "[verify_live] starting shim on :11434…"
uv run uvicorn polaris.utils.openai_gemini_shim:app --port 11434 >/tmp/polaris_shim.log 2>&1 &
SHIM_PID=$!

echo "[verify_live] starting Polaris API on :8000…"
uv run uvicorn polaris.api.server:app --port 8000 >/tmp/polaris_api.log 2>&1 &
API_PID=$!

# Wait for both to be reachable
for port in 11434 8000; do
  for i in {1..30}; do
    if curl -sf "http://localhost:$port/healthz" >/dev/null 2>&1 \
       || curl -sf "http://localhost:$port/openapi.json" >/dev/null 2>&1 \
       || curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
      echo "[verify_live] :$port up"
      break
    fi
    sleep 0.5
    [[ $i -eq 30 ]] && { echo "[verify_live] :$port did not come up in 15s" >&2; cat /tmp/polaris_*.log; exit 1; }
  done
done

# Run the latency test against fresh state.
echo "[verify_live] running latency test (fresh state)…"
POLARIS_LIVE_E2E=1 uv run pytest tests/test_latency_60s.py -v -s
LATENCY_EXIT=$?

# Tear down + reset before the second test so Gemini rate limits recover and there's no
# state contention with the previous job's audit-tail task.
echo "[verify_live] resetting between tests…"
cleanup
sleep 5
rm -f polaris.db && rm -rf artifacts/* && mkdir -p artifacts/audit_logs

# Re-spawn the stack
echo "[verify_live] re-starting shim + API for injection test…"
uv run uvicorn polaris.utils.openai_gemini_shim:app --port 11434 >/tmp/polaris_shim2.log 2>&1 &
uv run uvicorn polaris.api.server:app --port 8000 >/tmp/polaris_api2.log 2>&1 &
for port in 11434 8000; do
  for i in {1..30}; do
    if curl -sf "http://localhost:$port/healthz" >/dev/null 2>&1 \
       || curl -sf "http://localhost:$port/openapi.json" >/dev/null 2>&1 \
       || curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
    [[ $i -eq 30 ]] && { echo "[verify_live] :$port did not come up in 15s" >&2; exit 1; }
  done
done

echo "[verify_live] running injection block test…"
POLARIS_LIVE_E2E=1 uv run pytest tests/test_e2e_block_injection.py -v -s
INJECTION_EXIT=$?

if [[ $LATENCY_EXIT -eq 0 && $INJECTION_EXIT -eq 0 ]]; then
  echo "[verify_live] OK — both tests passed (latency=$LATENCY_EXIT injection=$INJECTION_EXIT)"
else
  echo "[verify_live] FAIL — latency=$LATENCY_EXIT injection=$INJECTION_EXIT"
  exit 1
fi
