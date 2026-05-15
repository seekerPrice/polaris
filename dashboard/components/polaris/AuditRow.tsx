// AuditRow — one row in the live agent-traffic feed. Slide-in animation +
// DENY-rose highlight + mismatch pulse badge.
import type { AuditEntry } from "@/lib/api";
import { I } from "./icons";

function fmtTime(ts?: string): string {
  if (!ts) return "now";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  const elapsed = Math.floor((Date.now() - d.getTime()) / 1000);
  if (elapsed < 0) return d.toLocaleTimeString();
  if (elapsed < 1) return "just now";
  if (elapsed < 60) return `${elapsed}s ago`;
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  return d.toLocaleTimeString();
}

export function AuditRow({ entry }: { entry: AuditEntry }) {
  // Phase-12 T4: QUARANTINE is a third verdict state, styled amber to sit
  // between green ALLOW and red DENY. Audit row tells you SOMETHING happened;
  // the QuarantineQueue panel offers the resolution action.
  const verdict = entry.verdict;
  const cls =
    "audit-row " +
    (verdict === "DENY"
      ? "audit-row--deny"
      : verdict === "QUARANTINE"
      ? "audit-row--quarantine"
      : "audit-row--allow");
  const pillCls =
    "pill " +
    (verdict === "DENY"
      ? "pill--rose"
      : verdict === "QUARANTINE"
      ? "pill--amber"
      : "pill--emerald");
  return (
    <div className={cls}>
      <div className="audit-row__head">
        <span className={pillCls}>
          <span className="pill__dot" />
          {verdict || "—"}
        </span>
        <span className="audit-row__rule">{entry.matched_rule || "—"}</span>
        <span className="ts">{fmtTime(entry.timestamp)}</span>
      </div>
      {entry.detected && (
        <div className="audit-row__line">
          <span><strong>detected</strong></span>
          <span>intent=<code>{entry.detected.intent_category}</code></span>
          <span>risk=<code>{(entry.detected.risk_score ?? 0).toFixed(2)}</code></span>
          {entry.detected.target_domains?.length ? (
            <span>domains=<code>{entry.detected.target_domains.join(",")}</code></span>
          ) : null}
          {entry.detected.target_paths?.length ? (
            <span>paths=<code>{entry.detected.target_paths.join(",")}</code></span>
          ) : null}
        </div>
      )}
      {entry.declared && (
        <div className="audit-row__line">
          <span><strong>declared</strong></span>
          <span>intent=<code>{entry.declared.declared_intent}</code></span>
          <span>
            agent=
            <span
              className={
                "agent-badge " +
                (entry.declared.agent_id?.startsWith("sales")
                  ? "agent-badge--sales"
                  : entry.declared.agent_id?.startsWith("engineering")
                  ? "agent-badge--eng"
                  : "agent-badge--other")
              }
            >
              {entry.declared.agent_id || "—"}
            </span>
          </span>
        </div>
      )}
      {entry.mismatches && entry.mismatches.length > 0 && (
        <div className="audit-row__mismatch">
          <I.Alert /> declared/detected mismatch · {entry.mismatches.join(" · ")}
        </div>
      )}
    </div>
  );
}
