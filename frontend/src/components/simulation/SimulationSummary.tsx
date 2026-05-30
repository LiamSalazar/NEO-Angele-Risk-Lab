import type { SimulationResult } from "@/api/types";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { formatNumber, formatPercent, formatScore } from "@/lib/formatters";

type SimulationSummaryProps = {
  result?: SimulationResult | null;
};

export function SimulationSummary({ result }: SimulationSummaryProps) {
  const metrics = [
    ["base score", formatScore(result?.base_score)],
    ["mean", formatScore(result?.mean_score)],
    ["std", formatNumber(result?.std_score, { maximumFractionDigits: 2 })],
    ["p95", formatScore(result?.p95_score)],
    ["prob > 60", formatPercent(result?.probability_score_above_60 ?? 0)],
    ["prob > 80", formatPercent(result?.probability_score_above_80 ?? 0)]
  ];

  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4" data-testid="simulation-summary">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="technical-label text-[11px] text-slate-500">Monte Carlo output</p>
          <h3 className="mt-1 font-semibold text-white">{result?.object_key || "No object selected"}</h3>
        </div>
        <RiskCategoryBadge category={result?.p95_category || result?.base_category} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map(([label, value]) => (
          <div key={label} className="rounded-md border border-cyan-300/10 bg-black/20 p-3">
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-lg text-white">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
