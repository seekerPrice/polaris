// Topbar — brand + connection status + Reset / Run-demo buttons. Props-only;
// no state ownership.
import { PolarisMark } from "./Brand";
import { I } from "./icons";

type Props = {
  sseStatus: "connected" | "reconnecting";
  jobId: string | null;
  replaying: boolean;
  onReset: () => void;
  onRunDemo: () => void;
};

export function Topbar({ sseStatus, jobId, replaying, onReset, onRunDemo }: Props) {
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <PolarisMark />
        <div className="brand-text">
          <span className="brand-text__name">Polaris</span>
          <span className="brand-text__sub">AI Agent Firewall · Veea Trust Track</span>
        </div>
      </div>
      <div className="topbar__rail">
        {sseStatus === "reconnecting" ? (
          <span className="status-pill status-pill--warn">
            <span className="status-pill__dot" />
            Reconnecting
          </span>
        ) : (
          <span className="status-pill">
            <span className="status-pill__dot" />
            SSE live · :8000
          </span>
        )}
        <button className="btn btn--ghost" onClick={onReset} disabled={!jobId && !replaying}>
          <I.Restart /> Reset
        </button>
        <button
          className={"btn " + (jobId ? "btn--primary" : "btn--cta")}
          onClick={onRunDemo}
          disabled={replaying}
        >
          <I.Play /> {replaying ? "Running…" : "Run demo"}
        </button>
      </div>
    </header>
  );
}
