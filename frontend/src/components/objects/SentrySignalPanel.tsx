import type { RiskObject } from "@/api/types";
import { formatBoolean, formatNumber } from "@/lib/formatters";

type SentrySignalPanelProps = {
  object?: RiskObject | null;
};

export function SentrySignalPanel({ object }: SentrySignalPanelProps) {
  const fields = [
    ["sentry flag", formatBoolean(object?.sentry_flag)],
    ["impact probability", formatNumber(object?.sentry_ip, { maximumSignificantDigits: 4 })],
    ["palermo cumulative", formatNumber(object?.sentry_ps_cum, { maximumFractionDigits: 3 })],
    ["palermo max", formatNumber(object?.sentry_ps_max, { maximumFractionDigits: 3 })],
    ["torino max", formatNumber(object?.sentry_ts_max, { maximumFractionDigits: 2 })],
    ["impact solutions", formatNumber(object?.sentry_n_imp, { maximumFractionDigits: 0 })]
  ];

  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <h3 className="mb-3 font-semibold text-white">Sentry signal</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label}>
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-sm text-slate-100">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
