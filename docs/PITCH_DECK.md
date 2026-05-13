# Polaris — Pitch Deck (10 slides)

> Build in Google Slides or pitch.com using this outline. Export as `docs/PITCH_DECK.pdf`.
> Target: 10 slides, no animations, ~3 min spoken.

---

## Slide 1 — Hero
**Background:** full-screen Polaris dashboard mid-demo screenshot (`docs/img/demo_thumbnail.png`).

**Overlay text:**
> **POLARIS**
> *From SOC 2 PDF to live AI guardrail in 60 seconds.*
> *60-second SLA. Actual 11s. Watch.*

**Footer (small):** Veea Trust Track · TechEx 2026 · Built with Google Gemini & Lobster Trap

---

## Slide 2 — The pain

Centred quote on plain dark background:

> "We have 47 AI agents in production. We have no idea what any of them are allowed to do, and our compliance team is six weeks behind."
> — composite, every enterprise AI security lead, 2026

Below, small text:
> The gap between AI agents in production and the policies meant to govern them is now measured in weeks of legal review. It is the bottleneck on enterprise AI adoption.

**Why now (callouts):**
- **EU AI Act** high-risk obligations: in force **August 2026** (3 months from demo) *(source: [official timeline](https://artificialintelligenceact.eu/implementation-timeline/))*.
- **Colorado AI Act**: enforceable **June 2026** (1 month from demo) *(source: [Colorado HB 24-1139 §5](https://leg.colorado.gov/sites/default/files/2024a_205_signed.pdf))*.
- Without runtime enforcement, every enterprise with a deployed AI agent is non-conformant by default.

---

## Slide 3 — What Polaris is

Single sentence, large:
> Polaris generates deployable AI firewall policies from your compliance documents — and verifies them with a continuous adversarial Red Team.

Below, one-line architecture:
`Compliance PDF → Reader → Synthesizer → Lobster Trap → Red Team ↺`

---

## Slide 4 — The dashboard

Single full-bleed screenshot of `localhost:3000` mid-demo. Three callout arrows:
1. *Drag-drop policy upload (top-left)*
2. *Live YAML synthesis with `lobstertrap test` validation gate (centre)*
3. *Real-time attack timeline + auto-patching (right)*

---

## Slide 5 — The closed loop (why this is different)

Architecture diagram from `CLAUDE.md` §3 (the ASCII one, redrawn cleanly).

Annotation in red:
> **This loop closes itself.** Lobster Trap's `_lobstertrap` declared-vs-detected mismatches feed the Red Team Agent. Successful probes trigger Synthesizer regeneration. AI governing AI, with humans on the audit trail.

*Watch the live timer in slide 6. Hero metric is 60 seconds. Actual measured: ~11s.*

---

## Slide 6 — Live demo

Single line:
> *"Let's run it."*

Embed the 60-second action demo (with 60-90s framing intro pre-pended). Backup: this slide pre-loads the cached output if the live video fails.

---

## Slide 7 — Why now + unit economics

Three-column compact table:

| Regulation         | In force        | Demands                                   |
| ------------------ | --------------- | ----------------------------------------- |
| EU AI Act          | **August 2026** | Risk management, logging, human oversight |
| Colorado AI Act    | **June 2026**   | Algorithmic discrimination disclosure     |
| SOC 2 (AI annex)   | 2026            | Conversational-layer audit trails         |
| NIST AI RMF        | 2024            | Continuous adversarial testing            |

Closing line:
> All four are policy documents. Polaris compiles all four into runtime enforcement.

**Unit economics:**
- **$15,000–$36,000** of legal review per policy (1–3 weeks of compliance counsel + paralegal at blended $150–300/hr) → **~$0.005** in Gemini API cost.
- ~**3 million ×** cost compression on the policy authoring step.

---

## Slide 8 — The tech

Compact diagram showing exactly what was used:

- **Google Gemini** — `gemini-3.1-flash-lite` (GA May 7 2026) powers Reader AND Synthesizer (the latter with `thinking_level="low"` per `docs/MODEL_BAKEOFF.md`); `gemini-3.1-pro-preview` powers the Red Team Agent. Schema-first architecture passes `LobsterTrapPolicy` directly as Gemini's `response_schema`, eliminating the YAML-string-bloat surface that broke earlier 3.x experiments. [Stacks Gemini partner award.]
- **Veea Lobster Trap** — DPI proxy with full bidirectional `_lobstertrap` declared-intent integration — the underused half of LT, central to Polaris. [Stacks Veea partner award.]
- **No frameworks.** Direct API calls. ~2,000 lines of Python + 250 lines of TypeScript.
- **Built solo in 6 days, validated by 20+ unit tests, 11/11 Lobster Trap corpus tests, and a closed-loop Red Team verification.**
- **Built with Claude Code** as the implementation co-pilot — Lucas drove architecture, Red Team loop logic, and the Phase-9 model bake-off; Claude Code did refactoring, test scaffolding, and dashboard MVP. Net: 1 engineer × Claude Code = the productivity of a 3-engineer week.

Tag line:
> First end-to-end natural-language → deployed firewall implementation on an OSS DPI proxy.

---

## Slide 9 — What we shipped

Simple table:

| Built | Status |
|---|---|
| Reader Agent over 3 real compliance docs (SOC 2, EU AI Act, OWASP LLM Top 10) | ✓ |
| Synthesizer + 3-layer validation gate (yaml.safe_load → Pydantic → `lobstertrap test`) | ✓ |
| Lobster Trap integration with declared-intent schemas | ✓ |
| Demo Agent (Sales Ops Copilot) with realistic indirect-injection scenario | ✓ |
| Red Team Agent with closed-loop policy patching (gap → regenerate → hot-reload) | ✓ |
| Auto-generated compliance report PDF mapped to source controls | ✓ |
| Dashboard: 4-panel real-time UI with line-by-line YAML animation | ✓ |

**Pricing model proposal (v1):** per-policy per-month subscription (~$500/mo/policy) covering Polaris API + Lobster Trap deployment + compliance PDF refreshes. Marginal cost: <$0.01 in Gemini per policy. Margin: >95%. TAM: ~2M enterprises subject to SOC 2 / EU AI Act / HIPAA with AI agents in production.

---

## Slide 10 — Team & ask

Photo / icon for Lucas. One line:

> **Lucas (Loo Tan Yu Heng)** — sole engineer. Lead AI engineer at Hoppi on Hotseller V5 (25+ orchestrated Gemini agents, multi-tier model routing, semantic cache invalidation, taxonomy classifier across 51 categories × 100K+ multilingual records). Polaris's 4-agent closed loop is the same architectural pattern, applied to compliance.
>
> *Designed for Fortune-500 CISOs and security engineers in regulated AI deployments. Pilot interest from enterprise security teams welcome — lucas@heyhoppi.com.*

**The ask:**
> We built Polaris because we believe the bottleneck on safe enterprise AI is not the AI — it's the distance between policy and enforcement. We'd love to keep building.

**Stacking three prizes:**
- **Overall $10K prize pool** (closed-loop control architecture)
- **Veea partner award** (deepest Lobster Trap integration in any submission, including the underused declared-intent feature)
- **Gemini partner award** (4 Gemini agents, no framework dependencies, direct API)

**Links:** GitHub · Demo video · LinkedIn
