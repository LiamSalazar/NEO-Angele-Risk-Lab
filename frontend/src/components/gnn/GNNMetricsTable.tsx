import type { ApiRecord } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { formatNumber } from "@/lib/formatters";

type GNNMetricsTableProps = {
  metrics?: ApiRecord[];
};

const columns = [
  "model_name",
  "model_family",
  "feature_set",
  "target",
  "accuracy",
  "precision",
  "recall",
  "f1",
  "roc_auc",
  "pr_auc",
  "false_negative_rate",
  "status",
  "interpretation"
];

export function GNNMetricsTable({ metrics = [] }: GNNMetricsTableProps) {
  const normalized = metrics.filter((row) => row.model_name || row.model || row.family);

  if (!normalized.length) {
    return (
      <EmptyState
        title="Graph evidence metrics unavailable"
        description="Run graph baselines/GNN experiments to populate evidence metrics."
        command="python -m neo_ange.cli gnn run --target pha --k 10 --min-nodes 100"
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1180px] text-left text-sm">
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
          {normalized.map((row, index) => (
            <tr
              key={`${row.model_name ?? row.model}-${index}`}
              className="border-t border-cyan-300/10 text-slate-200"
            >
              {columns.map((column) => {
                const value = row[column] ?? fallbackValue(row, column);
                return (
                  <td key={column} className="px-3 py-3 font-mono text-xs">
                    {typeof value === "number"
                      ? formatNumber(value, { maximumFractionDigits: 4 })
                      : String(value ?? "pending")}
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

function fallbackValue(row: ApiRecord, column: string) {
  if (column === "model_name") return row.model;
  if (column === "model_family") return row.family ?? "graph";
  if (column === "target") return "pha";
  if (column === "interpretation") {
    const featureSet = String(row.feature_set ?? "");
    if (featureSet === "full_features" || featureSet === "definition_features_only") {
      return "Leakage-sensitive diagnostic; not preferred as user-facing evidence.";
    }
    return "Secondary evidence for orbital and tabular pattern consistency.";
  }
  return undefined;
}
