"use client";
// Phase-12 T4 — QUARANTINE Review Queue panel. Closes the 6/6 LT-action
// coverage gap. Shows audit rows where verdict=QUARANTINE that the operator
// hasn't yet decided RELEASE/BLOCK on.
import type { AuditEntry } from "@/lib/api";
import { I } from "./icons";

export function QuarantineQueue({
  audits,
  decisions,
  onRelease,
  onBlock,
}: {
  audits: AuditEntry[];
  decisions: Record<number, "RELEASE" | "BLOCK">;
  onRelease: (entryId: number) => void;
  onBlock: (entryId: number) => void;
}) {
  const pending = audits.filter(
    (a) => a.verdict === "QUARANTINE" && a.entry_id !== undefined && !decisions[a.entry_id],
  );

  return (
    <div className="panel">
      <div className="panel__head">
        <div className="panel__title">
          <I.Shield /> Quarantine queue
          {pending.length > 0 && (
            <span className="panel__title-counter">{pending.length}</span>
          )}
        </div>
        <span className="kicker">human-review · CC6.1</span>
      </div>
      <div className="panel__body">
        {pending.length === 0 ? (
          <div className="empty">
            <I.Check /> No requests awaiting review
          </div>
        ) : (
          pending.map((entry) => (
            <div key={entry.entry_id} className="quarantine-row">
              <div className="quarantine-row__head">
                <span className="pill pill--amber">
                  <span className="pill__dot" />
                  QUARANTINE
                </span>
                <span className="audit-row__rule">{entry.matched_rule ?? "—"}</span>
              </div>
              <div className="quarantine-row__detail">
                <span>intent=<code>{entry.detected?.intent_category ?? "—"}</code></span>
                <span>risk=<code>{(entry.detected?.risk_score ?? 0).toFixed(2)}</code></span>
                {entry.declared?.agent_id && (
                  <span>agent=<code>{entry.declared.agent_id}</code></span>
                )}
              </div>
              <div className="quarantine-row__actions">
                <button
                  className="btn btn--ghost"
                  onClick={() => entry.entry_id !== undefined && onBlock(entry.entry_id)}
                >
                  <I.X /> Block
                </button>
                <button
                  className="btn btn--primary"
                  onClick={() => entry.entry_id !== undefined && onRelease(entry.entry_id)}
                >
                  <I.Check /> Release
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
