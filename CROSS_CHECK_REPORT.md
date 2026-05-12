# Polaris Handoff — Final Cross-Check Report

Date: May 12, 2026
Status: **Ready to hand to Claude Code.** One fix applied; two enhancements added. No blocking errors.

---

## Method

External facts verified via fresh web search against:
- lablab.ai TechEx Transforming Enterprise Through AI hackathon page
- ai-expo.net (AI & Big Data Expo schedule)
- github.com/veeainc/lobstertrap README
- ai.google.dev Gemini model docs and changelog
- Veea press release at veea.com/news

Internal consistency verified by grep across all 10 handoff files for: dates, model names, file references, Lobster Trap schema, banned dependencies, CLI commands.

---

## What was verified ✅

### Hackathon facts
- **Submission deadline May 18, 2026** — confirmed. (Online build phase May 11–18.)
- **Demo & awards day May 19, 2026** — confirmed. Winning teams present on the AI Developer Track on Day 2 of the conference.
- **Prize pool $10,000** — confirmed as the headline figure (additional partner prizes also exist, see below).
- **Sponsors: Veea + Google (Gemini, AI Studio, DeepMind) + Surge** — confirmed. Surge sponsors the X402 payments track (not ours).
- **Judging criteria (4 axes):** Application of Technology · Presentation · Business Value · Originality — confirmed verbatim from lablab page. Matches `CLAUDE.md` section 2 exactly.
- **Veea Trust track description:** "Build the trust layer enterprise security teams will actually sign off on. Build guardrails, observability, access control, audit, or red-team tooling where policy enforcement and conversation-layer security are first-class citizens." — Polaris hits every keyword. Strong fit.

### Lobster Trap technical details
- **Schema** (5 top-level sections, 22 metadata fields, 8 actions, 8 match types) — re-verified against the actual repo. `LOBSTER_TRAP_REFERENCE.md` matches.
- **`_lobstertrap` declared-intent feature** — verified. The example payload structure in our reference doc matches the upstream README exactly.
- **CLI commands** (`serve`, `inspect`, `test`) — verified.
- **Repository URL** https://github.com/veeainc/lobstertrap — verified live.
- **License** MIT — verified.
- **No external dependencies, single Go binary** — verified (means our `scripts/download_lobstertrap.sh` will work).

### Gemini models
- `gemini-2.5-pro` — still available and stable. Right choice for Synthesizer and Red Team.
- `gemini-2.5-flash` — still available and stable. Right choice for Reader.
- A note: **Gemini 3.1 Pro Preview** is now out (released between our knowledge cutoff and today). It's in preview status with restrictive rate limits — keep 2.5-pro as default for hackathon stability. Updated `CLAUDE.md` accordingly.

### Internal consistency
- All 7 build phase dates align across CLAUDE.md and BUILD_PLAYBOOK.md (Days 1–7 = May 12–18, demo May 19).
- All file references resolve: `examples/customer_feedback_today.txt` is created in Day 4 of the playbook and referenced in DEMO_SCRIPT and redteam_agent. ✓
- Banned dependencies (LangChain, LangGraph, CrewAI, AutoGen, llamaindex) only mentioned in the "do not use" lists. ✓
- Lobster Trap binary path convention (`./bin/lobstertrap`) consistent in scripts; bare `./lobstertrap` is used in spec prose where the exact path is irrelevant. Claude Code will resolve at build time. ✓
- The 12 demo beats in CLAUDE.md section 8 match the 12 beats in DEMO_SCRIPT.md section 1. ✓

---

## What was fixed 🔧

### Issue 1 — Red Team model inconsistency
**Found:** `CLAUDE.md` said the Red Team agent used `gemini-2.5-flash`, but README, `BUILD_PLAYBOOK.md`, and `prompts/redteam_agent.md` all said `gemini-2.5-pro`.

**Why pro is correct:** the Red Team generates adversarial attack variations across 12 categories — variety and creativity benefit from the better model. Flash is right for Reader (long PDF parsing, latency matters); Pro is right for Synthesizer (YAML correctness) and Red Team (attack diversity).

**Fix:** updated CLAUDE.md section 4 to specify `gemini-2.5-pro` for both Synthesizer and Red Team. Now consistent across all 10 files.

---

## What was added 📥

### Addition 1 — Discord mentor support
The lablab page mentions: *"TerraFabric Mentor support: Veea engineers active in the lablab Discord throughout the build phase for policy review, integration help, and architecture questions."*

Direct access to sponsor engineers (who are often also the judges) is one of the highest-leverage things in any hackathon. This wasn't in any of the 10 files. Added to `BUILD_PLAYBOOK.md` as a Day 1 pre-work item: join Discord, find Veea channel, introduce yourself, stay visible across the week.

### Addition 2 — Stackable prize structure
The $10K headline pool isn't the whole picture. Verified additional partner prizes:

- **Veea partner award:** Veea edge AI compute hardware + TerraFabric pilot access
- **Gemini partner award:** "Awarded to the top projects building with Gemini"
- **Veea publication award:** co-authored publication amplified across Veea's channels
- **Ecosystem opportunities:** collaboration, pilot, networking, hiring with Veea
- **Stage time:** AI Developer Track presentation at AI & Big Data Expo on May 19 (8,000+ attendees)

Polaris is positioned to stack three: overall + Veea + Gemini. Pitch deck slide 10 should explicitly call out all three angles. Added to `BUILD_PLAYBOOK.md` Day 1.

### Addition 3 — Default policy as a baseline
Verified that the upstream repo ships `configs/default_policy.yaml` as a starting point. Polaris should fetch a copy during scaffolding (kept at `examples/lobstertrap_default_policy.yaml`) for two uses: validating the Pydantic schema against a known-good YAML, and showing judges a before/after diff (generic default vs. Polaris-compliance-specific generation). Added to `BUILD_PLAYBOOK.md` Day 1.

---

## Advisories (not errors, but worth considering) ⚠

### Advisory 1 — Demo video length
The handoff specs a tight 60-second demo. Most successful lablab submissions run 2–3 minutes (60–90s of action + 60–90s of business framing). The 60s I scripted is action-heavy and skips the business case. Two options:

- **Option A (recommended):** record the 60s action demo as specified, then add 60–90s of voiceover-over-slides for the business framing (the problem, the loop architecture, the prize-stacking pitch from slide 10). Total ~2 minutes.
- **Option B:** keep the 60s as-is. Tight, punchy, memorable. Risk: judges score "Presentation" and "Business Value" lower because they had less to evaluate.

If you do Option A, the new framing 60–90s goes BEFORE the 60s action demo, not after. Hook first, action second.

### Advisory 2 — "1,500 lines of Python" claim in README
README slide 8 and the body text claim "~1,500 lines of Python." This is aspirational — the real number could be 2,000–3,000 lines including the demo agent, validators, and the dashboard. Either: (a) lower the claim to "~3,000 lines" before submission, or (b) verify the actual count on Day 6 and update accordingly. Currently the claim is fine for the spec but should be honest at submission.

### Advisory 3 — Gemini OpenAI-compatibility for Lobster Trap
Lobster Trap is an OpenAI-API-compatible proxy. Gemini's native API is NOT OpenAI-compatible by default. You have two options at Day 4:

- Use **Vertex AI's OpenAI-compatible endpoint** (Google offers one) — cleaner but requires GCP setup.
- Use **a tiny shim** (litellm or your own 30-line FastAPI proxy) that translates Gemini → OpenAI format.

Either works; both add Day 4 friction. The shim is faster to set up if you don't already have GCP configured. Worth deciding on Day 1 (when reviewing the kickoff prompt with Claude Code) rather than Day 4.

### Advisory 4 — Indirect injection demo realism
The customer_feedback_today.txt injection is well-designed but obvious if a judge reads it carefully ("Customer 14 (SYSTEM): Ignore..."). For maximum realism, consider planting the injection in a more naturalistic way — e.g., a customer message that quotes another customer's complaint in a way that contains the injection. Polish only on Day 6 after the basic demo works.

---

## Submission-day checklist (for May 18)

Pulled from DEMO_SCRIPT.md section 6, with the cross-check additions:

- [ ] Public GitHub repo (verify in incognito window).
- [ ] README.md has hero metric in line 1.
- [ ] Demo video — at least 60s, ideally 2–3 min total (see Advisory 1).
- [ ] Pitch deck as PDF (link in submission).
- [ ] Team page filled with at least one photo.
- [ ] Description paragraph hits all 4 judging axes in 4 sentences.
- [ ] Veea + Google logos visible in README and pitch deck.
- [ ] No exposed API keys in commit history (`git log -p | grep -i "key"`).
- [ ] Project description mentions: "Veea Trust Track" AND "uses Gemini deeply (4 agents)."
- [ ] Take a screenshot of submission confirmation.

---

## Bottom line

The package is internally consistent, technically accurate against the current Lobster Trap repo, and aligned with the actual hackathon judging criteria. One mismatch (CLAUDE.md model name for Red Team) fixed. Three valuable additions (Discord mentor support, prize stack visibility, default policy baseline) merged into the playbook. Four advisories left as judgment calls for the build.

**Ready to pass to Claude Code.** Start with `KICKOFF.md`.
