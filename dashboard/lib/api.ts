export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function uploadPolicy(file: File): Promise<{ job_id: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${API_BASE}/api/policies/generate`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`upload failed: ${r.status}`);
  return r.json();
}

export async function startRedTeam(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/api/redteam/start?job_id=${jobId}`, { method: "POST" });
}

export type PolarisEvent =
  | { type: "reader_progress"; job_id: string; status: string; n_requirements?: number }
  | { type: "synthesizer_progress"; job_id: string; status: string; passed?: boolean; summary?: string }
  | { type: "lobstertrap_deployed"; job_id: string; generation?: number }
  | { type: "lobstertrap_reloaded"; job_id: string }
  | { type: "audit_log_entry"; job_id: string; entry: AuditEntry }
  | { type: "redteam_probe_started"; job_id: string; probe: ProbeShape }
  | { type: "redteam_probe_result"; job_id: string; result: { probe: ProbeShape; actual_verdict: string; is_gap: boolean } }
  | { type: "policy_hash"; job_id: string; sha256: string };

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
