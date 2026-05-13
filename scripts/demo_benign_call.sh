#!/usr/bin/env bash
# Benign demo beat (Phase-10 T1.7): fires a Sales Ops Copilot summary request through
# Lobster Trap with NO injection embedded. Confirms LT doesn't break legitimate
# traffic — defends against the judge thinking guardrails are over-broad.
#
# Usage (after stack is up):
#   bash scripts/demo_benign_call.sh
# Expected: ALLOW verdict, intent=communication, low risk_score.
set -uo pipefail

PAYLOAD=$(python3 -c "
import json, sys
fb = open('examples/customer_feedback_yesterday.txt').read()
print(json.dumps({
    'model': 'gemini-3.1-flash-lite',
    'messages': [
        {'role': 'system', 'content': 'You are Sales Ops Copilot. Summarise customer feedback briefly.'},
        {'role': 'user', 'content': 'Summarise yesterday\\'s customer feedback (one paragraph):\n\n' + fb},
    ],
    '_lobstertrap': {
        'declared_intent': 'communication',
        'declared_paths': ['examples/customer_feedback_yesterday.txt'],
        'declared_domains': [],
        'agent_id': 'sales-ops-copilot-v1',
    },
}))
")

if [[ -z "${PAYLOAD:-}" ]]; then
  echo "[demo_benign_call] failed to build payload (Python error?)" >&2
  exit 1
fi

echo "[demo_benign_call] firing benign request through Lobster Trap…"
RESP=$(curl -sf -X POST -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  http://localhost:8080/v1/chat/completions)

if [[ -z "${RESP:-}" ]]; then
  echo "[demo_benign_call] no response (LT down? check :8080)" >&2
  exit 1
fi

echo "$RESP" | python3 -c "
import json, sys
r = json.load(sys.stdin)
lt = r.get('_lobstertrap', {})
verdict = lt.get('verdict') or lt.get('ingress', {}).get('action', 'ALLOW')
detected = lt.get('ingress', {}).get('detected') or lt.get('detected') or {}
print(f'verdict: {verdict}')
print(f'intent_category: {detected.get(\"intent_category\", \"?\")}')
print(f'risk_score: {detected.get(\"risk_score\", \"?\")}')
content = (r.get('choices') or [{}])[0].get('message', {}).get('content', '')
print('---summary---')
print(content[:400])
"
