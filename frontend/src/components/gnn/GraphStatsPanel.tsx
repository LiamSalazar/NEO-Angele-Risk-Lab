import type { GNNGraphResult, GNNStatusResult } from "@/api/types";
import { formatNumber } from "@/lib/formatters";

type GraphStatsPanelProps = {
  status?: GNNStatusResult | null;
  graph?: GNNGraphResult | null;
};

export function GraphStatsPanel({ status, graph }: GraphStatsPanelProps) {
  const summary = graph?.graph_summary ?? {};
  const stats: Array<[string, unknown]> = [
    ["node count", status?.node_count ?? graph?.nodes?.length],
    ["edge count", status?.edge_count ?? graph?.edges?.length],
    ["density", summary.density],
    ["average degree", summary.average_degree],
    ["components", summary.connected_components],
    ["readiness", status?.dataset_readiness?.readiness?.gnn]
  ];

  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <h3 className="mb-3 font-semibold text-white">Graph metrics</h3>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {stats.map(([label, value]) => (
          <div key={label} className="rounded-md border border-cyan-300/10 bg-black/20 p-3">
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-sm text-slate-100">
              {typeof value === "number" ? formatNumber(value, { maximumFractionDigits: 4 }) : String(value ?? "n/a")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
