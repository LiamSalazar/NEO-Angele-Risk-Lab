import type { RiskObject } from "@/api/types";
import type { ReactNode } from "react";
import { formatNumber } from "@/lib/formatters";

type OrbitalElementsPanelProps = {
  object?: RiskObject | null;
};

const fields = [
  ["semi-major axis", "a", 4],
  ["eccentricity", "e", 4],
  ["inclination", "i", 3],
  ["perihelion q", "q", 4],
  ["MOID", "moid", 6],
  ["condition code", "condition_code", 1],
  ["arc length", "arc_length", 0],
  ["observations", "n_obs_used", 0]
] as const;

export function OrbitalElementsPanel({ object }: OrbitalElementsPanelProps) {
  return (
    <Panel title="Orbital elements">
      {fields.map(([label, key, precision]) => (
        <Metric
          key={key}
          label={label}
          value={formatNumber(object?.[key], { maximumFractionDigits: precision })}
        />
      ))}
    </Panel>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <h3 className="mb-3 font-semibold text-white">{title}</h3>
      <div className="grid gap-3 sm:grid-cols-2">{children}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-sm text-slate-100">{value}</p>
    </div>
  );
}
