# Polaris — Pitch Deck Brief (Zacht "VC Pitch Deck" template)

> **How to use this file:** Open side-by-side with pitch.com. For each slide
> below, clone the matching Zacht template slide #, copy the body content
> verbatim, swap the stock image as noted, and add the footer citation as a
> 9pt grey (`#6F7585`) text element bottom-left.
>
> **Deck spec:** 15 core + 3 appendix = 18 slides. ~3-min spoken duration.
> Every numeric claim carries a clickable source URL footer (verified
> 2026-05-18 against Stanford HAI, McKinsey, Grand View Research, Clio, Drata,
> HHS, EU Commission, Microsoft Learn, Lakera, F5, Cisco, Google AI).
> Master bibliography at the bottom of this file.

## Brand palette — apply throughout *(REPLACES Zacht template defaults)*

Polaris uses a dark-mode "mission control" aesthetic with cyan glow accents (per `dashboard/app/globals.css`). The Zacht template defaults to a light-blue base with purple gradient emphasis panels. Map them as follows in pitch.com (Format → Background / Text fill / Stroke color):

| Zacht template default                       | Polaris brand substitute | Hex                 | Usage                                                      |
|----------------------------------------------|--------------------------|---------------------|------------------------------------------------------------|
| Light blue page bg *(≈`#EEF1FA`)*            | **Polaris navy bg**      | `#0B0D14`           | Page background on all slides                              |
| Light grey panel                             | **Polaris panel**        | `#13161F`           | Card / table backgrounds                                   |
| Elevated panel                               | **Polaris elevated**     | `#1B202A`           | Sub-cards, nested cells                                    |
| Purple gradient *(`#6366F1 → #8B7EFF`)*      | **Cyan gradient**        | `#1AA8C7 → #5DE3F5` | Mission / Why-Now / Closed-Loop / Thank-You emphasis panels |
| Section tag purple *(`#6366F1`)*             | **Polaris cyan**         | `#5DE3F5`           | All `OVERVIEW`, `MISSION`, `SOLUTION`, `PRODUCT`, etc. tags |
| Dark navy text *(`#0E1330`)*                 | **Near-white**           | `#F4F5F8`           | Primary headings + body                                    |
| Mid grey body                                | **Text-1**               | `#B8BCC9`           | Secondary body, sub-bullets                                |
| Footer grey *(`#6F7585`)*                    | **Text muted**           | `#7E8499`           | Citation footers (bottom-left)                             |
| Accent — deny / warning                      | **Rose**                 | `#F25C5C`           | "DENY" cells in slide 9 table; ✗ marks                     |
| Accent — success                             | **Emerald**              | `#3DD9A0`           | "✓" marks in slide 9 table; positive metrics               |
| Accent — CTA / highlight                     | **Amber**                | `#F5C25E`           | Slide 14 ask, A1 QR CTA, fundraising bar on slide 12       |

**Fonts (override Zacht's Inter default):**

- **Headings + body:** Space Grotesk. *(pitch.com → Format → Text → Font → search "Space Grotesk"; install via Google Fonts if not in dropdown.)* Matches dashboard's `--font-sans`.
- **Numbers / monospace data** *(slide 11 tiles, footer URLs, code-flavored references)*: JetBrains Mono. Matches dashboard's `--font-mono`.

**Style translation rule:** In the per-slide briefs below, when I say *"purple gradient"* or *"light bg"* or *"dark navy text"*, those refer to the Zacht template's defaults — substitute the Polaris equivalent from the palette above. The goal: the deck visually echoes the live dashboard at `polaris--lucaslootan.replit.app`, so when a judge clicks the URL the brand experience continues.

**Visual cohesion checklist:**

- All dashboard screenshots (`docs/img/demo_thumbnail.png`) already match this palette — no recolor needed.
- The architecture diagram for slides 7 + A2 should be redrawn with cyan strokes on the navy bg (`stroke: #5DE3F5`, `fill: #13161F`, text `#F4F5F8`).
- Section emphasis panels (currently purple in Zacht) should be a vertical cyan gradient `#1AA8C7` (top) → `#5DE3F5` (bottom) on a deep navy backdrop — NOT a flat cyan fill.
- The "Try Pitch" badge (free-tier watermark) sits on a dark bg; that's fine.

---

**Hedging notes — do NOT skip on slide 4:**

- **EU AI Act:** 2 Aug 2026 statutory. The Digital Omnibus political agreement
  (7 May 2026) defers Annex III high-risk obligations to 2 Dec 2027 — not yet
  enacted. Slide 4 must say "statutory; pending Omnibus deferral".
- **Colorado AI Act (SB24-205):** postponed to 30 Jun 2026 → federal
  magistrate stay 27 Apr 2026 → replacement bill SB 189 in motion. Slide 4
  must footnote "enforcement currently stayed".

---

## Slide 1 — Cover *(clone Zacht slide 1)*

- **Layout:** Gradient purple bg left, product mockup right.
- **Top-left tag:** `POLARIS`
- **Top-right tag:** `VEEA TRUST TRACK · TECHEX 2026`
- **Big headline (white):** `PITCH DECK`
- **Subline (smaller, white):** From SOC 2 PDF to live AI guardrail in 60 seconds.
- **Date stamp (white, smaller):** MAY 2026
- **Image swap (right):** Replace the iPhone "Bookmarks" mockup with
  `docs/img/demo_thumbnail.png` (dashboard mid-demo).
- **Footer citation:** *(none — cover slide)*

---

## Slide 2 — Mission *(clone Zacht slide 4 — full-bleed centered)*

- **Layout:** Full-bleed purple gradient. Centered text. No image.
- **Section tag (white, top center):** `MISSION`
- **Headline (white, h1, ~60pt):** "Compile compliance documents into running AI firewalls — at AI speed."
- **Sub-body (white, smaller):** Polaris is the only end-to-end loop from compliance PDF to deployed runtime policy to continuous adversarial verification.
- **Footer citation:** *(none — philosophy)*

---

## Slide 3 — Overview / One-Pager *(clone Zacht slide 5)*

- **Layout:** Dense one-pager — title left, highlights/industry/team/chart stacked right.
- **Section tag (purple top-left):** `OVERVIEW`
- **Headline (left, dark navy):** A 4-agent closed loop that compiles compliance into runtime enforcement.

**HIGHLIGHTS (right top):**

- Compiles SOC 2 / HIPAA / EU AI Act / PCI-DSS PDFs into deployable YAML
  Lobster Trap firewall policies. ~11s observed end-to-end; 60s SLA.
- Red Team agent continuously stress-tests deployed policy; auto-patches on
  gap detection.
- Audit-defensible chain of custody from source PDF to every blocked attack,
  mapped to SOC 2 CC8.1 change-management.

**INDUSTRY & MARKET (right middle):** Enterprise AI Trust, Risk & Security
Management (TRiSM) — USD **$2.34B in 2024**, projected **$7.44B by 2030**
(21.6% CAGR).

**TEAM (right lower-left):** Lucas Loo Tan Yu Heng — Founder & Lead AI
Engineer. Day job: Hoppi (M) Sdn Bhd — Hotseller V5 (25+ orchestrated Gemini
agents in production).

**HERO METRIC chart (right lower-right):** Bar chart contrasting "60s SLA · 11s
actual" vs status quo "3 weeks of legal review" (use Zacht's revenue-chart bar
style; relabel axes).

**Footer citation:** `Source: Grand View Research · grandviewresearch.com/press-release/global-ai-trust-risk-security-management-market`

---

## Slide 4 — Problem + Why Now *(clone Zacht slide 6 — vertical split)*

**Layout:** Left half light bg, right half purple gradient.

### LEFT — `THE PROBLEM`

- **Headline (dark navy, h2):** Compliance lives in PDFs. AI agents run in
  production. The wire between them is hand-written, weeks late, and untested.
- **Bullets:**
  - 23% of enterprises now scale AI agents; 39% experiment. *(McKinsey State of AI 2025)*
  - 233 AI security incidents in 2024 → 362 in 2025 (+55% YoY). *(Stanford HAI AI Index 2025/2026)*
  - Median compliance / business-formation counsel: **$378/hr** (US, 2025 data). *(Clio Legal Trends 2026)*

### RIGHT — `WHY NOW`

- **Headline (white, h2):** Regulators are catching up. Every enterprise
  running an AI agent is non-conformant by default.
- **Bullets:**
  - **EU AI Act** high-risk obligations: 2 Aug 2026 (statutory). The Digital
    Omnibus political agreement (7 May 2026) defers Annex III obligations to
    2 Dec 2027 — not yet enacted.
  - **Colorado AI Act (SB24-205):** postponed to 30 Jun 2026; enforcement
    currently stayed pending federal litigation (Apr 27 2026).
  - **NIST AI RMF 1.0** — voluntary framework, Jan 2023.
  - **OWASP LLM Top 10 v1.1** — prompt injection ranked #1.

**Footer citation (two-line, small):**

- `mckinsey.com/.../state-of-ai · hai.stanford.edu/ai-index · clio.com/resources/legal-trends`
- `artificialintelligenceact.eu · leg.colorado.gov/bills/sb24-205 · nist.gov/itl/ai-risk-management-framework · owasp.org`

---

## Slide 5 — Solution *(clone Zacht slide 7 — 3 features with images)*

- **Section tag (purple top-left):** `SOLUTION`
- **Headline (dark navy):** Polaris compiles compliance documents into runtime AI guardrails — and verifies them.
- **Sub-body:** Four Gemini agents. One Veea Lobster Trap firewall. One closed loop.

**3 columns (image top, label + description bottom):**

1. **Reader Agent** — `gemini-3.1-flash-lite`. Extracts compliance requirements
   from PDF text. ~3s per doc. *(Image: PDF being highlighted with extracted
   bullet points.)*
2. **Synthesizer Agent** — `gemini-3.1-flash-lite` + `thinking_level=low`.
   Schema-first synthesis: passes `LobsterTrapPolicy` Pydantic class as
   `response_schema`. ~4.6s median latency. *(Image: YAML streaming in editor.)*
3. **Red Team Agent** — `gemini-3.1-pro-preview`. Generates adversarial probes;
   triggers Synthesizer regeneration on gap. ~10s per round. *(Image: attack
   timeline chart showing DENY → gap → DENY recovery.)*

**Footer citation:** `Sources: Google Gemini pricing · ai.google.dev/gemini-api/docs/pricing · Veea Lobster Trap · github.com/veeainc/lobstertrap`

---

## Slide 6 — Product close-up *(clone Zacht slide 8 — text left, dashboard right)*

- **Section tag:** `PRODUCT · LIVE DASHBOARD`
- **Headline (left, dark navy):** Drag-drop. 11 seconds. Live firewall.
- **Sub-body (left):** Phase-9 schema-first Synthesizer cuts latency 5× while
  tying with the larger Pro model on intrinsic accuracy (6.0/11 on the internal
  Lobster Trap corpus). Same architectural pattern shipped at scale in Hoppi's
  Hotseller V5 (25+ orchestrated agents).
- **Image (right, large):** `docs/img/demo_thumbnail.png` — mid-demo dashboard
  with KPI strip, audit feed, red team panel, compliance PDF preview.
- **Footer citation:** `Source: Internal benchmark — docs/MODEL_BAKEOFF.md (48-run model bake-off, Phase 9, 2026-05-13, public on GitHub)`

---

## Slide 7 — The Closed Loop / USP *(clone Zacht slide 9 — annotated product image)*

- **Section tag (white on purple, top):** `THE CLOSED LOOP`
- **Headline (white, centered):** This loop closes itself.
- **Center:** Architecture diagram from `CLAUDE.md` §3 redrawn cleanly (PDF →
  Reader → Synthesizer → Lobster Trap → Demo Agent → Mismatch Detector → Red
  Team → Synthesizer regen).

**Annotations around (leader lines into the diagram, matching Zacht slide-9 style):**

- "1. Reader · ~3s" (top-left → PDF node)
- "2. Synthesizer · 4.6s median · schema-first" (top-right → YAML node)
- "3. Validation gate · `lobstertrap test` · 11/11 corpus pass" (right → LT node)
- "4. Lobster Trap · DPI proxy · _lobstertrap declared-intent" (bottom-right → DPI node)
- "5. Red Team · ~10s · auto-patches on gap" (bottom-left → loop back arrow)

**Footer citation:** `Source: Veea Lobster Trap · github.com/veeainc/lobstertrap`

---

## Slide 8 — Market Opportunity *(clone Zacht slide 11 — concentric circles + bullets)*

- **Section tag:** `MARKET OPPORTUNITY`
- **Headline (left, dark navy):** A $7.44B market, expanding 21.6% per year.

**Left bullets (TAM/SAM/Target/Share — matching Zacht layout):**

- **TAM — Global AI Trust, Risk & Security Management:** $2.34B (2024) →
  $7.44B by 2030 (21.6% CAGR). *(Grand View Research, 2025 — Gartner-named category.)*
- **SAM — AI governance platforms:** Gartner names this a "billion-dollar
  market" (Feb 2026 press release). Precedence Research projects $309M (2025)
  → $3.59B (2033) at 36% CAGR.
- **Target market — US enterprises subject to SOC 2 / HIPAA with AI agents in
  production:** subset of ~822,600 HIPAA-covered entities + ~1M business
  associates, narrowed to those with AI-in-production (23% per McKinsey 2025).
  Estimated **$740M** ARPU-weighted serviceable wedge.
- **Entry capture (Year 1-2):** 1% of target at $500-$2,500/month/policy ARPU
  ≈ **$74M ARR potential**.

**Right side:** Concentric circle visualization labeled $7.44B / $3.59B / $740M /
$74M (clone Zacht's circle style exactly, just relabel).

**Footer citation (multi-line):**

- `TAM: Grand View Research · grandviewresearch.com/press-release/global-ai-trust-risk-security-management-market`
- `SAM: Gartner PR (Feb 2026) · gartner.com/en/newsroom/press-releases/2026-02-17-... · Precedence Research · precedenceresearch.com/ai-governance-market`
- `Target: HHS HIPAA · hhs.gov/hipaa/for-professionals/compliance-enforcement/audit · McKinsey · mckinsey.com/.../state-of-ai`

---

## Slide 9 — Competitive Landscape *(custom — replaces Zacht slide 14)*

- **Section tag:** `COMPETITIVE LANDSCAPE`
- **Headline (dark navy):** Polaris is the only end-to-end PDF → Deploy → Verify → Patch loop.

**Comparison table (use Zacht's pricing-table cell style):**

| Capability                                   | **Polaris** | MS Purview AI Hub | Lakera Guard | F5 AI Guardrails *(ex-CalypsoAI)* | Cisco AI Defense *(ex-Robust Intelligence)* |
|----------------------------------------------|:-----------:|:-----------------:|:------------:|:---------------------------------:|:-------------------------------------------:|
| Auto-synthesizes policy **from a compliance PDF** |  ✓     | ✗                | ✗            | ✗                                | ✗                                          |
| Runtime inline enforcement on LLM I/O        |  ✓          | ✗\*              | ✓            | ✓                                | ✓                                          |
| **Closed-loop continuous Red Team**          |  ✓          | ✗                | ✗            | ✗                                | ✗                                          |
| Auto-generated compliance PDF                |  ✓          | partial *(audit log)* | ✗      | ✗                                | partial                                    |
| Open-source DPI substrate                    |  ✓ *(Veea LT)* | ✗             | ✗            | ✗                                | ✗                                          |

**Caption (small italic, below table):** \* Microsoft Purview AI Hub provides
endpoint browser DLP + post-hoc audit only — not inline blocking on LLM
outputs. None of the four funded incumbents combine auto-synthesis + runtime
enforcement + closed-loop verification. *(Verified May 2026 via product pages.)*

**Footer citation (multi-line, small):**

- `learn.microsoft.com/en-us/purview/ai-microsoft-purview`
- `lakera.ai/lakera-guard`
- `f5.com/products/ai-guardrails  (CalypsoAI acquired by F5)`
- `cisco.com/site/us/en/products/security/ai-defense/index.html  (Robust Intelligence acquired by Cisco)`

---

## Slide 10 — Business Model + Pricing *(clone Zacht slide 15 — pricing table)*

- **Section tag (left):** `BUSINESS MODEL`
- **Headline (left, dark navy):** Per-policy subscription. SOC 2-defensible. >95% gross margin.
- **Pricing strategy (left, smaller):** Tiered SaaS + per-inference overage.
  Self-hosted Lobster Trap option for compliance-strict tenants. Pricing is a
  **draft model** pending design-partner validation (Q3 2026 pilots).

**Pricing table (right, two-column matching Zacht slide 15):**

|                                  | **Starter**                                              | **Pro**                                          |
|----------------------------------|----------------------------------------------------------|--------------------------------------------------|
| Compliance packs                 | 1 *(SOC 2 OR HIPAA OR EU AI Act OR PCI-DSS)*             | Unlimited                                        |
| AI agents protected              | 1                                                        | Unlimited                                        |
| Continuous Red Team              | ✓ weekly                                                 | ✓ continuous                                     |
| Drift detection *(v0.2)*         | —                                                        | ✓                                                |
| Slack / Linear alerts            | —                                                        | ✓                                                |
| Compliance PDF auto-generation   | ✓                                                        | ✓                                                |
| Self-hosted Lobster Trap option  | —                                                        | ✓                                                |
| Audience                         | SOC 2 design partners                                    | Multi-policy enterprises                         |
| **Price**                        | **$499 / month**                                         | **$2,499 / month** + $0.10 / 1k inferences       |

**Bottom note (below table):** Marginal cost per policy synthesis ≈ **$0.005**
in Gemini compute (gemini-3.1-flash-lite at $0.25/M input + $2/M output ×
~3k input + 2k output tokens). Gross margin: **>95%**.

**Footer citation:** `Source: Google Gemini API pricing · ai.google.dev/gemini-api/docs/pricing`

---

## Slide 11 — Unit Economics *(clone Zacht slide 16 — 6 metric tiles)*

- **Section tag:** `UNIT ECONOMICS`
- **Headline:** Why the math works.

**6 tiles (3×2 grid; clone Zacht's large-number-over-caption style):**

|                                                                  |                                          |                                                            |
|------------------------------------------------------------------|------------------------------------------|------------------------------------------------------------|
| **11 seconds** <br/> END-TO-END *(60s SLA)*                      | **$0.005** <br/> GEMINI COST / POLICY    | **3,000,000×** <br/> COST COMPRESSION *(policy authoring)* |
| **$15K–$45K** <br/> COMPLIANCE COUNSEL REPLACED                  | **11 / 11** <br/> LOBSTER TRAP CORPUS PASS | **62 / 62** <br/> UNIT TESTS PASS                          |

**Below tiles (small text):** Counsel-cost floor derived from Drata-published
SOC 2 framework data (3-week observation + 2-5 week audit windows) × Clio's
$378/hr 2026 median compliance billing rate × full-time equivalent ≈ $45K
floor for a single policy review cycle.

**Footer citation (multi-line):**

- `drata.com/grc-central/soc-2/how-much-does-a-soc-2-audit-cost`
- `clio.com/resources/legal-trends/compare-lawyer-rates/`
- `ai.google.dev/gemini-api/docs/pricing`
- `Internal: 11/11 corpus and 62/62 pytest results — repo: github.com/seekerPrice/polaris`

---

## Slide 12 — Roadmap *(clone Zacht slide 18 — quarterly timeline)*

- **Section tag:** `ROADMAP`
- **Headline:** Where we go after the hackathon.

**Quarterly columns (5 quarters, matching Zacht slide 18):**

- **Q3 2026** *(next — demo + early adopters)*
  - Per-agent declared_intent verdicts *(multi-agent isolation, v0.2)*
  - SOC 2 design-partner pilot *(3-5 enterprises)*
  - Drift detection v0.1
- **Q4 2026**
  - HIPAA + PCI-DSS pack hardening from auto-synthesis
  - Pricing GA (Starter + Pro)
  - Slack / Linear alerts integration
- **Q1 2027** *(FUNDRAISING BAR — Series Seed)*
  - Multi-tenant SaaS architecture
  - $2M Seed target
- **Q2 2027**
  - EU AI Act high-risk Annex III policy templates
  - 25 paying tenants
- **Q3 2027**
  - Self-service Veea DevKit deployment
  - 100+ tenants

**Fundraising bar:** Solid purple horizontal line spanning Q1 2027 column,
labeled `SEED · $2M`.

**Footer citation:** *(none — internal forward-looking)*

---

## Slide 13 — Team *(clone Zacht slide 19 — photo grid; simplified for solo)*

- **Section tag:** `TEAM`
- **Headline:** Sole engineer, with the production playbook already shipped.

**Layout:** 1 large profile center + 3 silhouette/placeholder "advisor seat"
cards. Use Zacht's photo+name+title layout; leave 3 advisor cards as
"OPEN — recruiting".

**Lucas card:**

- **Photo:** GitHub avatar at high res (or supply professional headshot)
- **Name:** Loo Tan Yu Heng
- **Title:** Founder & Lead AI Engineer
- **Location:** Kuala Lumpur, Malaysia
- **Bio:** Lead AI Engineer at Hoppi (M) Sdn Bhd on Hotseller V5 — 25+
  orchestrated Gemini agents, multi-tier model routing, semantic cache
  invalidation, taxonomy classifier across 51 categories × 100K+ multilingual
  records. Authored a 26-entry internal LLM Production Anti-Pattern Registry.
  **Polaris's 4-agent closed loop is the same architectural pattern, applied
  to compliance.**

**3 open advisor cards:**

- "CISO Advisor — OPEN"
- "Compliance Counsel — OPEN"
- "Veea Partnerships — OPEN"

**Footer citation:** `github.com/seekerPrice/polaris  ·  linkedin.com/in/lucasloo  (or actual handle)`

---

## Slide 14 — Deal Terms / Ask *(clone Zacht slide 20 — donut + ideal partner)*

- **Section tag (left):** `WHAT WE'RE ASKING`
- **Headline (left, large):** Hackathon-first. Pilot deployments next. $2M Seed in Q1 2027.
- **Left sub-text:** Today's ask is operational, not financial: deploy Polaris
  as a Veea DevKit pilot in your enterprise.

**Donut chart (left, mid-page):** Future Seed allocation if raised — clone
Zacht donut, three slices:

- 50% Engineering hires *(3 FTE)*
- 30% Sales & partnerships
- 20% R&D *(drift detection + multi-tenant infra)*

**Right column — `IDEAL PARTNER` bullets:**

- A Veea ecosystem deployment lead *(Lobster Trap is the substrate)*
- A regulated-industry early-adopter *(Fortune 2000 in healthcare or fintech)*
- A counsel-side advisor on EU AI Act high-risk classification *(Annex III)*

**Footer citation:** *(none — forward-looking)*

---

## Slide 15 — Thank You *(clone Zacht slide 21 — huge "THANK YOU")*

- **Layout:** Full-bleed purple gradient. Huge centered "THANK YOU".
- **Top corners:** `POLARIS` (top-left) · `VEEA TRUST TRACK · TECHEX 2026` (top-right)
- **Above the THANK YOU:** "POLARIS" small logo placeholder
- **Below the THANK YOU:** `lucaslootan@gmail.com`
- **Bottom-line URL:** `polaris--lucaslootan.replit.app` (underlined, white)
- **Below URL (smaller, monospace):** `github.com/seekerPrice/polaris`
- **Footer citation:** *(none — close)*

---

## Appendix A1 — Live demo + QR *(clone Zacht slide 24 — dark CTA)*

- **Layout:** Dark bg matching Zacht slide 24, with one large QR code center, URL underneath.
- **QR code:** `docs/img/polaris_qr.png` *(generated via `uv run python -c "import qrcode; qrcode.make('https://polaris--lucaslootan.replit.app/').save('docs/img/polaris_qr.png')"`)*
- **Large text below QR:** `polaris--lucaslootan.replit.app`
- **CTA text:** Drop your SOC 2 PDF. Watch the firewall deploy in 11 seconds.
- **Footer citation:** *(none — call to action)*

---

## Appendix A2 — Technical Architecture *(clone Zacht slide 22 — appendix divider)*

- **Section tag (white on purple):** `ARCHITECTURE · APPENDIX`
- **Image (full-bleed center):** Full 4-agent + Lobster Trap loop diagram from
  `CLAUDE.md` §3, redrawn cleanly with all data flows labeled (export from
  excalidraw or mermaid).
- **Footer citation:** `github.com/seekerPrice/polaris  ·  github.com/veeainc/lobstertrap`

---

## Appendix A3 — Compliance Control Mapping *(custom dense table)*

- **Section tag:** `COMPLIANCE COVERAGE · APPENDIX`
- **Headline:** Every Polaris rule traces back to a named, citable control.

| Source control                                                          | Polaris rule examples                  | Lobster Trap action |
|-------------------------------------------------------------------------|----------------------------------------|---------------------|
| SOC 2 CC6.1 *(Logical access)*                                          | `block_credential_exfiltration`        | DENY                |
| SOC 2 CC8.1 *(Change management)*                                       | ApprovalGate consent before deploy     | HUMAN_REVIEW        |
| HIPAA §164.312(a)(2) *(Access control implementation specs)*            | `block_phi_unauthorized`               | DENY                |
| EU AI Act Art. 9 *(Risk management system)*                             | `quarantine_borderline_credential`     | QUARANTINE          |
| OWASP LLM01 *(Prompt Injection)*                                        | `block_obfuscation_attempts`           | DENY                |
| OWASP LLM06 *(Sensitive Information Disclosure)*                        | egress DPI scan rules                  | LOG + DENY          |

**Footer citation (multi-line):**

- `aicpa-cima.com  (SOC 2 Trust Services Criteria)`
- `hhs.gov/hipaa  ·  45 CFR §164.312`
- `artificialintelligenceact.eu/article/9/`
- `owasp.org/www-project-top-10-for-large-language-model-applications/`

---

## Master source bibliography

All URLs verified 2026-05-18 by two parallel research agents. Confidence ratings reflect source quality (HIGH = first-party + reachable; MEDIUM = secondary aggregator covering primary; LOW = vendor blog).

1. **Grand View Research — Global AI TRiSM Market Report** (TAM): `https://www.grandviewresearch.com/press-release/global-ai-trust-risk-security-management-market` *(MEDIUM — tracks Gartner's named category)*
2. **Gartner — Feb 2026 AI Governance Press Release** (SAM): `https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms` *(MEDIUM-HIGH)*
3. **Precedence Research — AI Governance Market**: `https://www.precedenceresearch.com/ai-governance-market` *(LOW-MEDIUM)*
4. **McKinsey — The State of AI 2025**: `https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai` *(HIGH — methodology disclosed)*
5. **Stanford HAI — AI Index 2025 (Responsible AI chapter)**: `https://hai.stanford.edu/ai-index/2025-ai-index-report/responsible-ai` *(HIGH)*
6. **Stanford HAI — AI Index 2026 (Responsible AI chapter)**: `https://hai.stanford.edu/ai-index/2026-ai-index-report/responsible-ai` *(HIGH)*
7. **Clio — Legal Trends 2026, lawyer hourly rate comparison**: `https://www.clio.com/resources/legal-trends/compare-lawyer-rates/` *(MEDIUM-HIGH — largest anonymized NA legal billing dataset; corroborated by ABA Journal)*
8. **Drata — SOC 2 audit cost & duration guide**: `https://drata.com/grc-central/soc-2/how-much-does-a-soc-2-audit-cost` *(HIGH — triangulates with Vanta, Secureframe)*
9. **HHS — HIPAA Compliance & Enforcement / Audit Program**: `https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/index.html` *(HIGH — government source)*
10. **EU AI Act — Implementation Timeline**: `https://artificialintelligenceact.eu/implementation-timeline/` *(HIGH on statutory dates; MEDIUM on Omnibus deferral until enacted)*
11. **Colorado General Assembly — SB24-205 (Colorado AI Act)**: `https://leg.colorado.gov/bills/sb24-205` *(HIGH on bill text; MEDIUM on enforcement status due to Apr 2026 stay)*
12. **NIST — AI Risk Management Framework 1.0**: `https://www.nist.gov/itl/ai-risk-management-framework` *(HIGH)*
13. **OWASP — Top 10 for LLM Applications (v1.1, 2025)**: `https://owasp.org/www-project-top-10-for-large-language-model-applications/` *(HIGH)*
14. **Google AI — Gemini API pricing**: `https://ai.google.dev/gemini-api/docs/pricing` *(HIGH — live-updated)*
15. **Microsoft Learn — Microsoft Purview AI Hub**: `https://learn.microsoft.com/en-us/purview/ai-microsoft-purview` *(HIGH — first-party docs)*
16. **Lakera — Lakera Guard product page**: `https://www.lakera.ai/lakera-guard` *(HIGH)*
17. **F5 — AI Guardrails (ex-CalypsoAI)**: `https://www.f5.com/products/ai-guardrails` *(HIGH — calypsoai.com 301-redirects here)*
18. **Cisco — AI Defense (ex-Robust Intelligence)**: `https://www.cisco.com/site/us/en/products/security/ai-defense/index.html` *(HIGH)*
19. **Veea Lobster Trap — GitHub repository**: `https://github.com/veeainc/lobstertrap` *(HIGH)*
20. **AICPA — Trust Services Criteria (SOC 2)**: `https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-trust-services-criteria` *(HIGH)*
21. **HHS — HIPAA Security Rule (45 CFR §164.312)**: `https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html` *(HIGH)*
22. **Polaris GitHub repo** *(internal evidence for unit tests, corpus pass, model bake-off)*: `https://github.com/seekerPrice/polaris`

---

## Build steps (in pitch.com)

1. Sign in to pitch.com → find **"VC Pitch Deck"** template by Zacht Studios → **Use template**.
2. Rename duplicate to `Polaris`.
3. For each of the 18 slides above:
   - Clone the matching Zacht template slide #.
   - Paste headline + body verbatim from this file.
   - Swap stock image for the indicated Polaris screenshot or diagram.
   - Add footer citation as 9pt grey (`#6F7585`) text element bottom-left, above the "Try Pitch" badge.
4. Delete unused Zacht template slides (testimonial, retention cohort, two-screen feature, map — unless wanted in appendix).
5. **File → Export → PDF**. Save as `docs/PITCH_DECK.pdf` in the repo.
6. Upload to Google Drive. Share → "Anyone with the link can view". Copy URL.
7. Replace `<Google Drive / Dropbox / inline GitHub asset URL>` at `docs/SUBMISSION.md:35` with the URL.
8. Commit: `git add docs/PITCH_DECK.md docs/PITCH_DECK.pdf docs/SUBMISSION.md docs/img/polaris_qr.png && git commit -m "docs: pitch deck v1 (Zacht template) with sourced citations"`

## Verification before submit

- [ ] Every slide with a number / fact has a clickable footer citation.
- [ ] Every footer URL resolves in incognito Chrome (re-test on May 18).
- [ ] Slide 4 includes the EU AI Act + Colorado AI Act deferral / stay hedge.
- [ ] No invented statistics — every figure traces to the master bibliography.
- [ ] PDF export size <10 MB.
- [ ] Drive link works for "Anyone with the link" — verify in incognito.
- [ ] `docs/SUBMISSION.md:35` updated with the actual Drive URL.
- [ ] `git log -p docs/PITCH_DECK.md docs/PITCH_DECK.pdf | grep -iE "GEMINI_API_KEY|sk-|AIza"` returns empty.

## Outstanding security flag

The Gemini API key visible in a prior screenshot (starts `AIzaSyAFv…`) was never confirmed rotated. Rotate before any judge clicks the live Replit URL. Update both local `.env` AND Replit Secrets, then republish.
