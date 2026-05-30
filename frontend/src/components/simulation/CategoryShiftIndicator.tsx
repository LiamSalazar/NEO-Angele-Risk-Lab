import { GitCompareArrows } from "lucide-react";

import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { formatPercent } from "@/lib/formatters";

type CategoryShiftIndicatorProps = {
  probability?: number | null;
  baseCategory?: string | null;
  p95Category?: string | null;
};

export function CategoryShiftIndicator({
  probability,
  baseCategory,
  p95Category
}: CategoryShiftIndicatorProps) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <div className="flex items-center gap-2">
        <GitCompareArrows className="h-4 w-4 text-cyan-100" />
        <h3 className="font-semibold text-white">Category shift</h3>
      </div>
      <p className="mt-3 font-mono text-3xl text-white">{formatPercent(probability ?? 0)}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <RiskCategoryBadge category={baseCategory} />
        <span className="text-xs text-slate-500">to p95</span>
        <RiskCategoryBadge category={p95Category} />
      </div>
    </div>
  );
}
