// Kpi — single KPI tile + KpiStrip composing the six shown in the dashboard.
//
// Phase-12 T2 adds "Risk reduction %" (bonus criterion: "measurable risk reduction").
// Phase-12 T3 splits "Attacks blocked" into "Injections blocked" + "Exfiltration caught"
// (bonus criterion: "caught exfiltration").
//
// Server-side reference for both metrics is polaris/api/kpi.py; this mirrors the
// logic in TypeScript for instant updates as audit SSE events stream in.
import type { State } from "@/lib/state";
import type { AuditEntry } from "@/lib/api";

type Accent = "cyan" | "rose" | "amber" | "emerald" | "violet";

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

// Mirrors polaris/api/kpi.py::compute_risk_reduction. Resolved excludes
// HUMAN_REVIEW (in-flight). Mitigated = DENY or QUARANTINE.
const MITIGATING = new Set(["DENY", "QUARANTINE"]);
const RESOLVED = new Set(["DENY", "ALLOW", "QUARANTINE", "LOG"]);

function computeRiskReduction(audits: AuditEntry[]): number {
  const resolved = audits.filter((a) => a.verdict && RESOLVED.has(a.verdict));
  if (resolved.length === 0) return 0;
  const mitigated = resolved.filter((a) => MITIGATING.has(a.verdict!)).length;
  return Math.round((1000 * mitigated) / resolved.length) / 10;
}

const EXFIL_DOMAINS = new Set([
  "pastebin.com", "transfer.sh", "requestbin.com", "requestbin.net",
]);

type BlockBuckets = { exfiltration: number; injection: number; other: number; total: number };

function bucketBlocks(audits: AuditEntry[]): BlockBuckets {
  let exfiltration = 0, injection = 0, other = 0, total = 0;
  for (const a of audits) {
    if (a.verdict !== "DENY") continue;
    total += 1;
    const md = a.detected ?? {};
    const domains = md.target_domains ?? [];
    const hasExfilDomain = domains.some((d) => EXFIL_DOMAINS.has(d));
    // contains_exfiltration is not in AuditEntry.detected typing today — read
    // through `unknown` to stay forward-compatible if LT adds the flag.
    const exfilFlag = (md as unknown as { contains_exfiltration?: boolean }).contains_exfiltration;
    const injectionFlag = (md as unknown as {
      contains_injection_patterns?: boolean;
      contains_role_impersonation?: boolean;
    });
    if (exfilFlag || hasExfilDomain) {
      exfiltration += 1;
    } else if (injectionFlag.contains_injection_patterns || injectionFlag.contains_role_impersonation) {
      injection += 1;
    } else {
      other += 1;
    }
  }
  return { exfiltration, injection, other, total };
}

export function KpiStrip({ state }: { state: State }) {
  const buckets = bucketBlocks(state.audits);
  const risk = computeRiskReduction(state.audits);
  const mismatches = state.audits.reduce((n, a) => n + (a.mismatches?.length ?? 0), 0);
  const probesBlocked = state.probes.filter(
    (p) => p.phase === "result" && p.actual_verdict === "DENY",
  ).length;

  // Injections KPI counts probe blocks too (red-team injection probes that fired
  // through LT and got denied). Exfiltration stays audit-only since probes don't
  // currently model paste-site domains.
  const injectionsBlocked = buckets.injection + probesBlocked;
  const totalBlocked = buckets.total + probesBlocked;

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
        label="Risk reduction"
        value={`${risk}%`}
        sub={`${totalBlocked} of ${totalBlocked + state.audits.filter((a) => a.verdict === "ALLOW").length} resolved`}
        accent="emerald"
        fill={risk}
      />
      <Kpi
        label="Injections blocked"
        value={injectionsBlocked}
        sub={probesBlocked ? `${probesBlocked} probes` : "audit"}
        accent="rose"
        fill={injectionsBlocked ? Math.min(100, injectionsBlocked * 25) : 0}
      />
      <Kpi
        label="Exfiltration caught"
        value={buckets.exfiltration}
        sub="paste-site / contains_exfiltration"
        accent="amber"
        fill={buckets.exfiltration ? Math.min(100, buckets.exfiltration * 33) : 0}
      />
      <Kpi
        label="Mismatches caught"
        value={mismatches}
        sub="declared vs detected"
        accent="violet"
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
