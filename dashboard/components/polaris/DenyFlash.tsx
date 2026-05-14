// DenyFlash — full-screen radial red flash that fires when a DENY audit row
// appears. Self-contained: takes the audit list, watches its head, manages
// its own per-flash IDs and cleanup timers.
"use client";
import { useEffect, useState } from "react";
import type { AuditEntry } from "@/lib/api";

const FLASH_MS = 1050;

export function DenyFlash({ audits }: { audits: AuditEntry[] }) {
  const [flashes, setFlashes] = useState<number[]>([]);
  useEffect(() => {
    const last = audits[0];
    if (!last || last.verdict !== "DENY") return;
    const id = Math.random();
    setFlashes((p) => [...p, id]);
    const t = setTimeout(() => {
      setFlashes((p) => p.filter((x) => x !== id));
    }, FLASH_MS);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audits.length]);
  return (
    <>
      {flashes.map((id) => (
        <div key={id} className="deny-flash" />
      ))}
    </>
  );
}
