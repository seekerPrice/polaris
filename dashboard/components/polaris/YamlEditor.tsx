// YamlEditor — IDE-style streaming YAML view with syntax highlighting,
// blinking cursor, traffic-light header dots.
"use client";
import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

function highlight(line: string): ReactNode {
  if (/^\s*#/.test(line)) return <span className="y-comment">{line}</span>;
  const kv = (rest: string): ReactNode => {
    const m = rest.match(/^([A-Za-z0-9_]+)(:\s*)(.*)$/);
    if (!m) return <span>{rest}</span>;
    const [, key, sep, val] = m;
    let valEl: ReactNode = <span>{val}</span>;
    if (/^"[^"]*"$/.test(val)) valEl = <span className="y-str">{val}</span>;
    else if (/^(true|false)$/.test(val)) valEl = <span className="y-bool">{val}</span>;
    else if (/^-?\d+(\.\d+)?$/.test(val)) valEl = <span className="y-num">{val}</span>;
    else if (val) valEl = <span className="y-str">{val}</span>;
    return (
      <>
        <span className="y-key">{key}</span>
        {sep}
        {valEl}
      </>
    );
  };
  const dash = line.match(/^(\s*-\s+)(.*)$/);
  if (dash) return (
    <>
      <span className="y-dash">{dash[1]}</span>
      {kv(dash[2])}
    </>
  );
  const indent = line.match(/^(\s*)(.*)$/)!;
  return (
    <>
      <span>{indent[1]}</span>
      {kv(indent[2])}
    </>
  );
}

type Props = {
  yaml: string;
  streaming: boolean;
  status?: string | null;
};

export function YamlEditor({ yaml, streaming, status }: Props) {
  const lines = yaml ? yaml.split("\n") : [];
  if (lines.length > 1 && lines[lines.length - 1] === "") lines.pop();
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current && streaming) ref.current.scrollTop = ref.current.scrollHeight;
  }, [yaml, streaming]);

  return (
    <div className="yaml">
      <div className="yaml__head">
        <div className="dots">
          <span className="dot" /><span className="dot" /><span className="dot" />
        </div>
        <div className="file mono">generated/policy.yaml</div>
        {streaming && (
          <div className="stream-pill">
            <span className="pulse" />
            streaming
          </div>
        )}
        {!streaming && status && (
          <div className="stream-pill" style={{ color: "var(--emerald)" }}>
            <span
              className="pulse"
              style={{ background: "var(--emerald)", boxShadow: "0 0 8px var(--emerald)" }}
            />
            {status}
          </div>
        )}
      </div>
      {yaml ? (
        <div className="yaml__body" ref={ref}>
          <div className="yaml__gutter">
            {lines.map((_, i) => <div key={i}>{String(i + 1).padStart(2, " ")}</div>)}
          </div>
          <div className="yaml__code">
            {lines.map((ln, i) => (
              <div key={i}>
                {highlight(ln)}
                {streaming && i === lines.length - 1 && <span className="yaml__cursor" />}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="yaml__body">
          <div className="yaml__empty">
            policy.yaml will stream here
            <br />after the Synthesizer agent runs
          </div>
        </div>
      )}
    </div>
  );
}
