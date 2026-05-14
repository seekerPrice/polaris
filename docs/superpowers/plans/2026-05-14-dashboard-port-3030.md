# Dashboard Port Move (3000 → 3030) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Polaris dashboard from `:3000` (which collides with Lucas's other dev apps) to a dedicated `:3030`, deterministically, across every script and doc that references it.

**Architecture:** Mechanical port substitution. `:3000` only appears in dashboard-facing references — the FastAPI on `:8000`, the OpenAI shim on `:11434`, and the LT proxy on `:8080` are unchanged. The dashboard talks to the API via `NEXT_PUBLIC_API_BASE` (still `:8000`), so no inter-service URL changes. The change touches 7 files: 2 scripts, 4 docs, 1 comment in `polaris/api/server.py`.

**Tech Stack:** bash (run_demo.sh, capture_thumbnail.sh), Markdown (README + docs), Python comment (server.py).

**Why 3030:** uncommon for dev tools (3000 = Next/React/Express/Rails/Grafana, 4000 = Phoenix, 5000 = Flask, 8080 = LT). 3030 is rarely defaulted by anything.

---

## File Inventory

Files touched (all references to `:3000` / `localhost:3000` / `PORT=3000`):

| File | Lines | What |
|---|---|---|
| `scripts/run_demo.sh` | 23, 24, 43, 47, 63, 65 | port-collision warn comments, `PORT=3000 npm run dev`, readiness probe, "stack ready" message |
| `scripts/capture_thumbnail.sh` | 10, 25, 26, 84 | usage comment, sanity-check curl, error message, manual-fallback help text |
| `README.md` | 93 | "Open http://localhost:3000" instruction |
| `CLAUDE.md` | 226 | "dashboard :3000" + "Open http://localhost:3000" reproducible-run blurb |
| `docs/RECORDING_NOTES.md` | 10 | recording prep checklist: "Browser windows: localhost:3000" |
| `docs/DEMO_SCRIPT.md` | 13 | "Polaris dashboard open in Chromium full-screen at localhost:3000" |
| `docs/PITCH_DECK.md` | 49 | slide caption "Single full-bleed screenshot of localhost:3000 mid-demo" |
| `polaris/api/server.py` | 49 | CORS comment: `["http://localhost:3000"]` post-hackathon allowlist hint |
| `dashboard/README.md` | 17 | Next.js scaffold default text (low-priority — never read; include for consistency) |

NOT touched (verified clean):
- `polaris/api/routes.py`, `polaris/api/state.py`, `dashboard/lib/api.ts` — no `:3000` references
- `docs/BUILD_PLAYBOOK.md`, `docs/SUBMISSION.md`, `KICKOFF.md` — verified no `:3000` references
- `scripts/capture_replay.sh`, `scripts/verify_live.sh`, `scripts/preflight.sh`, `scripts/prewarm.sh` — verified no `:3000` references
- `next.config.ts`, `package.json` — no hard-coded port

---

## Task 1: Update `scripts/run_demo.sh`

**Files:**
- Modify: `scripts/run_demo.sh:23-65`

- [ ] **Step 1: Edit run_demo.sh — replace all `:3000` → `:3030`**

Replace `PORT=3000` with `PORT=3030`. Replace `:3000` strings in comments + readiness probe + "stack ready" message.

After edit, `scripts/run_demo.sh` should contain (relevant lines):
```bash
# L33 fix (deep-check 2026-05-13): probe ALL three ports we need (:3030 dashboard,
# :8000 api, :11434 shim). Previously only :3030 was checked; an Ollama install on
# :11434 (default) would silently take over our shim port and the demo would fail
# with the wrong stack listening on :11434.
if command -v lsof >/dev/null; then
  for port in 3030 8000 11434; do
    ...
```
And:
```bash
( cd dashboard && PORT=3030 npm run dev ) &
```
And:
```bash
wait_for_http "dashboard :3030" "http://127.0.0.1:3030/"
echo "polaris stack ready — api :8000, shim :11434 (loopback-only), dashboard :3030"
```

- [ ] **Step 2: Verify no `:3000` remains in `scripts/run_demo.sh`**

Run: `grep -n ':3000\|PORT=3000' scripts/run_demo.sh`
Expected: no output.

---

## Task 2: Update `scripts/capture_thumbnail.sh`

**Files:**
- Modify: `scripts/capture_thumbnail.sh:10, 25-26, 84`

- [ ] **Step 1: Edit capture_thumbnail.sh — replace all `:3000` / `localhost:3000` → `:3030` / `localhost:3030`**

The script's sanity check on line 25 (`if ! curl -sf http://localhost:3000 >/dev/null 2>&1`) must point at the new port.

- [ ] **Step 2: Verify no `:3000` / `localhost:3000` remains**

Run: `grep -n '3000' scripts/capture_thumbnail.sh`
Expected: no output.

---

## Task 3: Update top-level docs (`README.md`, `CLAUDE.md`)

**Files:**
- Modify: `README.md:93`
- Modify: `CLAUDE.md:226`

- [ ] **Step 1: Edit README.md line 93**

Change `Open `http://localhost:3000`` to `Open `http://localhost:3030``.

- [ ] **Step 2: Edit CLAUDE.md line 226**

Two replacements on that line: `dashboard :3000` → `dashboard :3030` and `Open http://localhost:3000` → `Open http://localhost:3030`.

- [ ] **Step 3: Verify**

Run: `grep -n ':3000\|localhost:3000' README.md CLAUDE.md`
Expected: no output.

---

## Task 4: Update docs in `docs/`

**Files:**
- Modify: `docs/RECORDING_NOTES.md:10`
- Modify: `docs/DEMO_SCRIPT.md:13`
- Modify: `docs/PITCH_DECK.md:49`

- [ ] **Step 1: Edit each file — replace `localhost:3000` → `localhost:3030`**

These are caption / checklist mentions; same substitution.

- [ ] **Step 2: Verify**

Run: `grep -rn ':3000\|localhost:3000' docs/`
Expected: no output.

---

## Task 5: Update remaining references (`polaris/api/server.py`, `dashboard/README.md`)

**Files:**
- Modify: `polaris/api/server.py:49`
- Modify: `dashboard/README.md:17`

- [ ] **Step 1: Edit polaris/api/server.py line 49**

Change the comment `["http://localhost:3000"]` → `["http://localhost:3030"]` so post-hackathon CORS-allowlist guidance is consistent.

- [ ] **Step 2: Edit dashboard/README.md line 17**

Change `http://localhost:3000` → `http://localhost:3030` (twice on the same line — the URL and the markdown link). Low priority but maintains consistency.

- [ ] **Step 3: Final repo-wide verification**

Run:
```bash
grep -rn --color=never -E '(:3000|localhost:3000|PORT=3000)' \
  --include='*.md' --include='*.sh' --include='*.py' --include='*.ts' --include='*.tsx' --include='*.json' --include='*.mjs' \
  . 2>/dev/null | grep -v node_modules | grep -v '\.next/' | grep -v '\.deep-check/' | grep -v 'superpowers/plans/'
```
Expected: no output (the plan file in `docs/superpowers/plans/` is the only place 3000 is referenced as a literal, and grep excludes it).

---

## Task 6: Live verification

**Files:** none modified — runs the demo stack to confirm the port move works end-to-end.

- [ ] **Step 1: Kill any orphans on the new + old ports**

```bash
lsof -ti :3000 :3030 :8000 :8080 :11434 2>/dev/null | xargs kill -9 2>/dev/null
pkill -f "uvicorn polaris" 2>/dev/null
pkill -f "bin/lobstertrap" 2>/dev/null
pkill -f "next dev" 2>/dev/null
sleep 1
```

- [ ] **Step 2: Load `.env` so `GEMINI_API_KEY` is set**

```bash
set -a && source .env && set +a
[[ -n "${GEMINI_API_KEY:-}" ]] && echo "GEMINI_API_KEY: ok" || echo "GEMINI_API_KEY: MISSING"
```
Expected: `GEMINI_API_KEY: ok`.

- [ ] **Step 3: Start the stack**

```bash
./scripts/run_demo.sh
```

Expected output (in order):
1. `[run_demo] shim    :11434 ready (N)` (small N)
2. `[run_demo] api     :8000 ready (N)`
3. `[run_demo] dashboard :3030 ready (N)`
4. `polaris stack ready — api :8000, shim :11434 (loopback-only), dashboard :3030`

NOT expected:
- `WARNING: port :3000 already in use` (we're not using :3000 anymore)
- `Failed to start server: EADDRINUSE` on Next.js
- `LT startup spawn failed`

- [ ] **Step 4: Smoke-test the dashboard**

Open `http://localhost:3030` in the browser. Confirm:
- Tab title reads "Polaris — AI Agent Firewall"
- KPI row + 4-panel grid render
- No console errors (DevTools → Console)

- [ ] **Step 5: Stop the stack**

`Ctrl-C` in the run_demo terminal. Verify the trap cleans up:
```bash
lsof -i :3030 -i :8000 -i :8080 -i :11434
```
Expected: no output (clean teardown).

---

## Task 7: Commit

- [ ] **Step 1: Stage and commit**

```bash
git add scripts/run_demo.sh scripts/capture_thumbnail.sh \
        README.md CLAUDE.md \
        docs/RECORDING_NOTES.md docs/DEMO_SCRIPT.md docs/PITCH_DECK.md \
        polaris/api/server.py dashboard/README.md \
        docs/superpowers/plans/2026-05-14-dashboard-port-3030.md
git commit -m "$(cat <<'EOF'
chore: move dashboard from :3000 to :3030

:3000 collides with other dev apps on the recording machine. The new
:3030 is uncommon enough to be stable across machines. Pure config /
doc change — no functional impact on the API (:8000), shim (:11434),
or LT (:8080) ports.

Touched: scripts/run_demo.sh, scripts/capture_thumbnail.sh, README.md,
CLAUDE.md, docs/{RECORDING_NOTES,DEMO_SCRIPT,PITCH_DECK}.md,
polaris/api/server.py (CORS comment), dashboard/README.md.

Verified: ./scripts/run_demo.sh brings up the full stack on the new
port; dashboard renders at http://localhost:3030; no :3000 references
remain in tracked files.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review (run after writing — done)

- **Spec coverage**: every touchpoint from the user's instruction is mapped to a task (run_demo, verify_live [no refs found, verified clean], README, BUILD_PLAYBOOK [no refs], PITCH_DECK, KICKOFF [no refs], capture_thumbnail, capture_replay [no refs]). 7 files touched, all bound to tasks.
- **Placeholder scan**: no TBDs, no "add appropriate X", every step has the actual substitution.
- **Type consistency**: N/A (no types involved; pure string substitution).
- **Gaps**: Plan covers the operational verification (Task 6) so we catch any miss in step 3's grep.
