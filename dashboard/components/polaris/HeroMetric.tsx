// HeroMetric — the gradient "11.1s" hero card. Lives in the page hero next to
// the pipeline. Props-only; counts elapsed locally so the page doesn't have to
// own an interval.
"use client";
import { useEffect, useState } from "react";
import type { State } from "@/lib/state";

function useElapsedMs(startedAt: number | null, deployedMs: number | null): number | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (startedAt == null || deployedMs != null) return;
    const id = setInterval(() => setNow(Date.now()), 50);
    return () => clearInterval(id);
  }, [startedAt, deployedMs]);
  if (deployedMs != null) return deployedMs;
  if (startedAt == null) return null;
  return now - startedAt;
}

type Props = { timing: State["timing"] };

export function HeroMetric({ timing }: Props) {
  const elapsed = useElapsedMs(timing.startedAt, timing.deployedMs);
  const seconds = elapsed == null ? null : elapsed / 1000;
  const isLive = timing.startedAt != null && timing.deployedMs == null;
  const isIdle = timing.startedAt == null;

  return (
    <div className="metric-card">
      <div className="metric-card__kicker">
        <span className="label label--hot">Hero metric · end-to-end</span>
        {isLive && (
          <span className="pill pill--cyan">
            <span className="pill__dot" />
            live
          </span>
        )}
        {timing.deployedMs != null && (
          <span className="pill pill--emerald">
            <span className="pill__dot" />
            deployed
          </span>
        )}
        {isIdle && (
          <span className="pill pill--amber">
            <span className="pill__dot" />
            ready
          </span>
        )}
      </div>
      <div className="metric-card__before-after">
        <span className="metric-strike">3 weeks of legal review</span>
        <span className="metric-arrow">→</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", marginTop: 6 }}>
        {isIdle ? (
          <span className="metric-hero metric-hero--idle">drop a PDF to begin</span>
        ) : (
          <>
            <span className="metric-hero">{seconds!.toFixed(1)}</span>
            <span className="metric-unit">sec</span>
          </>
        )}
      </div>
      <div className="metric-card__caption">
        SOC 2 PDF → Reader → Synthesizer → <code>./lobstertrap test</code> → deployed firewall.
        SLA <span className="mono" style={{ color: "var(--text-1)" }}>60s</span> · bench median{" "}
        <span className="mono" style={{ color: "var(--cyan)" }}>11.1s</span>.
      </div>
    </div>
  );
}
