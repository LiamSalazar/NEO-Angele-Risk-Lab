import type { RiskObject } from "@/api/types";
import { formatBoolean, formatNumber } from "@/lib/formatters";

type PhysicalPropertiesPanelProps = {
  object?: RiskObject | null;
};

const fields = [
  ["diameter", "diameter", 4],
  ["absolute magnitude H", "h", 2],
  ["albedo", "albedo", 3],
  ["size proxy", "size_proxy_score", 3],
  ["NEO", "neo", 0],
  ["PHA", "pha", 0]
] as const;

export function PhysicalPropertiesPanel({ object }: PhysicalPropertiesPanelProps) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <h3 className="mb-3 font-semibold text-white">Physical properties</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {fields.map(([label, key, precision]) => (
          <div key={key}>
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-sm text-slate-100">
              {key === "neo" || key === "pha"
                ? formatBoolean(object?.[key])
                : formatNumber(object?.[key], { maximumFractionDigits: precision })}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
