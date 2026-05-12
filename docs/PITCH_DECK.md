# Polaris — Pitch Deck (10 slides)

> Build in Google Slides or pitch.com using this outline. Export as `docs/PITCH_DECK.pdf`.
> Target: 10 slides, no animations, ~3 min spoken.

---

## Slide 1 — Hero
**Background:** full-screen Polaris dashboard mid-demo screenshot (`docs/img/demo_thumbnail.png`).

**Overlay text:**
> **POLARIS**
> *From SOC 2 PDF to live AI guardrail in 60 seconds.*

**Footer (small):** Veea Trust Track · TechEx 2026 · Built with Google Gemini & Lobster Trap

---

## Slide 2 — The pain

Centred quote on plain dark background:

> "We have 47 AI agents in production. We have no idea what any of them are allowed to do, and our compliance team is six weeks behind."
> — composite, every enterprise AI security lead, 2026

Below, small text:
> The gap between AI agents in production and the policies meant to govern them is now measured in weeks of legal review. It is the bottleneck on enterprise AI adoption.

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

---

## Slide 6 — Live demo

Single line:
> *"Let's run it."*

Embed the 60-second action demo (with 60-90s framing intro pre-pended). Backup: this slide pre-loads the cached output if the live video fails.

---

## Slide 7 — Why now

Three-column compact table:

| Regulation | In force | Demands |
|---|---|---|
| EU AI Act | 2025 | Risk management, logging, human oversight |
| SOC 2 (AI annex) | 2026 | Conversational-layer audit trails |
| NIST AI RMF | 2024 | Continuous adversarial testing |

Closing line:
> All three are policy documents. Polaris compiles all three into runtime enforcement.

---

## Slide 8 — The tech

Compact diagram showing exactly what was used:

- **Google Gemini** — `gemini-3.1-pro-preview` for the Synthesizer + Red Team. `gemini-3-flash-preview` for the Reader (2× faster than 2.5-flash with same coverage). [Stacks Gemini partner award.]
- **Veea Lobster Trap** — DPI proxy with full bidirectional `_lobstertrap` declared-intent integration — the underused half of LT, central to Polaris. [Stacks Veea partner award.]
- **No frameworks.** Direct API calls. ~2,000 lines of Python + 250 lines of TypeScript.
- **Built solo in 6 days, validated by 20+ unit tests, 11/11 Lobster Trap corpus tests, and a closed-loop Red Team verification.**

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

---

## Slide 10 — Team & ask

Photo / icon for Lucas. One line:

> **Lucas (Loo Tan Yu Heng)** — AI engineer, sole builder. Production LLM systems lead at Hoppi (Hotseller V5: 25+ orchestrated Gemini agents).

**The ask:**
> We built Polaris because we believe the bottleneck on safe enterprise AI is not the AI — it's the distance between policy and enforcement. We'd love to keep building.

**Stacking three prizes:**
- **Overall $10K prize pool** (closed-loop control architecture)
- **Veea partner award** (deepest Lobster Trap integration in any submission, including the underused declared-intent feature)
- **Gemini partner award** (4 Gemini agents, no framework dependencies, direct API)

**Links:** GitHub · Demo video · LinkedIn
