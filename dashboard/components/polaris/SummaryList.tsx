// SummaryList — Reader / Synth / E2E / Policy-hash rows shown below the
// dropzone in the left column.
import type { State } from "@/lib/state";

type Props = {
  reader: State["reader"];
  synth: State["synth"];
  timing: State["timing"];
  policyHash: string | null;
};

export function SummaryList({ reader, synth, timing, policyHash }: Props) {
  const synthStreaming = synth.status === "started" || synth.status === "regenerating";
  return (
    <div className="summary-list">
      <div className="summary-row">
        <span className="summary-row__label">Reader</span>
        <span className="summary-row__val row" style={{ gap: 8 }}>
          <span
            className={
              "pill " +
              (reader.status === "completed"
                ? "pill--emerald"
                : reader.status === "idle"
                ? ""
                : "pill--cyan")
            }
          >
            {reader.status !== "idle" && <span className="pill__dot" />}
            {reader.status}
          </span>
          <span className="mono" style={{ color: "var(--text-1)", fontSize: 11 }}>
            req: {reader.n}
          </span>
        </span>
      </div>
      <div className="summary-row">
        <span className="summary-row__label">Synthesizer</span>
        <span className="summary-row__val row" style={{ gap: 8 }}>
          <span className={"pill " + (synth.passed ? "pill--emerald" : synthStreaming ? "pill--cyan" : "")}>
            {synth.status !== "idle" && <span className="pill__dot" />}
            {synth.status}
          </span>
          {synth.passed === true && (
            <span className="pill pill--emerald" style={{ fontSize: 9.5 }}>
              ✓ lt test
            </span>
          )}
        </span>
      </div>
      {timing.deployedMs != null && (
        <div className="summary-row">
          <span className="summary-row__label">End-to-end</span>
          <span className="summary-row__val mono" style={{ color: "var(--cyan)" }}>
            {(timing.deployedMs / 1000).toFixed(1)}s{" "}
            <small style={{ color: "var(--text-2)" }}>· SLA 60s</small>
          </span>
        </div>
      )}
      {policyHash && (
        <div className="summary-row">
          <span className="summary-row__label">Policy</span>
          <span
            className="summary-row__val mono"
            style={{ color: "var(--text-1)", fontSize: 10.5 }}
          >
            sha256·{policyHash}
          </span>
        </div>
      )}
    </div>
  );
}
