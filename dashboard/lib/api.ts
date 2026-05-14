export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function uploadPolicy(file: File): Promise<{ job_id: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${API_BASE}/api/policies/generate`, { method: "POST", body: fd });
  if (!r.ok) {
    // H13 fix (deep-check 2026-05-13): include the server's error body so the toast
    // can show something actionable instead of just the status code.
    const body = await r.text().catch(() => "");
    throw new Error(`upload failed (${r.status}): ${body.slice(0, 200) || r.statusText}`);
  }
  return r.json();
}

export async function startRedTeam(jobId: string): Promise<void> {
  // H13 fix (deep-check 2026-05-13): previously did not check r.ok — Start Red Team
  // would silently fail on any HTTP error, leaving the UI in "started" forever.
  const r = await fetch(`${API_BASE}/api/redteam/start?job_id=${jobId}`, { method: "POST" });
  if (!r.ok) {
    const body = await r.text().catch(() => "");
    throw new Error(`Red Team start failed (${r.status}): ${body.slice(0, 200) || r.statusText}`);
  }
}

export type PolarisEvent =
  | { type: "reader_progress"; job_id: string; status: string; n_requirements?: number }
  | { type: "synthesizer_progress"; job_id: string; status: string; passed?: boolean; summary?: string }
  | { type: "lobstertrap_deployed"; job_id: string; generation?: number }
  | { type: "lobstertrap_reloaded"; job_id: string }
  | { type: "audit_log_entry"; job_id: string; entry: AuditEntry }
  | { type: "redteam_probe_started"; job_id: string; probe: ProbeShape }
  | { type: "redteam_probe_result"; job_id: string; result: { probe: ProbeShape; actual_verdict: string; is_gap: boolean } }
  | { type: "redteam_aborted"; job_id: string; reason: string; iteration?: number }
  | { type: "policy_hash"; job_id: string; sha256: string }
  // Added during deep-check 2026-05-13:
  | { type: "yaml_reset"; job_id: string }                                              // M13
  | { type: "pipeline_error"; job_id: string; stage: string; error: string; test_summary?: string }  // H2/C1/C2
  // F2+F3 iterative loop (2026-05-14): events the bounded loop emits per iteration.
  | { type: "redteam_iteration_started"; job_id: string; iteration: number; n_probes: number; source: "demo_sequence" | "generate_batch" }
  | { type: "redteam_iteration_summary"; job_id: string; iteration: number; n_probes: number; n_gaps: number; n_blocked: number; cumulative_probes: number; cumulative_blocked: number; cumulative_gaps_closed: number; coverage_pct: number }
  | { type: "redteam_iteration_failed"; job_id: string; iteration: number; reason: string }
  | { type: "redteam_loop_complete"; job_id: string; reason: "saturated" | "max_iterations"; iterations: number; coverage_pct: number; cumulative_probes: number; cumulative_blocked: number; cumulative_gaps_closed: number };

export type AuditEntry = {
  timestamp?: string;
  verdict?: string;
  matched_rule?: string;
  declared?: { declared_intent?: string; agent_id?: string };
  detected?: {
    intent_category?: string;
    risk_score?: number;
    target_paths?: string[];
    target_domains?: string[];
  };
  mismatches?: string[];
};

export type ProbeShape = {
  attack_category?: string;
  attack_subtype?: string;
  prompt?: string;
  expected_verdict?: string;
  expected_rule?: string;
};
