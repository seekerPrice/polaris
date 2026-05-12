#!/usr/bin/env bash
# Warm Gemini's response cache for the Synthesizer prompt before recording the demo.
# Per Phase 6.2 determinism pass — running the validation-gate spike 3× exercises
# gemini-3.1-pro-preview on the stripped synthesizer_agent.md prompt (the same code path
# Synthesizer.process uses), without re-deploying Lobster Trap each time.
set -uo pipefail
for i in 1 2 3; do
  echo "[prewarm] spike run $i/3 …"
  PYTHONPATH=. uv run python scripts/spike_validation_gate.py >/tmp/prewarm_$i.log 2>&1 && echo "  PASS" || echo "  FAIL — see /tmp/prewarm_$i.log"
done
echo "[prewarm] done — cache warmed; safe to record."
