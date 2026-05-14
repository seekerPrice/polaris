// ProbeRow — one row in the Red Team timeline. Three states: running (violet),
// blocked (emerald), gap (amber, glowing).
import type { ProbeView } from "@/lib/state";

export function ProbeRow({ probe }: { probe: ProbeView }) {
  const isResult = probe.phase === "result";
  const isGap = probe.is_gap === true;
  const isBlocked = isResult && probe.actual_verdict === "DENY" && !isGap;
  const cls = "probe-row " + (
    isGap ? "probe-row--gap" : isBlocked ? "probe-row--blocked" : "probe-row--running"
  );
  return (
    <div className={cls}>
      <span className="probe-row__arrow">{isResult ? (isGap ? "▲" : "✓") : "▶"}</span>
      <span className="probe-row__title">
        {probe.probe?.attack_category || probe.attack_category || "probe"}{" "}
        <small>· {probe.probe?.attack_subtype || ""}</small>
      </span>
      <span className="probe-row__verdict">
        {isGap ? (
          <span className="pill pill--amber">
            <span className="pill__dot" />GAP
          </span>
        ) : isBlocked ? (
          <span className="pill pill--emerald">
            <span className="pill__dot" />BLOCKED
          </span>
        ) : probe.actual_verdict ? (
          <span className="pill">{probe.actual_verdict}</span>
        ) : (
          <span className="pill pill--violet">
            <span className="pill__dot" />running
          </span>
        )}
      </span>
    </div>
  );
}
