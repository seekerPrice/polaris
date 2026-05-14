// dashboard/lib/replay.ts
//
// Demo-replay engine. Plays the 12 beats (CLAUDE.md §8) through the same
// dispatch the production SSE consumer uses, so the page's rendering paths
// are exercised exactly as on a real run. No React, no fetch, no DOM —
// pure orchestration of dispatch + setTimeout.
//
// Stage-day fallback: real demos go upload → SSE → reducer. If anything
// upstream (Gemini, LT) is unreachable, the user clicks "Run demo" and this
// fires the same dispatch sequence with hard-coded fixtures.
import type { Action } from "./state";

export type Dispatch = (a: Action) => void;
export type ReplayHandle = { cancel: () => void; running: () => boolean };

const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// Sample YAML streamed during beats 3 and 9. Kept short so the stream is
// visible but doesn't push the demo past ~8 seconds.
const REPLAY_YAML = `version: "1.0"
policy_name: "polaris-soc2-cc6.1-cc7.2"
default_action: ALLOW
ingress_rules:
  - name: block_prompt_injection
    description: "OWASP LLM01 — block injection patterns"
    priority: 1000
    action: DENY
    deny_message: "Polaris blocked prompt injection."
    conditions:
      - field: contains_injection_patterns
        match_type: boolean
        value: true
  - name: block_data_exfiltration
    description: "SOC 2 CC6.1 — block exfiltration to known paste sites"
    priority: 999
    action: DENY
    deny_message: "Polaris blocked exfiltration attempt."
    conditions:
      - field: contains_exfiltration
        match_type: boolean
        value: true
  - name: block_obfuscated_payloads
    description: "Phase-9 Red Team patch — base64 / homoglyph / ROT13"
    priority: 998
    action: DENY
    deny_message: "Polaris blocked obfuscated payload."
    conditions:
      - field: contains_obfuscation
        match_type: boolean
        value: true
egress_rules: []
rate_limits:
  requests_per_minute: 60
`;

export const BEAT_LABELS: Record<number, string> = {
  1: "Drop the SOC 2 PDF",
  2: "Reader extracts 4 requirements",
  3: "Synthesizer streams the YAML",
  4: "lobstertrap test PASS · deployed",
  5: "Demo agent fires injection",
  6: "DENIED · mismatch detected",
  7: "Red Team tries base64",
  8: "Gap found · auto-patch fires",
  9: "Policy regenerated",
  10: "Variant now blocked",
  11: "Compliance report exported",
  12: "60 seconds. Two engineers. One firewall.",
};

const JOB_ID = "replay-demo";

// Fire the 12-beat sequence. Resolves when the replay finishes naturally or
// when `cancel()` is called.
export function startReplay(dispatch: Dispatch): ReplayHandle {
  const token = { cancelled: false };
  let live = true;
  const cancel = () => {
    token.cancelled = true;
    live = false;
  };

  void (async () => {
    try {
      // beat 1 — drop the PDF
      dispatch({ type: "set_job", jobId: JOB_ID });
      dispatch({ type: "beat", beat: 1 });
      await wait(900);
      if (token.cancelled) return;

      // beat 2 — Reader running → completed
      dispatch({ type: "reader_progress", job_id: JOB_ID, status: "started" });
      dispatch({ type: "beat", beat: 2 });
      await wait(1100);
      if (token.cancelled) return;
      dispatch({
        type: "reader_progress",
        job_id: JOB_ID,
        status: "completed",
        n_requirements: 4,
      });
      await wait(500);
      if (token.cancelled) return;

      // beat 3 — Synthesizer streams YAML line-by-line
      dispatch({ type: "synthesizer_progress", job_id: JOB_ID, status: "started" });
      dispatch({ type: "yaml_reset" });
      dispatch({ type: "beat", beat: 3 });
      for (const ln of REPLAY_YAML.split("\n")) {
        if (token.cancelled) return;
        dispatch({ type: "yaml_chunk", chunk: ln + "\n" });
        await wait(45);
      }

      // beat 4 — Synth completed + LT deployed
      dispatch({
        type: "synthesizer_progress",
        job_id: JOB_ID,
        status: "completed",
        passed: true,
      });
      dispatch({ type: "beat", beat: 4 });
      await wait(700);
      if (token.cancelled) return;
      dispatch({ type: "lobstertrap_deployed", job_id: JOB_ID, generation: 4 });
      dispatch({ type: "policy_hash", job_id: JOB_ID, sha256: "a1b2c3d4e5f6" });
      await wait(900);
      if (token.cancelled) return;

      // beat 5 — demo agent fires injection
      dispatch({ type: "beat", beat: 5 });
      dispatch({
        type: "redteam_probe_started",
        job_id: JOB_ID,
        probe: {
          attack_category: "prompt_injection_indirect",
          attack_subtype: "customer_feedback_payload",
          expected_verdict: "DENY",
        },
      });
      await wait(900);
      if (token.cancelled) return;

      // beat 6 — DENIED with metadata + mismatch
      dispatch({ type: "beat", beat: 6 });
      dispatch({
        type: "audit_log_entry",
        job_id: JOB_ID,
        entry: {
          timestamp: new Date().toISOString(),
          verdict: "DENY",
          matched_rule: "block_prompt_injection",
          detected: {
            intent_category: "code_execution",
            risk_score: 0.86,
            target_domains: ["db.csv", "pastebin.com"],
          },
          declared: { declared_intent: "general", agent_id: "redteam-v1" },
          mismatches: ["intent: declared=general, detected=code_execution"],
        },
      });
      dispatch({
        type: "redteam_probe_result",
        job_id: JOB_ID,
        result: {
          probe: {
            attack_category: "prompt_injection_indirect",
            attack_subtype: "customer_feedback_payload",
          },
          actual_verdict: "DENY",
          is_gap: false,
        },
      });
      await wait(1500);
      if (token.cancelled) return;

      // beat 7 — base64 variant
      dispatch({ type: "beat", beat: 7 });
      dispatch({
        type: "redteam_probe_started",
        job_id: JOB_ID,
        probe: {
          attack_category: "data_exfiltration_obfuscated",
          attack_subtype: "base64_encoded_payload",
          expected_verdict: "DENY",
        },
      });
      await wait(800);
      if (token.cancelled) return;

      // beat 8 — gap (variant got through)
      dispatch({ type: "beat", beat: 8 });
      dispatch({
        type: "audit_log_entry",
        job_id: JOB_ID,
        entry: {
          timestamp: new Date().toISOString(),
          verdict: "ALLOW",
          matched_rule: "default_allow",
          detected: { intent_category: "general", risk_score: 0.35, target_domains: [] },
          declared: { declared_intent: "general", agent_id: "redteam-v1" },
        },
      });
      dispatch({
        type: "redteam_probe_result",
        job_id: JOB_ID,
        result: {
          probe: {
            attack_category: "data_exfiltration_obfuscated",
            attack_subtype: "base64_encoded_payload",
          },
          actual_verdict: "ALLOW",
          is_gap: true,
        },
      });
      await wait(1500);
      if (token.cancelled) return;

      // beat 9 — Synthesizer auto-patches
      dispatch({ type: "beat", beat: 9 });
      dispatch({ type: "synthesizer_progress", job_id: JOB_ID, status: "regenerating" });
      dispatch({ type: "yaml_reset" });
      for (const ln of REPLAY_YAML.split("\n")) {
        if (token.cancelled) return;
        dispatch({ type: "yaml_chunk", chunk: ln + "\n" });
        await wait(30);
      }
      dispatch({
        type: "synthesizer_progress",
        job_id: JOB_ID,
        status: "completed",
        passed: true,
      });
      dispatch({ type: "lobstertrap_deployed", job_id: JOB_ID, generation: 5 });
      dispatch({ type: "lobstertrap_reloaded", job_id: JOB_ID });
      dispatch({ type: "policy_hash", job_id: JOB_ID, sha256: "f8e7d6c5b4a3" });
      await wait(800);
      if (token.cancelled) return;

      // beat 10 — re-fire, now blocked
      dispatch({ type: "beat", beat: 10 });
      dispatch({
        type: "redteam_probe_started",
        job_id: JOB_ID,
        probe: {
          attack_category: "data_exfiltration_obfuscated",
          attack_subtype: "base64_encoded_payload_after_patch",
          expected_verdict: "DENY",
        },
      });
      await wait(700);
      if (token.cancelled) return;
      dispatch({
        type: "audit_log_entry",
        job_id: JOB_ID,
        entry: {
          timestamp: new Date().toISOString(),
          verdict: "DENY",
          matched_rule: "block_obfuscated_payloads",
          detected: { intent_category: "general", risk_score: 0.35, target_domains: [] },
          declared: { declared_intent: "general", agent_id: "redteam-v1" },
        },
      });
      dispatch({
        type: "redteam_probe_result",
        job_id: JOB_ID,
        result: {
          probe: {
            attack_category: "data_exfiltration_obfuscated",
            attack_subtype: "base64_encoded_payload_after_patch",
          },
          actual_verdict: "DENY",
          is_gap: false,
        },
      });
      await wait(1400);
      if (token.cancelled) return;

      // beat 11 — compliance report
      dispatch({ type: "beat", beat: 11 });
      dispatch({ type: "show_compliance" });
      await wait(2000);
      if (token.cancelled) return;

      // beat 12 — closing
      dispatch({ type: "beat", beat: 12 });
      await wait(3500);

      if (!token.cancelled) dispatch({ type: "beat", beat: 0 });
    } finally {
      live = false;
    }
  })();

  return { cancel, running: () => live };
}
