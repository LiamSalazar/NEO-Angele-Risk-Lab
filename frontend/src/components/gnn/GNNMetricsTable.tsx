import type { ApiRecord } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { formatNumber } from "@/lib/formatters";

type GNNMetricsTableProps = {
  metrics?: ApiRecord[];
};

const columns = ["model", "target", "accuracy", "precision", "recall", "f1", "roc_auc", "status"];

export function GNNMetricsTable({ metrics = [] }: GNNMetricsTableProps) {
  if (!metrics.length) {
    return (
      <EmptyState
        title="GNN metrics unavailable"
        description="Run baselines/GNN experiments to populate the metrics table."
        command="python -m neo_ange.cli gnn compare"
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="text-slate-500">
            {columns.map((column) => (
              <th key={column} className="px-3 py-2 technical-label text-[10px]">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((row, index) => (
            <tr key={`${row.model}-${index}`} className="border-t border-cyan-300/10 text-slate-200">
              {columns.map((column) => {
                const value = row[column];
                return (
                  <td key={column} className="px-3 py-3 font-mono text-xs">
                    {typeof value === "number" ? formatNumber(value, { maximumFractionDigits: 4 }) : String(value ?? "n/a")}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
