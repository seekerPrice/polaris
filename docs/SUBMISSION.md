# Polaris — lablab.ai Submission Cheat Sheet

> Pre-filled form answers for the TechEx Veea Trust Track submission on lablab.ai. Copy each field verbatim into the submission form. Update placeholder URLs before submitting.

---

## Project name
**Polaris**

## One-line tagline
From SOC 2 PDF to live AI guardrail in 60 seconds.

## Project description (4 sentences — one per judging axis)

Polaris uses Google Gemini and Veea Lobster Trap as a closed control loop: Reader and Synthesizer agents (gemini-3.1-flash-lite with thinking_level=low) compile a compliance PDF into a deployable YAML firewall policy in ~11 seconds, then a Red Team agent (gemini-3.1-pro-preview) continuously stress-tests the deployed policy and triggers Synthesizer regeneration when it finds gaps. The business value is compressing 1–3 weeks of legal review per policy (an estimated $15,000–$36,000 of compliance counsel and paralegal time) into ~$0.005 of Gemini API cost while producing an auditor-grade compliance report mapped to SOC 2 / EU AI Act / OWASP LLM Top 10 controls. Originality: Polaris is the first end-to-end natural-language→deployed-firewall implementation on an OSS DPI proxy, and the only project we know of that combines auto-synthesis (which Microsoft Agent Governance Toolkit lacks), runtime enforcement (which audit-time platforms like Comp AI lack), and closed-loop verification in a single tool. Presentation: a 12-beat 60-second demo video (recorded with ~11s actual end-to-end latency demonstrated by a live timer), a 10-slide pitch deck, an auto-generated compliance PDF, and 25 unit tests + 3 live e2e tests gating the build.

## Tech stack
- **Languages:** Python 3.11+, TypeScript
- **Models:** Google Gemini — `gemini-3.1-flash-lite` (Reader + Synthesizer, thinking_level=low) and `gemini-3.1-pro-preview` (Red Team)
- **Runtime enforcement:** Veea Lobster Trap (Go binary, DPI proxy on :8080)
- **API:** FastAPI + Server-Sent Events + aiosqlite
- **UI:** Next.js 16 + Tailwind + shadcn/ui + recharts
- **No frameworks:** direct API calls; no LangChain / LangGraph / CrewAI / AutoGen / llamaindex

## Sponsors used
- **Google Gemini** (criteria #1 — model integration depth, with thinking_level tuning + schema-first response_schema architecture per `docs/MODEL_BAKEOFF.md`)
- **Veea Lobster Trap** (criteria #1 — full bidirectional `_lobstertrap` declared-intent integration; 8 of 8 action classes exercised: ALLOW + DENY + LOG + HUMAN_REVIEW + RATE_LIMIT + threshold/boolean/contains match types + non-empty egress_rules)

## Team
- **Lucas (Loo Tan Yu Heng)** — sole engineer. Lead AI engineer at Hoppi on Hotseller V5 (25+ orchestrated Gemini agents, multi-tier model routing, semantic cache invalidation, taxonomy classifier across 51 categories × 100K+ multilingual records, per-entity iterative RAG). BSc First-Class Hons Computing Science, Heriot-Watt Malaysia (CGPA 3.9). Authored a 26-entry LLM Production Anti-Pattern Registry. **Polaris's 4-agent closed loop is the same architectural pattern shipped at Hoppi, applied to compliance.** Built solo in 6 days with Claude Code as implementation co-pilot.

## Links (UPDATE BEFORE SUBMIT)
- **GitHub repo:** https://github.com/seekerPrice/polaris  *(public; 16 commits on `main` as of 2026-05-15)*
- **Demo video:** <YouTube unlisted or Vimeo anyone-with-link URL>
- **Pitch deck PDF:** <Google Drive / Dropbox / inline GitHub asset URL>
- **Live dashboard screenshot (mid-demo):** `docs/img/demo_thumbnail.png`

## Hero metric (for landing page)
- **Headline:** 3 weeks of legal review → 60 seconds *(actual ~11s on the SOC 2 demo doc per `docs/MODEL_BAKEOFF.md`)*
- **Unit economics:** $15,000–$36,000 of compliance counsel per policy → ~$0.005 in Gemini API cost (≈ 3 million × cost compression on the policy authoring step).

## Verification artifacts to include in repo
- [ ] `submission_confirmation.png` (screenshot of lablab.ai submission confirmation)
- [ ] `docs/img/demo_thumbnail.png` (dashboard mid-demo, captured via `scripts/capture_thumbnail.sh` or browser DevTools)
- [ ] `docs/MODEL_BAKEOFF.md` (the 48-run benchmark that picked the Phase 9 winner)
- [ ] `dashboard/public/precomputed_run.json` (stage-day fallback fixture; Cmd+Shift+P replays without Gemini/LT)

## Pre-flight checklist (run before clicking submit)
```bash
bash scripts/preflight.sh           # unit tests + dashboard build + live verify
bash scripts/verify_live.sh          # repeat for cache warm-up
POLARIS_LIVE_E2E=1 uv run pytest tests/test_redteam_e2e.py -v  # closed loop
POLARIS_LIVE_E2E=1 uv run pytest tests/test_compliance_pdf.py -v  # PDF
```
All must PASS.

## Day-of submission flow
1. Push final commit: `git push origin main`
2. Confirm public repo loads in incognito.
3. Run `git log -p | grep -iE "GEMINI_API_KEY|sk-|AIza"` — must be empty.
4. Submit at https://lablab.ai/event/techex-intelligent-enterprise-solutions-hackathon → use this file's fields.
5. Screenshot confirmation page, commit as `submission_confirmation.png`.
