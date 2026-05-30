import type { RiskObject } from "@/api/types";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { formatBoolean, formatNumber, objectDisplayName, objectKey } from "@/lib/formatters";

type ObjectSummaryCardProps = {
  object?: RiskObject | null;
};

export function ObjectSummaryCard({ object }: ObjectSummaryCardProps) {
  const fields = [
    ["object_key", objectKey(object)],
    ["designation", object?.des],
    ["PHA", formatBoolean(object?.pha)],
    ["Sentry", formatBoolean(object?.sentry_flag)],
    ["MOID", formatNumber(object?.moid, { maximumFractionDigits: 5 })],
    ["H", formatNumber(object?.h, { maximumFractionDigits: 2 })]
  ];

  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="technical-label text-[11px] text-slate-500">Mission object</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{objectDisplayName(object)}</h2>
        </div>
        <RiskCategoryBadge category={object?.risk_category} />
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border border-cyan-300/10 bg-black/20 p-3">
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 truncate font-mono text-sm text-slate-100">{String(value ?? "n/a")}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
