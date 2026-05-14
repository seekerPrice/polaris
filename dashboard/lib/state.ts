// dashboard/lib/state.ts
//
// Single source of truth for dashboard state. Pure data + reducer; no React, no
// fetch, no SSE — those concerns live in the orchestration layer (app/page.tsx).
//
// CONTRACT NOTE: the shape of `State`, the `PolarisEvent` union, and the
// reducer's case-by-case behavior must stay aligned with the SSE events the
// FastAPI backend publishes (see polaris/api/routes.py). Adding a new event
// type from the server requires adding a case here; removing a state field
// requires confirming no SSE consumer relies on it.
import type { AuditEntry, ProbeShape, PolarisEvent } from "./api";

// ---- view-only types (presentation-derived, not transported over SSE) ----
export type ProbeView = {
  phase: "started" | "result";
  probe?: { attack_category?: string; attack_subtype?: string };
  attack_category?: string;
  actual_verdict?: string;
  is_gap?: boolean;
};

// ---- state ----
export type State = {
  jobId: string | null;
  reader: { status: string; n: number };
  synth: { status: string; yaml: string; passed: boolean | null };
  audits: AuditEntry[];
  probes: ProbeView[];
  timing: { startedAt: number | null; deployedMs: number | null };
  policyHash: string | null;
  policiesGenerated: number;
  // Deep-check fixes (2026-05-13): surface error/connection state instead of
  // letting the UI sit at "idle" forever. Cleared on `set_job`.
  error: string | null;
  pipelineError: { stage: string; error: string; test_summary?: string } | null;
  sseStatus: "connected" | "reconnecting";
  isDragging: boolean;
  // Demo-only: replay engine progress + which beat overlay to show + whether to
  // render the compliance panel content (the replay engine sets these; real
  // backend traffic ignores them).
  beat: number;
  showComplianceReport: boolean;
};

// ---- actions ----
// Union of (a) PolarisEvent forwarded from SSE, and (b) local UI actions that
// only the page or replay engine dispatch.
export type LocalAction =
  | { type: "set_job"; jobId: string }
  | { type: "yaml_chunk"; chunk: string }
  | { type: "yaml_reset" }
  | { type: "client_error"; error: string | null }
  | { type: "sse_status"; status: "connected" | "reconnecting" }
  | { type: "drag"; value: boolean }
  | { type: "beat"; beat: number }
  | { type: "show_compliance" }
  | { type: "reset" };

export type Action = LocalAction | PolarisEvent;

// ---- initial state ----
export const INIT_STATE: State = {
  jobId: null,
  reader: { status: "idle", n: 0 },
  synth: { status: "idle", yaml: "", passed: null },
  audits: [],
  probes: [],
  timing: { startedAt: null, deployedMs: null },
  policyHash: null,
  policiesGenerated: 0,
  error: null,
  pipelineError: null,
  sseStatus: "connected",
  isDragging: false,
  beat: 0,
  showComplianceReport: false,
};

// ---- reducer ----
export function reducer(s: State, ev: Action): State {
  switch (ev.type) {
    case "set_job":
      // L42 fix: preserve the running counter; bump only on lobstertrap_deployed.
      return {
        ...INIT_STATE,
        jobId: ev.jobId,
        timing: { startedAt: Date.now(), deployedMs: null },
        policiesGenerated: s.policiesGenerated,
      };
    case "reader_progress":
      return { ...s, reader: { status: ev.status, n: ev.n_requirements ?? s.reader.n } };
    case "synthesizer_progress":
      return {
        ...s,
        synth: { ...s.synth, status: ev.status, passed: ev.passed ?? s.synth.passed },
      };
    case "lobstertrap_deployed": {
      const deployedMs =
        s.timing.startedAt !== null && s.timing.deployedMs === null
          ? Date.now() - s.timing.startedAt
          : s.timing.deployedMs;
      const isFirstDeployForJob = s.timing.deployedMs === null;
      return {
        ...s,
        synth: { ...s.synth, status: "deployed" },
        timing: { ...s.timing, deployedMs },
        policiesGenerated: isFirstDeployForJob ? s.policiesGenerated + 1 : s.policiesGenerated,
      };
    }
    case "lobstertrap_reloaded":
      return { ...s, synth: { ...s.synth, status: "reloaded" } };
    case "audit_log_entry":
      return { ...s, audits: [ev.entry, ...s.audits].slice(0, 50) };
    case "redteam_probe_started": {
      const v: ProbeView = { phase: "started", probe: ev.probe };
      return { ...s, probes: [v, ...s.probes].slice(0, 50) };
    }
    case "redteam_probe_result": {
      const v: ProbeView = {
        phase: "result",
        probe: ev.result.probe,
        actual_verdict: ev.result.actual_verdict,
        is_gap: ev.result.is_gap,
      };
      return { ...s, probes: [v, ...s.probes].slice(0, 50) };
    }
    case "yaml_chunk":
      return { ...s, synth: { ...s.synth, yaml: s.synth.yaml + ev.chunk } };
    case "yaml_reset":
      return { ...s, synth: { ...s.synth, yaml: "" } };
    case "policy_hash":
      return { ...s, policyHash: ev.sha256 };
    case "redteam_aborted": {
      const v: ProbeView = { phase: "result", attack_category: `aborted: ${ev.reason}` };
      return { ...s, probes: [v, ...s.probes].slice(0, 50) };
    }
    case "pipeline_error":
      return {
        ...s,
        pipelineError: { stage: ev.stage, error: ev.error, test_summary: ev.test_summary },
        synth: s.synth.status === "idle" ? s.synth : { ...s.synth, status: "failed" },
        reader:
          s.reader.status === "idle"
            ? s.reader
            : { ...s.reader, status: s.reader.status === "started" ? "failed" : s.reader.status },
      };
    case "client_error":
      return { ...s, error: ev.error };
    case "sse_status":
      return { ...s, sseStatus: ev.status };
    case "drag":
      return { ...s, isDragging: ev.value };
    case "beat":
      return { ...s, beat: ev.beat };
    case "show_compliance":
      return { ...s, showComplianceReport: true };
    case "reset":
      return { ...INIT_STATE };
    default:
      return s;
  }
}

// Re-export ProbeShape for components that take probe props.
export type { AuditEntry, ProbeShape };
