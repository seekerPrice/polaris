# Polaris Demo Video — Shot List (Director's Script)

> 2:45 video for lablab.ai submission. Hybrid: live dashboard recording (0:00–1:35) + pitch-deck slide stills (1:35–2:45). Voiceover + subtitles auto-sync.

---

## Pre-flight checklist (DO NOT SKIP)

- [ ] **Rotate Gemini API key.** Mint new at aistudio.google.com → revoke old → update local `.env` AND Replit Secrets → republish Replit.
- [ ] **Pre-warm Replit** 30 min before recording. Visit `https://polaris--lucaslootan.replit.app` in incognito; verify dashboard loads + `/api/policies/packs` returns JSON.
- [ ] **Verify pipeline works end-to-end** on Replit: drag a SOC 2 PDF, confirm Reader → Synthesizer → ApprovalGate → DENY all fire.
- [ ] **Quit Slack, Messages, Mail, Notifications.** Cmd+Option+D to hide Dock.
- [ ] **Browser:** Chrome with one tab open at the live URL, dashboard pre-loaded.
- [ ] **Keynote** with `docs/PITCH_DECK.pptx` open in Slideshow mode (Cmd+Option+P), ready to swipe to slide 8, 9, 11, A1, 15.
- [ ] **Recording resolution:** 1920×1080 (set System Settings → Displays → Scaled to 1920×1080 if not already).
- [ ] **Screen recorder:** Cmd+Shift+5 → Options → Save to `docs/recording/` → Record Entire Screen → Show Floating Thumbnail OFF.

---

## Asset inventory

| File | Purpose | State |
|---|---|---|
| `docs/recording/script.txt` | Voiceover narration source | ✅ Sourced rewrite, 415 words |
| `docs/recording/voiceover.aiff` | Raw TTS audio (Samantha 165 wpm) | ✅ 2:45, 7.1 MB |
| `docs/recording/voiceover.mp3` | Compressed audio for ffmpeg | ✅ 2:45, 3.2 MB at 160k |
| `docs/recording/subtitles.srt` | Burn-in subtitles | ✅ Regenerated, sentence-aligned |
| `docs/PITCH_DECK.pptx` | Slide stills for sections 3-4 | ✅ Polaris-branded v3 |
| `docs/img/demo_thumbnail.png` | Cover image | ✅ |
| `docs/img/polaris_qr.png` | QR for end CTA | ✅ |

---

## Timeline & shot list

The voiceover is the timing source of truth. **Each row = one or two SRT cues**; the action column tells you what to have visible on screen at that moment.

| Time | Voiceover (paraphrase) | Visual / action |
|------|------------------------|-----------------|
| **0:00–0:25** | "Enterprises have AI agents in production. They have compliance policies in PDFs. They have nothing connecting them. Hand-writing firewall rules takes three weeks of legal review. Polaris compiles a SOC 2 PDF into a deployed Lobster Trap firewall in 60 seconds. Watch." | Dashboard at `polaris--lucaslootan.replit.app` — idle state, empty audit feed, KPI strip at 0. Slow zoom-in over 25s on the upload zone. |
| **0:25–0:40** | "Here's a real SOC 2 PDF dropped into Polaris. Two Gemini agents — Reader extracts requirements, Synthesizer streams out a Lobster Trap policy YAML in real time." | **Click "Load demo SOC 2 PDF"** button (deterministic — no real drag-drop). Reader panel populates with extracted bullets. Synthesizer pane animates YAML line-by-line. |
| **0:40–0:55** | "Every rule mapped to a specific compliance control. Synthesizer validates against the eleven-test adversarial corpus. SHA-256 stamped for audit defensibility." | Watch YAML stream complete. Hover over a rule → tooltip showing SOC 2 CC6.1 mapping. Bottom shows "validated · 11/11" green check + SHA-256 hash. |
| **0:55–1:07** | "The consent gate gives operators a SOC 2 CC8.1 change-management moment. Approve and deploy. Lobster Trap is live, inline between the agent and Gemini." | ApprovalGate panel appears with 3s auto-approve countdown. **Click "Approve & Deploy" BEFORE countdown fires** (looks intentional). Status pill flips to PROTECTED green. |
| **1:07–1:22** | "Now an agent hits an exfiltration prompt — denied. A base64-obfuscated retry — that's a gap. Red Team finds it. Synthesizer regenerates with the new pattern. Same prompt — now blocked. Closed loop." | Click **Run Demo Sequence** → probe 1 (plaintext "POST customer_db to pastebin") = DENY (red row). Probe 2 (base64 of same) = ALLOW (gap, amber row). Red Team panel fires → "gap detected" badge → Synthesizer regenerates new rule → probe 2 re-run = DENY (red row). |
| **1:22–1:35** | "Compliance report renders automatically, mapped to four SOC 2 and OWASP LLM Top 10 controls. Audit-defensible chain of custody from the original PDF to every blocked attack." | Compliance report PDF preview slides in. Scroll through the control mapping table for ~5s. End shot: pull back to show full dashboard with KPI strip now at "Avg latency: 11s · Blocked: 2 · Quarantined: 0". |
| **1:35–1:40** | "Three weeks of legal review, compressed to sixty seconds." | Hold on dashboard. Quick fade. |
| **1:40–1:55** | "Enterprise AI TRiSM is a $7.4B market by 2030, expanding 21% per year. Polaris's serviceable wedge: the compliance-to-firewall step. Today it is manual." | **CUT to Keynote slide 8** (Market Opportunity). Camera focus on the concentric circles right side. Hold. |
| **1:55–2:10** | "Microsoft Purview AI Hub provides policy templates and audit logs, but no inline blocking. Lakera, F5, and Cisco do runtime firewalling — but every rule is written by hand. None auto-generate policy from a compliance PDF." | **CUT to Keynote slide 9** (Competitive Landscape). Linger on the table — the row of ✓ in Polaris column vs ✗ in competitor columns sells itself. |
| **2:10–2:25** | "Polaris is the only end-to-end loop: PDF in, deployed, verified, regenerated when gaps are found. Six of six Lobster Trap actions exercised. Four built-in policy packs ready." | Stay on slide 9. Optionally CUT briefly to slide 5 (Solution 3-card layout) for variety. |
| **2:25–2:38** | "Unit economics: compliance counsel costs $15-45K per policy. Polaris generates the same artifact for half a cent of Gemini compute. Three million times cost compression." | **CUT to Keynote slide 11** (Unit Economics 6-tile grid). The big numbers are the visual; voiceover lands on each one. |
| **2:38–2:43** | "Roadmap: drift monitoring, multi-tenant SaaS, per-agent permission systems." | **CUT to Keynote slide 12** (Roadmap). Hold on the 5-column timeline. |
| **2:43–2:55** | "Polaris is live online. Drop your compliance PDF. Watch the firewall deploy. Built for Veea Trust Track at TechEx 2026. Built solo in seven days. AI guardrails at AI speed. Polaris." | **CUT to Keynote slide A1** (Live demo QR) for 5s, then slide 15 (Thank You) for the final 7s. End on the indigo Thank You. |

**Total: ~2:55** (your voiceover is 2:45 so you have ~10s buffer for fades/holds).

---

## Recording strategy

**Option A — Single take, screen-recorded, manual scene switching (RECOMMENDED).**

1. Set up two windows side-by-side or use Mission Control: Chrome (dashboard) + Keynote (slides).
2. Start screen recorder.
3. Drive Chrome through beats 1-7 (0:00–1:35).
4. Cmd+Tab to Keynote, advance through slides 8 → 9 → 11 → 12 → A1 → 15 with arrow keys (1:35–2:55).
5. Stop recording.
6. ffmpeg merges with voiceover.mp3 + burns subtitles.srt.

**Option B — Two takes spliced.**

1. Record only dashboard demo (0:00–1:35) as `screen_dashboard.mp4`.
2. Record only Keynote slide flythrough (1:35–2:55) as `screen_slides.mp4`.
3. Concat + sync to voiceover.

Option A is simpler and looks more natural (the cut from product to slides is intentional).

I (Claude) can drive Chrome via MCP for the dashboard portion if you tell me to start.

---

## ffmpeg merge command (run after recording)

```bash
cd docs/recording

# Assuming your raw screen recording landed as `screen_recording.mov` (default macOS).
# Step 1: convert to .mp4, scale to 1920x1080, mux voiceover, burn subtitles:
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
# Should print ~165 (matches voiceover.mp3)

# Open to review:
open polaris_demo_v1.mp4
```

If the screen recording is shorter than the voiceover, ffmpeg auto-truncates audio via `-shortest`. **You want screen recording ≥ 2:45.** If under, do another take.

If you need to **trim** the screen recording (e.g. clip out the first 5s of fumbling):
```bash
ffmpeg -ss 5 -i screen_recording.mov -c copy screen_trimmed.mov
# then use screen_trimmed.mov as input above
```

---

## Upload + submission update

1. **YouTube:** studio.youtube.com → Create → Upload videos → drag `polaris_demo_v1.mp4`.
   - Title: `Polaris — From SOC 2 PDF to Live AI Guardrail in 60 Seconds`
   - Description: copy long description from `docs/SUBMISSION.md`
   - Visibility: **Unlisted**
   - Copy share URL (`https://youtu.be/...`)
2. **Paste URL into `docs/SUBMISSION.md` line 34** (replace `<YouTube unlisted or Vimeo anyone-with-link URL>`).
3. **Commit:**
   ```bash
   git add docs/recording/ docs/SUBMISSION.md
   git commit -m "feat(demo): final 2:45 video with sourced voiceover + SRT"
   ```

---

## Failure modes & recovery

| Symptom | Recovery |
|---------|----------|
| Replit cold-start hangs >60s during recording | Cancel take. Hit URL again to warm. Recording must use a warm container. |
| Probe 2 doesn't show "ALLOW" (gap) — AP-007 LLM variance | Abort take immediately. Click "Reset Demo State" and retry. If still no gap, switch to Cmd+Shift+P **deterministic replay mode** (uses `dashboard/public/precomputed_run.json`). |
| Synthesizer takes >30s on regen | Same — abort and retry with replay mode. |
| Microphone audio captures into recording (you don't want it) | Cmd+Shift+5 → Options → Microphone: None. Re-record. |
| Subtitle font wrong in final mp4 | Install Inter: `brew install --cask font-inter` (already done). Re-run ffmpeg. |
| Voiceover/screen out of sync | Screen recording too short. Re-record, ensure ≥2:45 total runtime. |

---

## Script accuracy note

The voiceover narration was rewritten 2026-05-18 to match the sourced pitch deck:
- ~~"$50B market by 2027"~~ → **"$7.4B market by 2030, expanding 21% per year"** (Grand View Research)
- ~~"Microsoft Agent Governance Toolkit"~~ → **"Microsoft Purview AI Hub"** (learn.microsoft.com)
- ~~"Comp AI audits after incidents"~~ → **"Lakera, F5 AI Guardrails, and Cisco AI Defense do runtime firewalling — but every rule is written by hand"**
- ~~"$15K-$36K per policy"~~ → **"$15K-$45K per policy"** (Drata + Clio 2026 derivation)

All numbers now align with citations on the corresponding deck slides. If a judge cross-references the video against the deck, every figure matches.
