// Pipeline — the 4-stage animated visualisation (Reader → Synthesizer →
// Lobster Trap → Red Team). Derives each stage's status from state slices.
import type { ReactNode } from "react";
import type { State, ProbeView } from "@/lib/state";
import { I } from "./icons";

type StageStatus = "idle" | "active" | "regen" | "done" | "failed";

function statusOfReader(reader: State["reader"]): StageStatus {
  if (reader.status === "completed") return "done";
  if (reader.status === "started" || reader.status === "running") return "active";
  if (reader.status === "failed") return "failed";
  return "idle";
}

function statusOfSynth(synth: State["synth"]): StageStatus {
  if (synth.status === "deployed" || synth.status === "reloaded" || synth.status === "completed") return "done";
  if (synth.status === "started") return "active";
  if (synth.status === "regenerating") return "regen";
  if (synth.status === "failed") return "failed";
  return "idle";
}

function statusOfLT(synth: State["synth"]): StageStatus {
  if (synth.status === "reloaded" || synth.status === "deployed") return "done";
  if (synth.status === "regenerating") return "regen";
  if (synth.status === "completed") return "active";
  return "idle";
}

function statusOfRedTeam(probes: ProbeView[]): StageStatus {
  if (probes.length === 0) return "idle";
  const last = probes[0];
  if (last.is_gap) return "regen";
  if (last.phase === "started") return "active";
  return "done";
}

function Stage({
  icon, name, status, label, metric,
}: {
  icon: ReactNode;
  name: string;
  status: StageStatus;
  label: string;
  metric: ReactNode;
}) {
  return (
    <div className={`stage stage--${status}`}>
      <div className="stage__row1">
        <span className="stage__icon">{icon}</span>
        <span className="stage__name">{name}</span>
        <span className="stage__dot" />
      </div>
      <div className="stage__status">{label}</div>
      <div className="stage__metric">{metric}</div>
    </div>
  );
}

type Props = {
  reader: State["reader"];
  synth: State["synth"];
  probes: ProbeView[];
  policyHash: string | null;
};

export function Pipeline({ reader, synth, probes, policyHash }: Props) {
  const sReader = statusOfReader(reader);
  const sSynth = statusOfSynth(synth);
  const sLT = statusOfLT(synth);
  const sRT = statusOfRedTeam(probes);
  const policyGen = synth.status === "reloaded" ? 5 : sLT !== "idle" ? 4 : "—";
  const probesRun = probes.length;
  const blocked = probes.filter((p) => p.phase === "result" && p.actual_verdict === "DENY").length;

  return (
    <div className="pipeline-card">
      <div className="pipeline-head">
        <span className="label">Live pipeline · 4 agents · 1 closed loop</span>
        <span className="kicker">
          {policyHash ? (
            <>sha256 · <span style={{ color: "var(--cyan)" }}>{policyHash}</span></>
          ) : (
            "awaiting policy"
          )}
        </span>
      </div>
      <div className="pipeline-flow">
        <Stage
          icon={<I.Brain />}
          name="Reader"
          status={sReader}
          label={sReader === "idle" ? "Idle" : sReader === "active" ? "Reading PDF…" : sReader === "done" ? "Done" : "Failed"}
          metric={<>requirements: <strong>{reader.n || "—"}</strong></>}
        />
        <Stage
          icon={<I.Cpu />}
          name="Synthesizer"
          status={sSynth}
          label={
            sSynth === "idle" ? "Idle" :
            sSynth === "active" ? "Streaming YAML…" :
            sSynth === "regen" ? "Patching policy" :
            sSynth === "done" ? "Validated" : "Failed"
          }
          metric={synth.passed === true ? (
            <>test: <strong style={{ color: "var(--emerald)" }}>11/11 pass</strong></>
          ) : (
            <>gemini-3.1-flash-lite</>
          )}
        />
        <Stage
          icon={<I.Shield />}
          name="Lobster Trap"
          status={sLT}
          label={
            sLT === "idle" ? "Standby" :
            sLT === "regen" ? "Hot-reload" :
            sLT === "done" ? "Inline · enforcing" : "Deploying"
          }
          metric={<>gen <strong>{policyGen}</strong> · :8080</>}
        />
        <Stage
          icon={<I.Crosshair />}
          name="Red Team"
          status={sRT}
          label={
            sRT === "idle" ? "Standby" :
            sRT === "active" ? "Probing…" :
            sRT === "regen" ? "Gap found" : "Blocked"
          }
          metric={<>{probesRun} probes · <strong style={{ color: "var(--emerald)" }}>{blocked}</strong> blocked</>}
        />
      </div>
    </div>
  );
}
