// ComplianceReport — collapsed empty state OR populated 4-control list.
// The "show" prop is the replay engine's `state.showComplianceReport` flag.
// Real backend traffic eventually replaces this with a fetched report PDF.
import { I } from "./icons";

const CONTROLS = [
  { code: "SOC 2 CC7.2", desc: "System operations — anomaly detection" },
  { code: "SOC 2 CC6.1", desc: "Logical access — restrict data exfiltration" },
  { code: "OWASP LLM01", desc: "Prompt injection — direct & indirect" },
  { code: "OWASP LLM06", desc: "Sensitive information disclosure" },
];

export function ComplianceReport({ show, onDownload }: { show: boolean; onDownload?: () => void }) {
  return (
    <div className="panel">
      <div className="panel__head">
        <div className="panel__title"><I.FileCheck /> Compliance report</div>
        {show && (
          <span className="pill pill--emerald">
            <span className="pill__dot" />ready
          </span>
        )}
      </div>
      <div className="panel__body compliance">
        {show ? (
          <>
            {CONTROLS.map((c) => (
              <div className="control-row" key={c.code}>
                <span className="control-row__code">{c.code}</span>
                <span className="control-row__desc">{c.desc}</span>
                <span className="pill pill--emerald" style={{ fontSize: 9.5 }}>mapped</span>
              </div>
            ))}
            <button
              className="btn btn--primary"
              style={{ marginTop: 6, justifyContent: "center" }}
              onClick={onDownload}
            >
              <I.FileCheck /> Download report.pdf
            </button>
          </>
        ) : (
          <div className="empty">
            <I.FileCheck />
            Compliance report renders here once a policy is deployed.
          </div>
        )}
      </div>
    </div>
  );
}
