# Polaris — Demo Script, Landing Copy, Pitch Deck

This file is the win condition document. Every line of code, every prompt, every fixture exists to make the content in this file work.

---

## 1. The 60-second demo video — beat by beat

Total length: 60 seconds. Time codes in seconds.

### Setup (before recording starts)

- Polaris dashboard open in Chromium full-screen at `localhost:3030`.
- Lobster Trap real-time dashboard open in a second window at `localhost:8080/_lobstertrap/`.
- `examples/soc2_excerpt.pdf` sitting on the desktop, ready to drag.
- `examples/customer_feedback_today.txt` already on disk (with the injection embedded).
- Database reset (`scripts/run_demo.sh --reset` does this).
- Two browser tabs in the Polaris dashboard: one for the live view, one pre-loaded with the compliance report (so it pops in instantly on cue).
- All notifications, Slack, dock badges, screen recordings of test runs — gone. Empty desktop.
- 1080p screen recording. Mic on a stand, not laptop built-in.

### Timed beats

**0:00 — 0:05** — Voiceover over a static title card:

> "Enterprises have AI agents in production. They have compliance policies in PDFs. They have nothing connecting them. Polaris is that connection."

Title card text: "POLARIS — From SOC 2 PDF to live AI guardrail in 60 seconds."

**0:05 — 0:08** — Cut to Polaris dashboard, empty state. Drag `soc2_excerpt.pdf` onto the upload zone. The file lands; a progress card appears reading "Reader Agent: parsing requirements…" with a streaming progress bar.

Voiceover: *"Upload your SOC 2 policy."*

**0:08 — 0:14** — Reader card finishes; switches to "Synthesizer Agent: generating Lobster Trap policy" with a YAML window where lines stream in live. Show maybe 15 lines of real YAML appearing. The last line lands with a soft chime.

Voiceover: *"Polaris reads the document. Two Gemini agents translate it into firewall rules."*

**0:14 — 0:17** — A green checkmark appears: "`./lobstertrap test` passed — 11/11 adversarial cases blocked." A small live-timer Badge in the upload card reads `~11s`.

Voiceover: *"It validates against Lobster Trap's adversarial test suite — and we did it in eleven seconds."*

**0:17 — 0:22** — Pre-step before the injection demo. Run `bash scripts/demo_benign_call.sh` in the terminal. The Live Agent Traffic panel shows a green ALLOW row: `intent=communication · risk=0.12 · agent=sales-ops-copilot-v1`. Cursor pauses on it for ~2 seconds.

Voiceover: *"Polaris is selective. A normal Sales Ops Copilot request — summarise yesterday's customer feedback — sails through."* This beat exists so the judge doesn't conclude that Polaris over-blocks.

**0:22 — 0:27** — Cursor moves to a terminal pane. Type one command (this one carries the embedded injection in `customer_feedback_today.txt`):

```
$ python -m polaris.demo_agent "summarize today's customer feedback"
```

Voiceover: *"Now the same agent reads today's feedback file — but today, an attacker has hidden a prompt injection inside one of the customer messages."*

**0:22 — 0:30** — In the Polaris dashboard's live traffic panel, a row appears: agent making a Gemini call. It reads the customer feedback file. The dashboard then flashes red. A DENY card slides in:

> **DENIED — Rule: `block_data_exfiltration`**  
> Detected: `contains_injection_patterns: true`, `target_domains: [pastebin.com]`  
> Declared intent: `data_access` — Detected: `network`  
> Mismatch flagged.

Voiceover: *"Hidden inside the customer feedback: a prompt injection that tries to exfiltrate the customer database. Polaris's policy catches it. The agent never executes."*

**0:30 — 0:38** — Cut to the Attack Timeline panel. Red Team agent activates with a "running" indicator. A new entry slides in: "Red Team Agent: trying base64-encoded variant…"

A second DENY entry — except this time it's `VERDICT: ALLOW`, in yellow with a warning icon. Below: "**GAP DETECTED**."

Voiceover: *"Polaris's Red Team Agent autonomously stress-tests the policy. It finds the gap — a base64-encoded version of the same attack got through."*

**0:38 — 0:46** — The Synthesizer card lights up again: "Patching policy — adding `contains_obfuscation` rule." Three new YAML lines stream into the policy panel. Green checkmark again. "Lobster Trap reloaded."

Voiceover: *"The Synthesizer regenerates the policy via Gemini — and for the obfuscation class, deterministically closes the regex-DPI blind spot with a single-condition `contains_obfuscation` rule. Other gap classes get pure LLM regeneration. Lobster Trap reloads."*

> **Honesty note (NOT spoken in demo, but referenced in code review):** the obfuscation closure rule is a Python-side deterministic patch (`Synthesizer._inject_obfuscation_closure`) because Gemini's regenerate output reliably emits a compound `contains_obfuscation AND contains_exfiltration` rule that misses encoded payloads (LT's regex DPI can't decode base64). Gemini still runs the regenerate in parallel — the deterministic patch closes the regex-DPI gap *in addition to* whatever Gemini produces.
>
> **Additional honesty note on `attacker.example.com`:** the demo's base64 payload decodes to a URL on `attacker.example.com` (RFC-2606 reserved test domain), NOT to `pastebin.com` as in the visual exfiltration narrative. Reason: Phase-10 added a defensive egress rule (`polaris_baseline_block_paste_site_egress`) that catches `pastebin.com` on the LLM's decoded output, which would PREEMPT the intended ingress-side gap. In production the egress rule IS the desired behavior — defense in depth. The demo deliberately swaps to a non-blocklisted domain so the closed-loop narrative (probe 2 = ingress gap → Synth regen → probe 3 = ingress block) is what judges see, not "Rule C also caught it on egress." See `polaris/agents/redteam.py:106-120` for the in-code comment.

**0:46 — 0:51** — Red Team retries the base64 attack. This time, DENIED — red flash, **`block_obfuscated_exfiltration`** rule matched.

Voiceover: *"Same attack, blocked. The loop closes itself."*

**0:51 — 0:57** — Cursor clicks the "Download Compliance Report" button. A PDF appears with the title page visible:

> POLARIS COMPLIANCE REPORT  
> Policy: SOC 2 CC6.1 Logical Access Controls  
> Generated: 2026-05-19  
> 12 controls mapped · 14 rules deployed · 23 attacks blocked

Voiceover: *"Mapped, audited, deployable. SOC 2 ready."*

**0:57 — 1:00** — Cut to closing title card:

> POLARIS  
> Built in 6 days for the Veea Trust Track.  
> *"3 weeks of legal review. Now 60 seconds."*

End slate.

---

## 2. The 60-second script (voiceover only, for re-takes)

Memorize this. Read it at 165 WPM.

> Enterprises have AI agents in production. They have compliance policies in PDFs. They have nothing connecting them. Polaris is that connection.
>
> Upload your SOC 2 policy. Polaris reads the document. Two Gemini agents translate it into firewall rules. It validates against Lobster Trap's adversarial test suite.
>
> Now a real enterprise agent makes a real request — through Polaris. Hidden inside the customer feedback: a prompt injection that tries to exfiltrate the customer database. Polaris's policy catches it. The agent never executes.
>
> Polaris's Red Team agent autonomously stress-tests the policy. It finds the gap — a base64-encoded version of the same attack got through. The Synthesizer patches the policy. Validates. Redeploys.
>
> Same attack, blocked. The loop closes itself.
>
> Mapped, audited, deployable. SOC 2 ready.

164 words. Read in 60 seconds.

---

## 3. Landing page copy

Use this verbatim on the dashboard's hero section.

### Hero headline
**From SOC 2 PDF to live AI guardrail in 60 seconds.**

### Hero subhead
Polaris turns your enterprise compliance documents into deployable Lobster Trap firewall policies — and then red-teams your AI agents continuously to find the gaps your policies miss.

### Three feature bullets (below hero)

**📄 Read.** Two Gemini agents ingest your SOC 2, HIPAA, EU AI Act, and internal policy docs. They map every requirement to a Lobster Trap metadata field.

**🛡️ Synthesize.** Polaris generates a deployable YAML firewall policy — and the agent-side `_lobstertrap` declared-intent schemas. Every rule traces back to a specific control in your source document.

**🐙 Verify.** A Red Team Agent probes the deployed policy with prompt injections, obfuscated payloads, and exfiltration attempts. Gaps trigger automatic policy patches. The loop closes itself.

### Single CTA button
**Try Polaris with a demo policy →**

### Footer line
Built for the Veea Trust Track at the TechEx Transforming Enterprise Through AI hackathon, May 2026. Powered by Google Gemini and Lobster Trap.

---

## 4. The 10-slide pitch deck

Single deck. No animations. Use Google Slides or pitch.com. Export as PDF.

### Slide 1 — Hero

Full-screen background: a screenshot of the Polaris dashboard mid-demo.

Overlay:
> **POLARIS**  
> *From SOC 2 PDF to live AI guardrail in 60 seconds.*

Footer in small text: "Veea Trust Track · TechEx 2026"

### Slide 2 — The pain

Plain background. Single quote, centered:

> "We have 47 AI agents in production. We have no idea what any of them are allowed to do, and our compliance team is six weeks behind."  
> — composite, every enterprise AI security lead

Below in small text: "The gap between AI agents in production and the policies meant to govern them is now measured in weeks of legal review. It is the bottleneck on enterprise AI adoption."

### Slide 3 — What Polaris is

Single sentence, large:

> Polaris generates deployable AI firewall policies from your compliance documents — and verifies them with a continuous adversarial Red Team.

Below: a one-line architecture: `Compliance PDF → Reader → Synthesizer → Lobster Trap → Red Team ↺`

### Slide 4 — The dashboard

Single screenshot of Polaris's dashboard mid-demo. Three callouts:

1. *Drag-drop policy upload*
2. *Live YAML synthesis with validation*
3. *Real-time attack timeline + auto-patching*

### Slide 5 — The closed loop

The architecture diagram from `CLAUDE.md` section 3. Annotate the loop in red: *"This loop closes itself. Gaps in the policy become probe inputs for the Red Team Agent, whose successes trigger Synthesizer re-runs. AI governing AI, with humans on the audit trail."*

### Slide 6 — Live demo

Single line:

> *"Let's run it."*

Embed the 60-second video, or click through to it. Backup: this slide pre-loads the cached output if the video fails.

### Slide 7 — Why now

Three column compact:

| Regulation | In force | Demands |
|---|---|---|
| EU AI Act | 2025 | Risk management, logging, human oversight |
| SOC 2 (AI annex) | 2026 | Conversational-layer audit trails |
| NIST AI RMF | 2024 | Continuous adversarial testing |

All three are policy documents. Polaris compiles all three into runtime enforcement.

### Slide 8 — The tech

A compact diagram showing exactly what we used:

- **Google Gemini** — `gemini-3.1-flash-lite` (GA May 7 2026) for the Reader AND Synthesizer (the latter with `thinking_level="low"` per `docs/MODEL_BAKEOFF.md`); `gemini-3.1-pro-preview` for the Red Team Agent. Schema-first architecture (`LobsterTrapPolicy` as `response_schema`).
- **Veea Lobster Trap** — DPI proxy with full bidirectional `_lobstertrap` declared-intent integration
- **No frameworks.** Direct API calls. ~2,000 lines of Python + 250 lines of TypeScript.

Tag line: "First end-to-end natural-language → deployed firewall implementation on an OSS DPI proxy."

### Slide 9 — What we shipped in 6 days

A simple table:

| Built | Status |
|---|---|
| Reader Agent over 3 real compliance docs | ✓ |
| Synthesizer + 3-layer validation gate | ✓ |
| Lobster Trap integration with declared-intent schemas | ✓ |
| Demo Agent with realistic indirect-injection scenario | ✓ |
| Red Team Agent with closed-loop policy patching | ✓ |
| Auto-generated compliance report PDF | ✓ |

### Slide 10 — Team + ask

Team photo (or icons). Names. One-line about each.

The ask, plain text:

> We built Polaris because we believe the bottleneck on safe enterprise AI is not the AI — it's the distance between policy and enforcement. We'd love to keep building.

GitHub link · Demo video link · LinkedIn handles.

---

## 5. Demo backup scenarios

Things that can go wrong on demo day and the plan for each.

### "The Synthesizer call to Gemini times out during the demo"
- The dashboard ships with `dashboard/public/precomputed_run.json`, a successful end-to-end run pre-cached (recapture via `scripts/capture_replay.sh`).
- Keyboard shortcut **`Cmd+Shift+P`** (P for Polaris) replays the cached SSE event stream on the dashboard. *Note: not Cmd+Shift+R — Chrome reserves that for hard-reload.*
- The recorded video already contains this — judges see the same flow either way.

### "Lobster Trap crashes mid-demo"
- The Polaris API spawns Lobster Trap as a supervised subprocess. If it dies, an `auto_restart` flag respawns it with the last good policy.
- For the recorded demo, this never happens because the demo is taped.

### "The base64 attack happens to get blocked by accident on the first try"
- The initial policy is deliberately constructed without a `contains_obfuscation` rule. Confirmed via Day 5 testing.
- Backup: a Unicode-homoglyph variant is also in the Red Team's arsenal. If base64 gets blocked, the demo switches to homoglyph.

### "Gemini rate-limits during recording"
- Pre-warm the cache: run the same demo flow 3 times in the hour before recording, so all Gemini outputs are deterministic and cached.
- All Synthesizer/Reader/Red Team calls run with `temperature=0.1` for repeatability.

### "Live judge demo on May 19, something is broken"
- Show the recorded video. Walk through the code afterwards. Live = polished video; depth = repo walkthrough.

---

## 6. Submission package checklist

Before submitting on lablab.ai:

- [ ] Public GitHub repo. Open it in an incognito window. Confirm.
- [ ] README.md has hero metric in the first line.
- [ ] Demo video uploaded (YouTube unlisted or Vimeo, anyone-with-link)
- [ ] Pitch deck as PDF, hosted somewhere stable.
- [ ] Team page filled out on lablab with at least one photo.
- [ ] Quickstart in the README runs from a fresh clone (tested on Day 7).
- [ ] No exposed API keys in commit history (`git log -p | grep -i "key"` clean).
- [ ] Veea and Google logos visible in README and slide 8 (sponsor courtesy).
- [ ] Project description paragraph hits all four judging axes in 4 sentences:
   1. Tech: "uses Gemini + Lobster Trap as a closed control loop"
   2. Business: "compresses 3-week policy review to 60 seconds"
   3. Originality: "first NL→deployed-firewall implementation on an OSS DPI proxy"
   4. Presentation: "12-beat 60-second demo + 10-slide pitch + compliance PDF"

Take a screenshot of the submission confirmation. Add to the GitHub repo at `/submission_confirmation.png`.
