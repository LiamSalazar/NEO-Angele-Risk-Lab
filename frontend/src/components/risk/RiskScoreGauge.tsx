import { Activity } from "lucide-react";

import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { formatScore } from "@/lib/formatters";
import { scoreColor, scoreToCategory } from "@/lib/risk";

type RiskScoreGaugeProps = {
  score?: number | null;
  category?: string | null;
};

export function RiskScoreGauge({ score, category }: RiskScoreGaugeProps) {
  const value = Math.max(0, Math.min(100, Number(score ?? 0)));
  const radius = 70;
  const circumference = Math.PI * radius;
  const dashOffset = circumference - (value / 100) * circumference;
  const resolvedCategory = category || scoreToCategory(value);
  const color = scoreColor(value, resolvedCategory);

  return (
    <div className="relative overflow-hidden rounded-lg border border-cyan-300/15 bg-slate-950/45 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="technical-label text-xs text-cyan-100">Experimental priority score</p>
          <p className="mt-2 text-sm text-slate-400">Composite follow-up score, not an official alert.</p>
        </div>
        <RiskCategoryBadge category={resolvedCategory} />
      </div>
      <div className="mt-4 grid place-items-center">
        <svg viewBox="0 0 180 112" className="h-36 w-full max-w-[280px]" role="img">
          <path
            d="M20 90 A70 70 0 0 1 160 90"
            fill="none"
            stroke="rgba(148,197,211,0.14)"
            strokeWidth="14"
            strokeLinecap="round"
          />
          <path
            d="M20 90 A70 70 0 0 1 160 90"
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
          />
          <line
            x1="90"
            y1="90"
            x2={90 + 55 * Math.cos(Math.PI - (Math.PI * value) / 100)}
            y2={90 - 55 * Math.sin(Math.PI - (Math.PI * value) / 100)}
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
          />
          <circle cx="90" cy="90" r="5" fill={color} />
        </svg>
        <div className="-mt-10 text-center">
          <div className="flex items-center justify-center gap-2">
            <Activity className="h-5 w-5" style={{ color }} />
            <p className="font-mono text-5xl font-semibold text-white" data-testid="risk-score-value">
              {formatScore(value)}
            </p>
          </div>
          <p className="technical-label mt-1 text-[11px] text-slate-500">0-100 lab scale</p>
        </div>
      </div>
    </div>
  );
}
