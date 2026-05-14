// Kpi — single KPI tile + KpiStrip composing the four shown in the dashboard.
import type { State } from "@/lib/state";

type Accent = "cyan" | "rose" | "amber" | "emerald";

type KpiProps = {
  label: string;
  value: number | string;
  sub?: string;
  accent?: Accent;
  fill?: number; // 0..100
};

export function Kpi({ label, value, sub, accent, fill }: KpiProps) {
  const cls = "kpi" + (accent ? ` kpi--${accent}` : "");
  return (
    <div className={cls}>
      <div className="kpi__label">{label}</div>
      <div className="kpi__val">
        {value}
        {sub && <small>{sub}</small>}
      </div>
      <div className="kpi__bar" style={{ width: `${fill ?? 0}%` }} />
    </div>
  );
}

export function KpiStrip({ state }: { state: State }) {
  const blocked = state.audits.filter((a) => a.verdict === "DENY").length;
  const mismatches = state.audits.reduce((n, a) => n + (a.mismatches?.length ?? 0), 0);
  const probesBlocked = state.probes.filter(
    (p) => p.phase === "result" && p.actual_verdict === "DENY",
  ).length;
  return (
    <section className="kpis">
      <Kpi
        label="Policies live"
        value={state.policiesGenerated}
        sub={state.policyHash ? "validated" : "—"}
        accent="cyan"
        fill={state.policiesGenerated ? 100 : 0}
      />
      <Kpi
        label="Attacks blocked"
        value={blocked}
        sub={`${probesBlocked} probes`}
        accent="rose"
        fill={blocked ? Math.min(100, blocked * 33) : 0}
      />
      <Kpi
        label="Mismatches caught"
        value={mismatches}
        sub="declared vs detected"
        accent="amber"
        fill={mismatches ? Math.min(100, mismatches * 25) : 0}
      />
      <Kpi
        label="Controls mapped"
        value={state.reader.n || "—"}
        sub="SOC 2 / OWASP / EU AI Act"
        accent="emerald"
        fill={state.reader.n ? Math.min(100, state.reader.n * 25) : 0}
      />
    </section>
  );
}
