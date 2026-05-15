# Polaris — Anti-Pattern Registry

> **Mandatory growth rule (see `CLAUDE.md` §10 Hard rules):**
> Every fix commit MUST add or update one entry here BEFORE the commit lands.
> No exceptions. The whole point of the registry is to make Day-N+1 cheaper
> than Day-N. Entries decay if they aren't audited; lock the entry to the
> commit SHA that introduced the fix, not just the date.

## Index

| ID | Title | Severity | Phase | Last verified |
|---|---|---|---|---|
| AP-001 | INSERT OR REPLACE + UNIQUE silently loses audit history | H | P12 T1 | 2026-05-15 |
| AP-002 | FastAPI matches routes in registration order; static must precede `{param}` | H | P12 T6 | 2026-05-15 |
| AP-003 | `httpx.ConnectError` is too narrow — transport retries need `TransportError` | H | P12 retry | 2026-05-15 |
| AP-004 | CSS Grid auto-stretch + unbounded list panel = empty space below cols | M | P12 UI | 2026-05-15 |
| AP-005 | `$(cmd &)` in bash is sequential — `&` is consumed by command substitution | M | P12 stress | 2026-05-15 |
| AP-006 | Prompt-hash dedup conflicts with intentional retry probes | M | P12 redteam | 2026-05-15 |
| AP-007 | LLM ignores prompt-stripping for "obviously useful" patterns | M | P12 T5/redteam | 2026-05-15 |
| AP-008 | SQLite WAL alone doesn't solve concurrency across uvicorn workers | M | P12 T1 | 2026-05-15 |
| AP-009 | SSE-replayed audit rows need server-stamped `entry_id` | M | P12 T4 | 2026-05-15 |
| AP-010 | LT silently ignores conditions on undocumented metadata fields | H | P12 T5 | 2026-05-15 |

**Severity:** H = breaks demo / loses data / silent failure. M = degrades UX / wastes dev time. L = cosmetic / future-proof.

---

## AP-001 — INSERT OR REPLACE + UNIQUE silently loses audit history

**Symptom:** Re-deploy of the same `(job_id, policy_sha)` overwrites a prior rejection row; the chain-of-custody table claims one decision when reality had two.

**Root cause:** `INSERT OR REPLACE INTO policy_deploys` plus `UNIQUE (job_id, policy_sha)`. SQLite's REPLACE deletes the old row before inserting — by design, but catastrophic for audit tables.

**Detection:** Pre-implementation code-review caught it before code was written (reviewer Issue 1, plan file). Without the review it would have surfaced on the first reject-then-re-approve scenario — likely during a regulator audit, i.e. far too late.

**Fix:** Use plain `INSERT INTO`. Drop the `UNIQUE` constraint. Each row is a separate event in the chain of custody. Add a compound index `(job_id, decided_at)` for query speed.

**Prevention:** Any table whose name contains `audit`, `deploy`, `decision`, `log`, `event`, `history` is presumed **append-only**. Never use `INSERT OR REPLACE` or `UNIQUE` on such tables without explicit justification in a comment.

**Code:** `polaris/utils/db.py:79-95` · test: `tests/test_db.py::test_policy_deploys_is_append_only`

---

## AP-002 — FastAPI matches routes in registration order; static must precede `{param}`

**Symptom:** `GET /api/policies/packs` returns 404 ("job not found") even though `list_packs()` is defined.

**Root cause:** `@router.get("/api/policies/{job_id}")` was registered before `@router.get("/api/policies/packs")`. FastAPI's path-matcher consumes `packs` into `{job_id}`, the handler's `_validate_job_id` regex `^[a-f0-9]{12}$` rejects, returns 404. The static route is unreachable.

**Detection:** Live e2e — `PackPicker` UI rendered with 0 cards. Unit tests didn't catch it because they exercised handlers directly, not the router.

**Fix:** Reorder — static routes BEFORE param routes. Add header comment to file documenting the constraint so future contributors don't reintroduce the bug.

**Prevention:** When adding ANY new route under a prefix that already has a path-param catch-all, register before the catch-all. Better long-term: constrain path params with a regex pattern (e.g., `Annotated[str, Path(pattern=r"^[a-f0-9]{12}$")]`) so FastAPI itself falls through on mismatch.

**Code:** `polaris/api/routes.py:144-176` (header comment locks the constraint).

---

## AP-003 — `httpx.ConnectError` is too narrow — transport retries need `TransportError`

**Symptom:** Background task `redteam_loop:*` crashes mid-iteration with `ConnectError` *or* `ReadError` *or* `ConnectTimeout` — the closed-loop demo aborts before beat 9.

**Root cause:** `except (httpx.ConnectError, httpx.RemoteProtocolError)` covers two of httpx's transport exception classes. `ConnectTimeout` is under `TimeoutException`, `ReadError`/`WriteError` are under `TransportError → NetworkError`. None of these alternatives were caught. When LT reloads (consent gate stretched the window to ~3s), the shim socket can produce ANY of them.

**Detection:** Live e2e run with consent gate enabled crashed with `background task redteam_loop:effdbab75af1 failed: ConnectError('All connection attempts failed')` in API logs. The round-3 reviewer caught the narrower-than-base-class pattern post-fix.

**Fix:** Catch `httpx.TransportError` — the common base. Future httpx transport subclasses are covered automatically. Also schedule retries with `[1.0, 1.0, 1.0]` (final attempt at t=3s) instead of `[0.5, 1.0, 1.5]` (final at t=1.5s) so the last retry lands at the typical reload-complete mark.

**Prevention:** When catching httpx exceptions, default to `httpx.TransportError` for network/transport concerns or `httpx.HTTPError` for the entire library tree. Only narrow when you specifically want to ignore one branch.

**Code:** `polaris/agents/redteam.py:85-126`

---

## AP-004 — CSS Grid auto-stretch + unbounded list panel = empty space below cols

**Symptom:** Audit feed (col 3) grows tall with new entries. Cols 1+2 visually empty below their natural-height panels. Page scrolls down forever with blank space on the left.

**Root cause:** Default `align-items: stretch` on CSS Grid makes every cell match the row's tallest content. If col 3 has an unbounded `panel__scroll` list, the entire row stretches to its height. Cols 1+2 panels stay at their content height pinned to the top; the stretched-down portion of the col is empty.

**Detection:** User screenshot. The earlier fix (cap `.grid` with `grid-auto-rows: minmax(0, calc(100vh - 320px))`) over-corrected — clipped col 1's expanded Phase-12 content.

**Fix v2:** Use `:has()` to target ONLY panels that contain `.panel__scroll`: `.panel:has(.panel__scroll) { max-height: calc(50vh - 20px) }`. Internal scroll triggers; non-list panels grow naturally.

**Prevention:** Any panel rendering a *list* needs an explicit height constraint somewhere in its parent chain so `overflow: auto` engages. Test layouts with realistic list sizes (e.g. 50 rows), not the idle/empty state.

**Code:** `dashboard/app/globals.css:570-588`

---

## AP-005 — `$(cmd &)` in bash is sequential — `&` is consumed by command substitution

**Symptom:** Stress test "concurrent deploys" check passes even when the API can't handle concurrent traffic — the test never actually exercised concurrency.

**Root cause:** `R1=$(curl ... &)` captures stdout via command substitution. The shell *waits* for the curl to finish (it has to, to capture output). The `&` is consumed by the assignment scope and has no effect on the outer shell. `wait` on the next line has no background jobs and returns immediately.

**Detection:** Round-2 code reviewer noticed and flagged.

**Fix:** Background the whole curl with output to per-process files: `curl ... > /tmp/r1.json 2>&1 & P1=$!; ...; wait $P1 $P2 $P3`. Then read each file for assertions.

**Prevention:** When you want concurrency in bash, never combine `$(...)` with `&`. Either background-and-PID (`& PID=$!; wait $PID`) or use a parallel-runner like GNU parallel / xargs -P.

**Code:** `scripts/stress_test_phase12.sh:84-104`

---

## AP-006 — Prompt-hash dedup conflicts with intentional retry probes

**Symptom:** Demo beat 9 silently broken — "same payload after Synth patch" never fires because the probe is dedup'd against the gap probe from beat 8.

**Root cause:** A 2026-05-14 fix added client-side dedup on `sha256(probe.prompt)` to filter Gemini-emitted repeat probes from `generate_batch`. But `demo_sequence` (iteration 1) **intentionally** ships two probes with the identical prompt — the second to verify post-patch re-blocking. The dedup blindly skipped it.

**Detection:** Live e2e — test asserted `results[2].is_gap == False` (probe 3 should be re-blocked) but `results[2]` was actually iteration-2's first generated probe; iteration-1 had only 2 results.

**Fix:** Gate dedup on `iteration > 1`. Iter-1 is fixed deterministic content; iter-2+ is LLM-emitted and dedup makes sense there.

**Prevention:** Any general-purpose filter applied to a deterministic test fixture must be gated by the iteration/phase the fixture belongs to. If the fixture relies on a property the filter would mask, the filter must opt-out for that phase.

**Code:** `polaris/api/routes.py:801-815`

---

## AP-007 — LLM ignores prompt-stripping for "obviously useful" patterns

**Symptom:** `test_redteam_e2e` is flaky — sometimes the Synthesizer emits a `block_obfuscation_attempts` rule on the initial pass *despite* `_strip_example_5` removing the obfuscation example from the prompt. When it does, probe 2 (base64 payload) is denied immediately, the demo's intentional gap closes, and the closed-loop story collapses.

**Root cause:** Gemini 3.1 Flash-Lite has strong priors about security policies. Stripping Example 5 from the prompt does NOT prevent the model from inventing the same rule — `contains_obfuscation` is in the booleans list at line 86 and the model "knows" blocking obfuscation is good practice.

**Detection:** Two e2e runs after the same code change — one PASS, one FAIL. Audit log shows `rule_name: block_obfuscation_attempts` matched probe 2 on the failing run.

**Fix (not yet shipped):** Strip `contains_obfuscation` ALSO from the booleans list on initial-pass prompts (in addition to Example 5). Add explicit negative instruction: "DO NOT emit rules using contains_obfuscation on the initial pass — that field is reserved for Red Team-driven regeneration."

**Prevention:** When the demo flow depends on the LLM *not* emitting a specific pattern, don't trust prompt-stripping alone. Use a stronger lever: omit the field from the schema entirely on the initial-pass branch, OR validate the output against a no-fly list post-generation and reject/retry if the rule appears.

**Code:** `polaris/agents/synthesizer.py::_strip_example_5` · symptom in `tests/test_redteam_e2e.py`

---

## AP-008 — SQLite WAL alone doesn't solve concurrency across uvicorn workers

**Symptom:** `_APPROVAL_GATES` dict + `BUS` (SSE pub/sub) are silently broken under `--workers > 1`. A gate inserted by worker A is invisible to worker B receiving `/approve` — the operator's click 404s.

**Root cause:** Both are module-level Python dicts. They are process-local. SQLite WAL handles the *database* concurrency fine, but in-process state structures are still per-worker. Run with multiple uvicorn workers and you fragment your application state.

**Detection:** Pre-emptive — round-2 reviewer flagged before any production multi-worker deploy. Verified single-worker constraint in CLAUDE.md.

**Fix:** Annotate `_APPROVAL_GATES` with a clear single-worker-only comment referencing the same constraint already documented on `BUS`. Both must move to a shared store (Redis pub/sub for BUS, Redis hash for gates) before any `--workers N>1`.

**Prevention:** Module-level mutable state in a uvicorn app = single-worker contract. Document at the declaration site. If you ever see `--workers` get bumped, do an audit pass for module-level dicts/sets/lists. `BUS`, `_APPROVAL_GATES`, `_BACKGROUND_TASKS`, `_AUDIT_TASK` — all single-worker.

**Code:** `polaris/api/routes.py:80-96` and `polaris/api/state.py:17-22`

---

## AP-009 — SSE-replayed audit rows need server-stamped `entry_id`

**Symptom:** Operator clicks Release/Block on a QuarantineQueue row, but the API can't route the decision to the right audit entry.

**Root cause:** `record_audit_entry` was returning `None`; the SSE payload (`audit_log_entry` event) carried the raw audit dict without an id field. The Quarantine UI had no way to identify which row to operate on.

**Detection:** Pre-implementation — designing T4 surfaced the gap before code was written.

**Fix:** `record_audit_entry` returns the SQLite auto-increment `lastrowid`. `_pump_audit_log` stamps `raw["entry_id"] = id` on the SSE payload *after* persistence (so client and DB agree on the id).

**Prevention:** Any feature where operator decisions target specific data rows needs server-side stable identifiers stamped on the wire format. Don't generate ids client-side (they collide on browser refresh, replay, multi-tab). Don't rely on timestamps.

**Code:** `polaris/utils/db.py:127-141` · `polaris/api/routes.py:704-710`

---

## AP-010 — LT silently ignores conditions on undocumented metadata fields

**Symptom:** A YAML policy with `field: agent_id, match_type: exact, value: engineering-copilot-v1` parses successfully via `./bin/lobstertrap test --policy probe.yaml` (corpus passes), but the rule never matches at runtime — the eng-copilot request goes through as ALLOW.

**Root cause:** LT's audit log shows `agent_id` in the `declared_headers` block (passthrough from the request `_lobstertrap` block), but the LT documented metadata-field list (LOBSTER_TRAP_REFERENCE §6) is 22 specific fields — `agent_id` is NOT one of them. LT's policy evaluator only matches against the 22 detected fields; unknown fields in conditions are silently ignored.

**Detection:** Pre-implementation behavioral probe. Wrote a 1-rule policy with `field: agent_id`, started LT, fired two requests (one matching, one not), observed both got `action: ALLOW`. Confirmed schema acceptance ≠ runtime evaluation.

**Fix:** Abort the multi-agent permission feature for Phase 12. Ship the partial-multi-agent observability story (per-agent badges in audit feed) but do NOT claim divergent-verdict capability. Defer to v0.2 with shim-level routing or upstream LT support.

**Prevention:** Before building a feature on top of an external system's data flow, write a 5-minute behavioral probe that exercises the actual contract — not just the schema. The LT corpus test was a schema test. The behavioral test is what told the truth.

**Code:** abort note in `polaris/demo_agent/engineering_copilot.py:14-25` · plan abort gate `read-the-full-hackathon-magical-meerkat.md` Task 5.1

---

## Adding a new entry

1. Open this file. Find the highest AP-NNN number, increment.
2. Add an entry row to the index table (severity + phase + date).
3. Append a section with the full structure: Symptom / Root cause / Detection / Fix / Prevention / Code.
4. Stage `docs/ANTI_PATTERNS.md` in the SAME commit as the fix. This is enforced by CLAUDE.md §10 — reviewers should block fix-commits that don't include a registry update.
5. Severity guide: H if it could silently break the demo / lose data / fail a regulator audit. M if it costs dev time or degrades UX. L if it's cosmetic.

If the bug repeats a pattern already in the registry, do NOT add a duplicate — extend the existing entry's *Detection* or *Prevention* section to cover the new case.
