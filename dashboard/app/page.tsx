"use client";
// dashboard/app/page.tsx — orchestration layer. Thin composition of:
//   - lib/state.ts   (reducer + state)
//   - lib/api.ts     (transport: uploadPolicy / startRedTeam)
//   - lib/replay.ts  (12-beat demo replay engine)
//   - components/polaris/* (presentation primitives)
//
// No JSX-internal state machines, no rendering logic that belongs in a
// component. The four useEffect blocks handle: SSE subscription, chime audio,
// YAML streaming animation, and the Cmd+Shift+P stage-day fallback.
import { useCallback, useEffect, useReducer, useRef } from "react";
import { API_BASE, uploadPolicy, startRedTeam } from "@/lib/api";
import { reducer, INIT_STATE } from "@/lib/state";
import { startReplay, type ReplayHandle } from "@/lib/replay";
import { Topbar } from "@/components/polaris/Topbar";
import { ErrorBanner } from "@/components/polaris/ErrorBanner";
import { HeroMetric } from "@/components/polaris/HeroMetric";
import { Pipeline } from "@/components/polaris/Pipeline";
import { KpiStrip } from "@/components/polaris/Kpi";
import { Dropzone } from "@/components/polaris/Dropzone";
import { SummaryList } from "@/components/polaris/SummaryList";
import { ComplianceReport } from "@/components/polaris/ComplianceReport";
import { YamlEditor } from "@/components/polaris/YamlEditor";
import { AuditRow } from "@/components/polaris/AuditRow";
import { ProbeRow } from "@/components/polaris/ProbeRow";
import { BeatOverlay } from "@/components/polaris/BeatOverlay";
import { DenyFlash } from "@/components/polaris/DenyFlash";
import { I } from "@/components/polaris/icons";

export default function Page() {
  const [state, dispatch] = useReducer(reducer, INIT_STATE);
  const replayRef = useRef<ReplayHandle | null>(null);

  // ----- SSE subscription -----
  // M23 fix (deep-check 2026-05-13): onerror dispatches sse_status=reconnecting
  // so the Topbar shows the amber pill instead of going silently idle.
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
    es.onerror = () => dispatch({ type: "sse_status", status: "reconnecting" });
    return () => es.close();
  }, []);

  // ----- chime audio on Synth completion (Phase-11 C2) -----
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
      void audio.play().catch(() => undefined);
    } catch {
      /* SSR safety */
    }
  }, [state.synth.status]);
  useEffect(() => {
    if (state.jobId === null) chimePlayed.current = false;
  }, [state.jobId]);

  // ----- Cmd+Shift+P stage-day replay fallback (loads precomputed_run.json) -----
  // Production replay path is the topbar "Run demo" button (uses lib/replay.ts
  // with hardcoded fixtures). This shortcut replays a REAL captured run for
  // stage-day fidelity when Gemini/LT are unreachable.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isReplay =
        (e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === "P" || e.key === "p");
      if (!isReplay) return;
      e.preventDefault();
      void (async () => {
        try {
          const r = await fetch("/precomputed_run.json");
          if (!r.ok) {
            alert("precomputed_run.json missing — run scripts/capture_replay.sh first");
            return;
          }
          const data = (await r.json()) as { job_id: string; events: unknown[] };
          dispatch({ type: "set_job", jobId: data.job_id });
          const SPACING_MS = 350;
          for (const ev of data.events) {
            await new Promise((res) => setTimeout(res, SPACING_MS));
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            dispatch(ev as any);
          }
        } catch (err) {
          alert(`Replay failed: ${err instanceof Error ? err.message : String(err)}`);
        }
      })();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // ----- real handlers (call into the API layer) -----
  async function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    dispatch({ type: "drag", value: false });
    const f = e.dataTransfer.files[0];
    if (!f) return;
    try {
      dispatch({ type: "client_error", error: null });
      const { job_id } = await uploadPolicy(f);
      dispatch({ type: "set_job", jobId: job_id });
    } catch (err) {
      dispatch({
        type: "client_error",
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  function onDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    if (!state.isDragging) dispatch({ type: "drag", value: true });
  }

  function onDragLeave() {
    dispatch({ type: "drag", value: false });
  }

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    // L34 fix (deep-check 2026-05-13): reset input value so picking the same
    // file twice fires a second onChange.
    e.target.value = "";
    if (!f) return;
    try {
      dispatch({ type: "client_error", error: null });
      const { job_id } = await uploadPolicy(f);
      dispatch({ type: "set_job", jobId: job_id });
    } catch (err) {
      dispatch({
        type: "client_error",
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  async function onLoadDemo() {
    try {
      dispatch({ type: "client_error", error: null });
      const r = await fetch("/sample-soc2.pdf");
      if (!r.ok) {
        dispatch({
          type: "client_error",
          error: "sample-soc2.pdf missing in dashboard/public/. Run scripts/copy_demo_pdf.sh.",
        });
        return;
      }
      const blob = await r.blob();
      const file = new File([blob], "soc2_excerpt.pdf", { type: "application/pdf" });
      const { job_id } = await uploadPolicy(file);
      dispatch({ type: "set_job", jobId: job_id });
    } catch (err) {
      dispatch({
        type: "client_error",
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  async function onStartRedTeam() {
    if (!state.jobId) return;
    try {
      dispatch({ type: "client_error", error: null });
      await startRedTeam(state.jobId);
    } catch (err) {
      dispatch({
        type: "client_error",
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  // ----- demo replay (hardcoded fixtures) -----
  const replaying = replayRef.current?.running() === true;
  const onRunDemo = useCallback(() => {
    if (replayRef.current?.running()) return;
    replayRef.current = startReplay(dispatch);
  }, []);
  const onReset = useCallback(() => {
    replayRef.current?.cancel();
    replayRef.current = null;
    dispatch({ type: "reset" });
  }, []);

  // ----- derived render values -----
  const synthStreaming =
    state.synth.status === "started" || state.synth.status === "regenerating";
  const synthStatusLabel =
    state.synth.status === "completed" ? "validated · 11/11 pass" :
    state.synth.status === "deployed" ? "deployed · gen live" :
    state.synth.status === "reloaded" ? "patched · re-deployed" :
    state.synth.status === "regenerating" ? "regenerating" :
    null;

  return (
    <div className="app">
      <DenyFlash audits={state.audits} />
      <BeatOverlay beat={state.beat} />

      <Topbar
        sseStatus={state.sseStatus}
        jobId={state.jobId}
        replaying={replaying}
        onReset={onReset}
        onRunDemo={onRunDemo}
      />

      <ErrorBanner error={state.error} pipelineError={state.pipelineError} />

      {/* hero */}
      <section className="hero">
        <HeroMetric timing={state.timing} />
        <Pipeline
          reader={state.reader}
          synth={state.synth}
          probes={state.probes}
          policyHash={state.policyHash}
        />
      </section>

      <KpiStrip state={state} />

      {/* main grid */}
      <section className="grid">
        {/* col 1 — upload + summary + compliance */}
        <div className="col">
          <div className="panel">
            <div className="panel__head">
              <div className="panel__title"><I.Upload /> Policy upload</div>
              <span className="kicker">drop · click · ⌘⇧P</span>
            </div>
            <div className="panel__body">
              <Dropzone
                isDragging={state.isDragging}
                jobId={state.jobId}
                replaying={replaying}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onPickFile={onPickFile}
                onLoadDemo={onLoadDemo}
              />
              <SummaryList
                reader={state.reader}
                synth={state.synth}
                timing={state.timing}
                policyHash={state.policyHash}
              />
              {state.jobId && (
                <button className="btn btn--primary" onClick={onStartRedTeam}>
                  <I.Crosshair /> Start Red Team
                </button>
              )}
            </div>
          </div>

          <ComplianceReport show={state.showComplianceReport} />
        </div>

        {/* col 2 — YAML stream */}
        <div className="col">
          <div className="panel" style={{ flex: 1, minHeight: 540 }}>
            <div className="panel__head">
              <div className="panel__title"><I.Cpu /> Synthesizer output</div>
              <span className="kicker">gemini-3.1-flash-lite · thinking_level=low</span>
            </div>
            <YamlEditor
              yaml={state.synth.yaml}
              streaming={synthStreaming}
              status={synthStatusLabel}
            />
          </div>
        </div>

        {/* col 3 — audit + red team */}
        <div className="col">
          <div className="panel" style={{ flex: 1.1, minHeight: 280 }}>
            <div className="panel__head">
              <div className="panel__title">
                <I.Activity /> Live agent traffic
                <span className="panel__title-counter">{state.audits.length}</span>
              </div>
              <span className="kicker">inline · :8080</span>
            </div>
            <div className="panel__body" style={{ paddingTop: 10 }}>
              <div className="panel__scroll">
                {state.audits.length === 0 ? (
                  <div className="empty">
                    <I.Inbox />
                    Waiting for the first request through Lobster Trap…
                  </div>
                ) : (
                  state.audits.map((a, i) => (
                    <AuditRow key={`${a.timestamp ?? ""}::${i}`} entry={a} />
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="panel" style={{ flex: 1, minHeight: 240 }}>
            <div className="panel__head">
              <div className="panel__title">
                <I.Crosshair /> Red Team timeline
                <span className="panel__title-counter">{state.probes.length}</span>
              </div>
              <span className="kicker">closed loop</span>
            </div>
            <div className="panel__body" style={{ paddingTop: 10 }}>
              <div className="panel__scroll">
                {state.probes.length === 0 ? (
                  <div className="empty">
                    <I.Crosshair />
                    Run the demo to see the closed-loop:
                    <br />probe → gap → patch → re-block.
                  </div>
                ) : (
                  state.probes.map((p, i) => (
                    <ProbeRow key={`${p.phase}::${p.attack_category ?? ""}::${i}`} probe={p} />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
