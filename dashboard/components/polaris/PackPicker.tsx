"use client";
// Phase-12 T6 — Pre-built policy pack picker. Shows alongside the Dropzone so
// operators can skip the PDF pipeline and deploy a curated SOC2 / HIPAA /
// EU-AI-Act / PCI-DSS policy in one click. Also serves as demo insurance:
// if the PDF parse fails mid-recording, packs are the fallback path.
import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
import { I } from "./icons";

type Pack = { name: string; filename: string };

const PACK_LABELS: Record<string, string> = {
  soc2: "SOC 2",
  hipaa: "HIPAA",
  eu_ai_act: "EU AI Act",
  pci_dss: "PCI-DSS",
};

export function PackPicker({
  onDeployed,
  disabled,
}: {
  onDeployed: (jobId: string, pack: string) => void;
  disabled?: boolean;
}) {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetch(`${API_BASE}/api/policies/packs`)
      .then((r) => r.json())
      .then((d) => {
        if (!cancelled && Array.isArray(d.packs)) setPacks(d.packs);
      })
      .catch(() => {
        /* dashboard renders empty grid; not worth a toast */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function deploy(name: string) {
    if (disabled || busy) return;
    setBusy(name);
    setErr(null);
    try {
      const r = await fetch(`${API_BASE}/api/policies/packs/${name}/deploy`, {
        method: "POST",
      });
      if (!r.ok) {
        const body = await r.text().catch(() => "");
        throw new Error(`deploy failed (${r.status}): ${body.slice(0, 200)}`);
      }
      const data = (await r.json()) as { job_id: string; pack: string };
      onDeployed(data.job_id, data.pack);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(null);
    }
  }

  if (packs.length === 0) return null;
  return (
    <div className="pack-picker">
      <div className="pack-picker__head">
        <I.Layers /> Or deploy a pre-built pack
      </div>
      <div className="pack-picker__grid">
        {packs.map((p) => (
          <button
            key={p.name}
            className={"pack-card" + (busy === p.name ? " pack-card--busy" : "")}
            onClick={() => deploy(p.name)}
            disabled={disabled || busy !== null}
            type="button"
          >
            {PACK_LABELS[p.name] ?? p.name.replace(/_/g, " ").toUpperCase()}
          </button>
        ))}
      </div>
      {err && <div className="pack-picker__err">{err}</div>}
    </div>
  );
}
