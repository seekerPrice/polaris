// Phase-12 T1 — SOC 2 CC8.1 pre-deploy consent gate. Slots between
// Synthesizer-validated and Lobster Trap deploy. 3-second auto-approve
// countdown so demo flow stays smooth; operator click overrides.
"use client";
import { useEffect, useState } from "react";
import { I } from "./icons";

export type ApprovalGateState = {
  jobId: string;
  policySha: string;
  nRequirements: number;
  nRules: number;
  autoApproveAfterS: number;
  startedAt: number; // unix millis when awaiting_approval arrived (countdown anchor)
  decision: null | {
    approved: boolean;
    approver: string;
    decidedAt: number;
    reason?: string;
  };
};

export function ApprovalGate({
  state,
  onApprove,
  onReject,
}: {
  state: ApprovalGateState | null;
  onApprove: (approver: string) => void;
  onReject: (approver: string, reason: string) => void;
}) {
  const [remaining, setRemaining] = useState<number>(() => {
    if (!state || state.decision) return 0;
    const elapsed = (Date.now() - state.startedAt) / 1000;
    return Math.max(0, state.autoApproveAfterS - elapsed);
  });

  useEffect(() => {
    if (!state || state.decision) return;
    const tick = setInterval(() => {
      const elapsed = (Date.now() - state.startedAt) / 1000;
      setRemaining(Math.max(0, state.autoApproveAfterS - elapsed));
    }, 100);
    return () => clearInterval(tick);
  }, [state?.startedAt, state?.autoApproveAfterS, state?.decision]);

  if (!state) return null;

  const decided = state.decision !== null;
  const approved = state.decision?.approved === true;
  const rejected = state.decision?.approved === false;

  return (
    <div className="panel approval-gate">
      <div className="panel__head">
        <div className="panel__title">
          <I.ShieldCheck /> Change approval (SOC 2 CC8.1)
        </div>
        <span className="kicker">policy_sha={state.policySha}</span>
      </div>
      <div className="panel__body">
        <div className="approval__summary">
          <div className="approval__line">
            <strong>{state.nRequirements}</strong> requirements{" "}
            · <strong>{state.nRules}</strong> rules{" "}
            ready to deploy
          </div>
          <div className="approval__sha">
            SHA-256: <code>{state.policySha}</code>
          </div>
        </div>

        {!decided && (
          <>
            <div className="approval__countdown">
              Auto-deploy in <strong>{remaining.toFixed(1)}s</strong>
              <span className="approval__hint"> · click to override</span>
            </div>
            <div className="approval__actions">
              <button
                className="btn btn--primary"
                onClick={() => onApprove("operator@polaris.demo")}
              >
                <I.Check /> Approve &amp; deploy
              </button>
              <button
                className="btn btn--ghost"
                onClick={() =>
                  onReject("operator@polaris.demo", "manual reject")
                }
              >
                <I.X /> Reject
              </button>
            </div>
          </>
        )}

        {approved && state.decision && (
          <div className="approval__decided approval__decided--approved">
            <I.Check /> Deployed by <code>{state.decision.approver}</code>
            {" "}at {new Date(state.decision.decidedAt * 1000).toLocaleTimeString()}
          </div>
        )}

        {rejected && state.decision && (
          <div className="approval__decided approval__decided--rejected">
            <I.X /> Rejected by <code>{state.decision.approver}</code>
            {state.decision.reason ? ` · ${state.decision.reason}` : ""}
          </div>
        )}
      </div>
    </div>
  );
}
