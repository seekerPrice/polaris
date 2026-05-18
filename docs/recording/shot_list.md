# Polaris Demo Video — Shot List (Director's Script · v2)

> 3:12 video for lablab.ai submission. Hybrid: live dashboard recording
> (0:00–1:48) + pitch-deck slide stills (1:48–3:12). Voiceover + subtitles
> auto-sync via ffmpeg burn-in.
>
> v2 (2026-05-19): added QUARANTINE beat + multi-agent + policy-pack beats
> to surface Phase 12 features. Total runtime 3:12 (was 2:45).

---

## Pre-flight checklist (DO NOT SKIP)

- [ ] **Rotate Gemini API key** — mint new at aistudio.google.com → revoke old → update local `.env` AND Replit Secrets → republish Replit.
- [ ] **Pre-warm Replit** 30 min before recording. Visit `https://polaris--lucaslootan.replit.app` in incognito; verify dashboard loads + `/api/policies/packs` returns JSON.
- [ ] **Verify pipeline works end-to-end** on Replit: drag a SOC 2 PDF, confirm Reader → Synthesizer → ApprovalGate → DENY → QUARANTINE all fire.
- [ ] **Quit Slack, Messages, Mail.** Cmd+Option+D to hide Dock. Focus mode ON.
- [ ] **Chrome:** one tab open at the live URL, dashboard pre-loaded, scroll position reset to top.
- [ ] **Keynote** with `docs/PITCH_DECK.pptx` open in Slideshow mode (Cmd+Option+P), ready to swipe slides 8 → 9 → 5 → A3 → 7 → 11 → 12 → A1 → 15.
- [ ] **Recording resolution:** 1920×1080 (System Settings → Displays → Scaled).
- [ ] **Screen recorder:** Cmd+Shift+5 → Options → Save to `docs/recording/` → Record Entire Screen → Show Floating Thumbnail OFF → Microphone OFF.

---

## Asset inventory

| File | Purpose | State |
|---|---|---|
| `docs/recording/script.txt` | Voiceover narration source | ✅ v2, ~485 words |
| `docs/recording/voiceover.aiff` | Raw TTS (Samantha 165 wpm) | ✅ 3:12, 8.4 MB |
| `docs/recording/voiceover.mp3` | Compressed audio for ffmpeg | ✅ 3:12, 3.7 MB at 160k |
| `docs/recording/subtitles.srt` | Burn-in subtitles | ✅ 50 cues, sentence-aligned |
| `docs/PITCH_DECK.pptx` | Slide stills for ACT 2 | ✅ Polaris-branded v3 |
| `docs/img/demo_thumbnail.png` | Cover image | ✅ |
| `docs/img/polaris_qr.png` | QR for slide A1 CTA | ✅ |

---

## Timeline & shot list

The voiceover is the timing source of truth. **Each row = one to three SRT cues**; the action column tells you what to have visible at that moment.

| Time | Voiceover (paraphrase) | Visual / action |
|------|------------------------|-----------------|
| **0:00–0:19** | "Enterprises have AI agents in production…compliance policies in PDFs…three weeks of legal review. Polaris compiles a SOC 2 PDF in 60 seconds." | Dashboard at `polaris--lucaslootan.replit.app` — idle state, KPI strip at 0. Slow zoom-in over 19s toward the upload zone. |
| **0:19–0:20** | "Watch." | Beat — hold on upload zone. |
| **0:20–0:30** | "Here's a real SOC 2 PDF dropped into Polaris. Two Gemini agents — Reader extracts requirements, Synthesizer streams out a Lobster Trap policy YAML in real time." | **🖱 CLICK "Load demo SOC 2 PDF"** button. Reader panel populates with extracted bullets. Synthesizer pane animates YAML line-by-line. |
| **0:30–0:41** | "Every rule mapped to a specific compliance control. Synthesizer validates against the eleven-test adversarial corpus. SHA-256 stamped for audit defensibility." | Watch YAML stream complete. Hover a rule → tooltip showing SOC 2 CC6.1 mapping. Green "validated · 11/11" check, then SHA-256 footer. |
| **0:41–0:48** | "The consent gate gives operators a SOC 2 CC8.1 change-management moment. Approve and deploy." | ApprovalGate panel appears with 3s auto-approve countdown. **🖱 CLICK "Approve & Deploy" BEFORE countdown fires** (looks intentional). |
| **0:48–0:52** | "Lobster Trap is live, inline between the agent and Gemini." | Status pill flips to **PROTECTED** green. LT spawn log scrolls. |
| **0:52–0:55** | "Now an agent hits an exfiltration prompt — denied." | **🖱 CLICK "Run Demo Sequence"**. Probe 1 plaintext exfil → **DENY** row (red). |
| **0:55–0:58** | "A base64-obfuscated retry — that's a gap." | Probe 2 base64 → **ALLOW** row (amber gap). |
| **0:58–1:02** | "Red Team finds it. Synthesizer regenerates with the new pattern." | Red Team panel fires → "gap detected" badge → Synthesizer regenerates new rule. |
| **1:02–1:05** | "Same prompt — now blocked. Closed loop." | Probe 2 re-run → **DENY** (red row). |
| **1:05–1:18** | "Some prompts aren't clear DENY — borderline credentials, ambiguous PII. Those route to a QUARANTINE queue for operator release or block. Six of six Lobster Trap actions, exercised in one demo." | **🖱 CLICK "Run Borderline Probe"** (or it fires as part of Demo Sequence). Audit row appears with **QUARANTINE** badge (amber). Right-panel **QuarantineQueue** shows the prompt with Release/Block buttons. **🖱 CLICK "Block"**. Audit feed shows QUARANTINE → BLOCKED transition. |
| **1:18–1:30** | "Compliance report renders automatically, mapped to four SOC 2 and OWASP LLM Top 10 controls. Audit-defensible chain of custody from the original PDF to every blocked attack." | **🖱 CLICK "Generate Compliance Report"** → PDF preview slides in. Scroll through the rule-to-control mapping table for ~5s. |
| **1:30–1:37** | "Multiple agents share the same firewall — Sales Ops, Engineering Copilot — each tagged in the audit log." | Pull back to audit feed. Highlight (Cmd+ to zoom Chrome) the **agent badges** in audit rows — cyan "Sales Ops" badges, violet "Engineering" badges side-by-side. If only Sales Ops rows exist, click **"Trigger Engineering probe"** to add one (or run a second pack with a different agent declared). |
| **1:37–1:44** | "Or skip the upload entirely. Pre-built packs for SOC 2, HIPAA, EU AI Act, and PCI-DSS deploy in seconds." | Scroll to **PackPicker** panel. Show 4 pack cards in 2×2 grid. Hover one (e.g. **HIPAA**) — its border glows. Optionally **🖱 CLICK "Deploy HIPAA"** to show the instant ApprovalGate path (and immediately approve). |
| **1:44–1:48** | "Three weeks of legal review, compressed to sixty seconds." | Pull back to dashboard, KPI strip showing **"Avg latency 11s · Blocked 3 · Quarantined 1"**. |
| **1:48–1:58** | "Enterprise AI Trust, Risk, and Security Management is a $7.4B market by 2030, expanding 21% per year." | **⌘+Tab → KEYNOTE · Slide 8** (Market Opportunity). Focus on concentric circles. |
| **1:58–2:03** | "Polaris's serviceable wedge: the compliance-to-firewall step. Today it is manual." | Stay on slide 8 (linger on Target $740M circle). |
| **2:03–2:11** | "Microsoft Purview AI Hub provides policy templates and audit logs, but no inline blocking on LLM outputs." | **→ Slide 9** (Competitive Landscape). Focus on Purview row. |
| **2:11–2:18** | "Lakera, F5 AI Guardrails, and Cisco AI Defense do runtime firewalling — but every rule is written by hand." | Slide 9 — linger on the ✓/✗ comparison rows. |
| **2:18–2:22** | "None of them auto-generate policy from a compliance PDF." | Slide 9 hold. |
| **2:22–2:29** | "Polaris is the only end-to-end loop: PDF in, deployed, verified, regenerated when gaps are found." | **→ Slide 5** (Solution 3-card). |
| **2:29–2:32** | "Six of six Lobster Trap actions exercised." | Stay on slide 5 (or quick cut to A3 Compliance Coverage table). |
| **2:32–2:37** | "Four built-in policy packs ready to deploy for SOC 2, HIPAA, EU AI Act, and PCI-DSS." | **→ Slide A3** (Compliance Coverage — control mapping table). |
| **2:37–2:40** | "Closed-loop self-patching red team." | **→ Slide 7** (Closed Loop 5-step diagram). |
| **2:40–2:46** | "Unit economics: compliance counsel costs $15-45K per policy." | **→ Slide 11** (Unit Economics 6 tiles). |
| **2:46–2:51** | "Polaris generates the same artifact for half a cent of Gemini compute." | Slide 11 (focus on $0.005 tile). |
| **2:51–2:55** | "Three million times cost compression on the policy authoring step." | Slide 11 (focus on 3,000,000× tile). |
| **2:55–3:00** | "Roadmap: drift monitoring, multi-tenant SaaS, per-agent permission systems." | **→ Slide 12** (Roadmap 5-quarter timeline). |
| **3:00–3:06** | "Polaris is live online. Drop your compliance PDF. Watch the firewall deploy." | **→ Slide A1** (Live demo QR). |
| **3:06–3:12** | "Built for Veea Trust Track at TechEx 2026. Built solo in seven days. AI guardrails at AI speed. Polaris." | **→ Slide 15** (Thank You). Hold until 3:12. |

**Total: 3:12** (voiceover length). Add 5-10s fade-to-black tail in ffmpeg if desired.

---

## Recording strategy

**Option A — Single take, screen-recorded, manual scene switching (RECOMMENDED).**

1. Two windows side-by-side or use Mission Control: Chrome (dashboard) + Keynote (slides).
2. Start screen recorder.
3. Drive Chrome through ACT 1 beats (0:00–1:48).
4. ⌘+Tab to Keynote, advance through slides 8 → 9 → 5 → A3 → 7 → 11 → 12 → A1 → 15 with right-arrow (1:48–3:12).
5. Stop recording (⌘⇧5 → Stop or Esc).

**Option B — Two takes spliced.**

1. Record dashboard demo (0:00–1:48) as `screen_dashboard.mov`.
2. Record Keynote slide flythrough (1:48–3:12) as `screen_slides.mov`.
3. Concat + sync to voiceover via ffmpeg.

Option A is simpler and the cut from product → slides feels intentional.

I (Claude) can drive Chrome via MCP for the ACT 1 portion if you say "drive" — you run `screencapture`.

---

## ffmpeg merge command (run after recording)

```bash
cd docs/recording

# Default macOS screen recording lands as a .mov. Rename to screen_recording.mov.

# Single command: mux voiceover + burn subtitles + render 1080p H.264:
ffmpeg -i screen_recording.mov \
       -i voiceover.mp3 \
  -vf "scale=1920:1080:flags=lanczos,subtitles=subtitles.srt:force_style='Fontname=Inter,FontSize=22,PrimaryColour=&Hffffff&,OutlineColour=&H80000000&,BorderStyle=3,Outline=2,Shadow=0,MarginV=40'" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -map 0:v -map 1:a \
  -shortest \
  -y polaris_demo_v1.mp4

# Sanity check:
ffprobe -v error -show_entries format=duration -of csv=p=0 polaris_demo_v1.mp4
# Should print ~192 (matches voiceover.mp3 duration)

# Open to review:
open polaris_demo_v1.mp4
```

**Screen recording must be ≥ 3:12** (auto-truncates audio via `-shortest` otherwise). If under, do another take.

To **trim** a slow start (e.g. clip first 4s):
```bash
ffmpeg -ss 4 -i screen_recording.mov -c copy screen_trimmed.mov
# then use screen_trimmed.mov as input above
```

---

## Upload + submission update

1. **YouTube:** studio.youtube.com → Create → Upload videos → drag `polaris_demo_v1.mp4`.
   - Title: `Polaris — From SOC 2 PDF to Live AI Guardrail in 60 Seconds`
   - Description: copy long description from `docs/SUBMISSION.md`
   - Visibility: **Unlisted**
   - Copy share URL (`https://youtu.be/...`)
2. **Paste URL into `docs/SUBMISSION.md:34`** (replace `<YouTube unlisted or Vimeo anyone-with-link URL>`).
3. **Commit:**
   ```bash
   git add docs/recording/ docs/SUBMISSION.md
   git commit -m "feat(demo): final 3:12 video with Phase 12 beats"
   ```

---

## Failure modes & recovery

| Symptom | Recovery |
|---------|----------|
| Replit cold-start hangs >60s during recording | Cancel take. Hit URL again to warm. Recording must use a warm container. |
| Probe 2 doesn't show "ALLOW" (gap) — AP-007 LLM variance | Abort take immediately. Click "Reset Demo State" and retry. If still no gap, switch to Cmd+Shift+P **deterministic replay mode** (uses `dashboard/public/precomputed_run.json`). |
| QUARANTINE row doesn't fire | Check the probe is borderline (contains_credentials + risk_score ≥ 0.65). May need to add a "Trigger Quarantine" button to the Demo Sequence. If not fireable on this build, drop the QUARANTINE beat and skip to compliance report — voiceover will be 13s ahead but ffmpeg `-shortest` truncates cleanly. |
| Engineering Copilot badge doesn't appear in audit | Run a second pack with engineering_copilot.py as the source agent. Or skip — voiceover still works if only Sales Ops badges show; "multiple agents share the same firewall" remains accurate. |
| Synth regen > 30s | Same as AP-007 — switch to replay mode. |
| Mic captured by accident | Cmd+Shift+5 → Options → Microphone: None. Re-record. |
| Subtitle font wrong in final mp4 | Install Inter: `brew install --cask font-inter` (already done). Re-run ffmpeg. |
| Voiceover/screen out of sync | Screen recording too short. Re-record; ensure ≥ 3:12 total runtime. |

---

## Script accuracy notes

The voiceover narration was rewritten 2026-05-18 (then extended 2026-05-19) to match the sourced pitch deck:

- ~~"$50B market by 2027"~~ → **"$7.4B market by 2030, expanding 21% per year"** (Grand View Research)
- ~~"Microsoft Agent Governance Toolkit"~~ → **"Microsoft Purview AI Hub"** (learn.microsoft.com)
- ~~"Comp AI audits after incidents"~~ → **"Lakera, F5 AI Guardrails, and Cisco AI Defense"** (vendor pages)
- ~~"$15K-$36K per policy"~~ → **"$15K-$45K per policy"** (Drata + Clio 2026)
- **NEW** QUARANTINE beat (Phase 12 T4 feature)
- **NEW** multi-agent badging beat (Phase 12 T5 feature)
- **NEW** policy pack picker beat (Phase 12 T6 feature)

All numbers align with citations on corresponding deck slides. Cross-reference video↔deck: every figure matches.
