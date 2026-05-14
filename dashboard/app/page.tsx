"use client";

import { useEffect, useReducer, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, Activity, Bug, FileCheck } from "lucide-react";
import { API_BASE, uploadPolicy, startRedTeam, type PolarisEvent, type AuditEntry } from "@/lib/api";

// Phase-11 T1.B5 — human-friendly timestamp helper.
function fmtTime(ts?: string): string {
  if (!ts) return "—";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  const elapsed = Math.floor((Date.now() - d.getTime()) / 1000);
  // Future or clock-skewed timestamps: fall back to wall-clock string.
  if (elapsed < 0) return d.toLocaleTimeString();
  if (elapsed < 1) return "just now";
  if (elapsed < 60) return `${elapsed}s ago`;
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  return d.toLocaleTimeString();
}

// Phase-11 T1.B2 — KPI row component above the 4-panel grid.
function KPI({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded p-3">
      <div className="text-[10px] uppercase tracking-wider text-slate-400">{label}</div>
      <div className="text-lg font-semibold text-slate-100 mt-1">{value}</div>
    </div>
  );
}

type ProbeView = {
  phase: "started" | "result";
  probe?: { attack_category?: string; attack_subtype?: string };
  attack_category?: string;
  actual_verdict?: string;
  is_gap?: boolean;
};

type State = {
  jobId: string | null;
  reader: { status: string; n: number };
  synth: { status: string; yaml: string; passed: boolean | null };
  audits: AuditEntry[];
  probes: ProbeView[];
  timing: { startedAt: number | null; deployedMs: number | null };
  policyHash: string | null;
  policiesGenerated: number;
  // H13/H2 fix (deep-check 2026-05-13): surface error states instead of leaving the
  // UI sat at "idle" / spinning forever. `error` is for client-side fetch failures;
  // `pipelineError` is the SSE-delivered server-side stage failure.
  error: string | null;
  pipelineError: { stage: string; error: string; test_summary?: string } | null;
  // M23 fix (deep-check 2026-05-13): SSE reconnect status so a server restart between
  // demo takes is visible to the operator instead of silently making the dashboard idle.
  sseStatus: "connected" | "reconnecting";
};

type Action =
  | { type: "set_job"; jobId: string }
  | { type: "yaml_chunk"; chunk: string }
  | { type: "yaml_reset" }
  | { type: "client_error"; error: string | null }
  | { type: "sse_status"; status: "connected" | "reconnecting" }
  | PolarisEvent;

const init: State = {
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
};

function reducer(s: State, ev: Action): State {
  switch (ev.type) {
    case "set_job":
      // L42 fix (deep-check 2026-05-13): preserve the running counter, but DO NOT bump
      // on upload — bump only on `lobstertrap_deployed` (below) so the KPI reflects
      // policies that actually went live, not in-flight uploads that may fail.
      return {
        ...init,
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
      // L42 fix: bump policy counter here, not on upload — only counts policies
      // that successfully made it to a live LT generation.
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
      // H2/C1/C2 fix: server stage failure. Show as red banner; UI stops spinning.
      return {
        ...s,
        pipelineError: { stage: ev.stage, error: ev.error, test_summary: ev.test_summary },
        synth: s.synth.status === "idle" ? s.synth : { ...s.synth, status: "failed" },
        reader: s.reader.status === "idle" ? s.reader : { ...s.reader, status: s.reader.status === "started" ? "failed" : s.reader.status },
      };
    case "client_error":
      return { ...s, error: ev.error };
    case "sse_status":
      return { ...s, sseStatus: ev.status };
    default:
      return s;
  }
}

export default function Page() {
  const [state, dispatch] = useReducer(reducer, init);
  const yamlAnimating = useRef(false);
  // L36 fix (deep-check 2026-05-13): show a visible "drop zone armed" state so the
  // demo audience can see the drag was registered. Cleared on drop/leave/end.
  const [isDragging, setIsDragging] = useReducer(
    (_: boolean, v: boolean) => v,
    false,
  );

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/events`);
    es.onopen = () => dispatch({ type: "sse_status", status: "connected" });
    es.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data);
        dispatch(ev);
      } catch {
        /* ignore malformed */
      }
    };
    // M23 fix: EventSource auto-reconnects but never tells the user. Surface the
    // "reconnecting" state so a server restart between demo takes is visible.
    es.onerror = () => dispatch({ type: "sse_status", status: "reconnecting" });
    return () => es.close();
  }, []);

  // Stage-day fallback: Cmd+Shift+P (P = Polaris) replays a pre-captured run from
  // dashboard/public/precomputed_run.json without needing Gemini or Lobster Trap live.
  // Cmd+Shift+R is intentionally NOT used because Chrome reserves it for hard-reload.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isReplay =
        (e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === "P" || e.key === "p");
      if (!isReplay) return;
      e.preventDefault();
      (async () => {
        try {
          const r = await fetch("/precomputed_run.json");
          if (!r.ok) {
            alert("precomputed_run.json missing — run scripts/capture_replay.sh first");
            return;
          }
          const data = (await r.json()) as { job_id: string; events: unknown[] };
          dispatch({ type: "set_job", jobId: data.job_id });
          // Replay events with realistic spacing — match recorded ~11s pacing.
          const SPACING_MS = 350;
          for (const ev of data.events) {
            await new Promise((res) => setTimeout(res, SPACING_MS));
            // Phase-11 deep-review C3 (dashboard): old replay fixtures captured RAW
            // LT field names (`action`, `rule_name`, `metadata`, `declared_headers`).
            // Production path now aliases these in `_pump_audit_log`; mirror that
            // aliasing client-side so old fixtures keep rendering correctly without
            // forcing a re-capture for every backend change.
            const e = ev as Record<string, unknown> & { type?: string; entry?: Record<string, unknown> };
            if (e?.type === "audit_log_entry" && e.entry && typeof e.entry === "object") {
              const entry = e.entry as Record<string, unknown>;
              if ("action" in entry && !("verdict" in entry)) entry.verdict = entry.action;
              if ("rule_name" in entry && !("matched_rule" in entry)) entry.matched_rule = entry.rule_name;
              if ("metadata" in entry && !("detected" in entry)) entry.detected = entry.metadata;
              if ("declared_headers" in entry && !("declared" in entry)) entry.declared = entry.declared_headers;
            }
            dispatch(ev as Action);
          }
        } catch (err) {
          alert(`Replay failed: ${err}`);
        }
      })();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Phase-10 T2.3 — play soft chime when Synthesizer completes (DEMO_SCRIPT beat 4).
  // chime.mp3 is CC0; drop one into dashboard/public/chime.mp3. If missing, fails silently.
  // Phase-11 deep-review C2 (dashboard): also chime on `started` → `completed` transition
  // for regen, so the patch beat (demo beat 9) has an audio cue too. Guard resets when
  // synth re-enters `started` (regenerating) so chime can replay on the second `completed`.
  const chimePlayed = useRef(false);
  useEffect(() => {
    const status = state.synth.status;
    if (status === "started" || status === "regenerating") {
      chimePlayed.current = false;
      return;
    }
    if (status !== "completed" || chimePlayed.current) return;
    chimePlayed.current = true;
    try {
      const audio = new Audio("/chime.mp3");
      audio.volume = 0.4;
      void audio.play().catch(() => { /* autoplay blocked or file missing — silent */ });
    } catch { /* no Audio constructor (SSR?) — silent */ }
  }, [state.synth.status]);

  // Reset chime guard on new job
  useEffect(() => {
    if (state.jobId === null) chimePlayed.current = false;
  }, [state.jobId]);

  // Demo beat 3 + 9: stream YAML line-by-line after Synthesizer reports completed,
  // AND re-stream on regen ("reloaded"). Phase-11 deep-review M9: omit
  // `state.synth.yaml` from deps — it's a write target of this effect, including
  // it caused the cleanup to fire on every chunk dispatch and (depending on React
  // scheduling) could halt the streamer mid-flow.
  useEffect(() => {
    const status = state.synth.status;
    const isStreamableStatus =
      status === "completed" || status === "deployed" || status === "reloaded";
    if (!isStreamableStatus) return;
    if (!state.jobId || yamlAnimating.current) return;
    yamlAnimating.current = true;
    let cancelled = false;
    (async () => {
      const j = await fetch(`${API_BASE}/api/policies/${state.jobId}`).then((r) => r.json());
      const yaml: string = j["policy.yaml"] ?? "";
      for (const line of yaml.split("\n")) {
        if (cancelled) break;
        await new Promise((r) => setTimeout(r, 60));
        dispatch({ type: "yaml_chunk", chunk: line + "\n" });
      }
      yamlAnimating.current = false;
    })();
    return () => {
      cancelled = true;
    };
  }, [state.synth.status, state.jobId]);

  async function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (!f) return;
    // H13 fix (deep-check 2026-05-13): wrap in try/catch so an API outage / 4xx
    // surfaces as a red banner instead of leaving the dashboard sat at "Reader: idle"
    // forever, indistinguishable from in-progress.
    try {
      dispatch({ type: "client_error", error: null });
      const { job_id } = await uploadPolicy(f);
      dispatch({ type: "set_job", jobId: job_id });
    } catch (err) {
      dispatch({ type: "client_error", error: err instanceof Error ? err.message : String(err) });
    }
  }

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    // L34 fix (deep-check 2026-05-13): reset the input value so picking the same
    // file twice fires a second onChange.
    e.target.value = "";
    if (!f) return;
    try {
      dispatch({ type: "client_error", error: null });
      const { job_id } = await uploadPolicy(f);
      dispatch({ type: "set_job", jobId: job_id });
    } catch (err) {
      dispatch({ type: "client_error", error: err instanceof Error ? err.message : String(err) });
    }
  }

  async function onStartRedTeam() {
    if (!state.jobId) return;
    try {
      dispatch({ type: "client_error", error: null });
      await startRedTeam(state.jobId);
    } catch (err) {
      dispatch({ type: "client_error", error: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-slate-100 p-6">
      <header className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Polaris — From SOC 2 PDF to live AI guardrail in 60 seconds
            </h1>
            <p className="text-sm text-slate-400">
              Veea Trust Track · Powered by Google Gemini & Lobster Trap
            </p>
          </div>
          {state.sseStatus === "reconnecting" && (
            <Badge className="bg-amber-600">Reconnecting…</Badge>
          )}
        </div>
        {(state.error || state.pipelineError) && (
          <div className="mt-3 rounded border border-red-700/60 bg-red-950/40 text-red-200 text-sm p-3">
            {state.error && (
              <div>
                <span className="font-semibold">Client error:</span> {state.error}
              </div>
            )}
            {state.pipelineError && (
              <div>
                <span className="font-semibold">Pipeline failed at {state.pipelineError.stage}:</span>{" "}
                {state.pipelineError.error}
                {state.pipelineError.test_summary && (
                  <div className="text-xs text-red-300/80 mt-1">
                    LT test: {state.pipelineError.test_summary.slice(0, 200)}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
        <KPI label="Policies generated" value={state.policiesGenerated} />
        <KPI label="Attacks blocked" value={state.audits.filter((a) => a.verdict === "DENY").length} />
        <KPI
          label="Mismatches caught"
          value={state.audits.reduce((n, a) => n + (a.mismatches?.length ?? 0), 0)}
        />
        <KPI label="Controls mapped" value={state.reader.n} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card
          className={`p-4 bg-slate-900/70 border-slate-800 transition-colors ${
            isDragging ? "ring-2 ring-emerald-400 bg-slate-900" : ""
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            if (!isDragging) setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
        >
          <div className="flex items-center gap-2 mb-3">
            <Upload className="h-4 w-4 text-emerald-400" />
            <h2 className="font-medium">Policy upload</h2>
          </div>
          <label className="block border-2 border-dashed border-slate-700 rounded p-8 text-center text-slate-400 cursor-pointer hover:border-slate-500">
            Drag a SOC 2 / OWASP / EU AI Act PDF or .md here, or click to choose
            <input
              type="file"
              data-testid="upload-input"
              className="hidden"
              onChange={onPickFile}
              accept=".pdf,.md,.txt"
            />
          </label>
          <Button
            variant="outline"
            size="sm"
            className="mt-2 w-full"
            data-testid="load-demo-soc2"
            onClick={async () => {
              try {
                const r = await fetch("/sample-soc2.pdf");
                if (!r.ok) {
                  alert("sample-soc2.pdf missing in dashboard/public/. Run: ./scripts/copy_demo_pdf.sh");
                  return;
                }
                const blob = await r.blob();
                const file = new File([blob], "soc2_excerpt.pdf", { type: "application/pdf" });
                const { job_id } = await uploadPolicy(file);
                dispatch({ type: "set_job", jobId: job_id });
              } catch (e) {
                alert(`Demo load failed: ${e}`);
              }
            }}
          >
            🚀 Load demo SOC 2 PDF
          </Button>
          <div className="mt-3 text-sm space-y-1">
            <div>
              Reader: <Badge variant="secondary">{state.reader.status}</Badge>{" "}
              requirements: {state.reader.n}
            </div>
            <div>
              Synth: <Badge variant="secondary">{state.synth.status}</Badge>{" "}
              {state.synth.passed === true && (
                <Badge className="bg-emerald-600">PASSED ./lobstertrap test</Badge>
              )}
            </div>
            {state.timing.deployedMs !== null && (
              <div>
                End-to-end:{" "}
                <Badge className="bg-sky-600">
                  ~{(state.timing.deployedMs / 1000).toFixed(1)}s
                </Badge>{" "}
                <span className="text-[10px] text-slate-400">(SLA: 60s)</span>
              </div>
            )}
            {state.policyHash && (
              <div>
                Policy: <Badge className="bg-slate-700 font-mono text-[10px]">{state.policyHash}</Badge>
                <span className="text-[10px] text-slate-400 ml-1">(sha256, audit-defensible)</span>
              </div>
            )}
            <div className="text-[10px] text-slate-500 mt-1">
              Why this model? See <code className="text-slate-400">docs/MODEL_BAKEOFF.md</code> (48-run bake-off).
            </div>
          </div>
          {state.jobId && (
            <Button className="mt-3" onClick={onStartRedTeam}>
              Start Red Team
            </Button>
          )}
          {state.synth.yaml && (
            <pre className="mt-3 text-[10px] bg-slate-950 text-emerald-300 p-3 rounded max-h-64 overflow-auto whitespace-pre-wrap">
              {state.synth.yaml}
            </pre>
          )}
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="h-4 w-4 text-emerald-400" />
            <h2 className="font-medium">Live agent traffic</h2>
          </div>
          <div className="space-y-2 max-h-80 overflow-auto">
            {state.audits.length === 0 && (
              <div className="text-xs text-slate-500">Waiting for the first request through Lobster Trap…</div>
            )}
            {state.audits.map((a, i) => (
              // L41 fix (deep-check 2026-05-13): key on timestamp+i, not just index.
              // New entries prepend to the array; using only `i` makes the animate-pulse
              // mismatch badge rebind to the wrong row across renders.
              <div
                key={`${a.timestamp ?? ""}::${i}`}
                className={`text-xs p-2 rounded ${
                  a.verdict === "DENY" ? "bg-red-950 text-red-200" : "bg-slate-800"
                }`}
              >
                <div>
                  <strong>{a.verdict}</strong> {a.matched_rule ?? "—"} · {fmtTime(a.timestamp)}
                </div>
                {a.detected && (
                  // M24 fix (deep-check 2026-05-13): text-[10px] + text-slate-500/opacity-70
                  // on bg-slate-900 fails readable-text contrast on the recording. Bump to
                  // text-xs (12px) and lift the foreground from slate-500/opacity-70 to
                  // slate-300 so the demo metadata stays legible on a 1920×1080 capture.
                  <div className="text-xs text-slate-300 mt-1">
                    detected: intent={a.detected.intent_category} risk=
                    {a.detected.risk_score?.toFixed?.(2)}
                    {a.detected.target_domains?.length
                      ? ` domains=${a.detected.target_domains.join(",")}`
                      : ""}
                    {a.detected.target_paths?.length
                      ? ` paths=${a.detected.target_paths.join(",")}`
                      : ""}
                  </div>
                )}
                {a.declared && (
                  <div className="text-xs text-slate-300">
                    declared: {a.declared.declared_intent} (agent={a.declared.agent_id})
                  </div>
                )}
                {a.mismatches && a.mismatches.length > 0 && (
                  <div className="mt-1">
                    <Badge className="bg-red-700 animate-pulse text-xs">
                      ⚠ Declared/Detected mismatch
                    </Badge>
                    <div className="text-xs text-red-100 mt-1">{a.mismatches.join(" · ")}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Bug className="h-4 w-4 text-rose-400" />
            <h2 className="font-medium">Red Team timeline</h2>
          </div>
          <div className="space-y-2 max-h-80 overflow-auto">
            {state.probes.length === 0 && (
              <div className="text-xs text-slate-500">Click &quot;Start Red Team&quot; to begin probing.</div>
            )}
            {state.probes.map((p, i) => (
              <div
                // L41 fix: stable composite key — phase + index in prepended list.
                key={`${p.phase}::${p.attack_category ?? ""}::${i}`}
                className={`text-xs p-2 rounded ${
                  p.is_gap ? "bg-yellow-950 text-yellow-200" : "bg-slate-800"
                }`}
              >
                {p.phase === "started" ? "▶ " : "✓ "}
                {p.probe?.attack_category ?? p.attack_category}{" "}
                {p.probe?.attack_subtype && (
                  <span className="opacity-70">· {p.probe.attack_subtype}</span>
                )}{" "}
                {p.is_gap && <span className="font-bold">GAP</span>}
                {p.actual_verdict && (
                  <span className="opacity-70"> → {p.actual_verdict}</span>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <FileCheck className="h-4 w-4 text-emerald-400" />
            <h2 className="font-medium">Compliance report</h2>
          </div>
          <p className="text-sm text-slate-400 mb-3">
            Mapped to SOC 2 / OWASP LLM Top 10 / EU AI Act controls.
          </p>
          {state.jobId && (
            <a
              href={`${API_BASE}/api/compliance-report/${state.jobId}`}
              target="_blank"
              rel="noreferrer"
            >
              <Button>Download Report PDF</Button>
            </a>
          )}
        </Card>
      </div>
    </main>
  );
}
