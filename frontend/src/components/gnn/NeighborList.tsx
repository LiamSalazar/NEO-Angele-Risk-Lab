import type { ApiRecord } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { formatBoolean, formatNumber, formatScore } from "@/lib/formatters";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";

type NeighborListProps = {
  neighbors?: ApiRecord[];
  onOpenNeighbor?: (objectKey: string) => void;
};

export function NeighborList({ neighbors = [], onOpenNeighbor }: NeighborListProps) {
  if (!neighbors.length) {
    return (
      <EmptyState
        title="No graph neighbors"
        description="The object is absent from the graph, or the graph has not been built."
        command="python -m neo_ange.cli gnn build-graph --k 10 --min-nodes 100"
      />
    );
  }

  return (
    <div className="space-y-2">
      {neighbors.slice(0, 12).map((neighbor, index) => {
        const key = String(neighbor.neighbor_object_key || neighbor.object_key || neighbor.neighbor_node_id || index);
        return (
          <div
            key={`${key}-${index}`}
            className="flex items-center justify-between gap-3 rounded-md border border-cyan-300/12 bg-slate-950/45 p-3"
          >
            <div className="min-w-0">
              <p className="font-mono text-sm text-white">{key}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span>similarity {formatNumber(neighbor.similarity, { maximumFractionDigits: 4 })}</span>
                <span>score {formatScore(neighbor.risk_score_0_100 as number)}</span>
                <span>PHA {formatBoolean(neighbor.pha)}</span>
              </div>
              {neighbor.risk_category ? (
                <div className="mt-2">
                  <RiskCategoryBadge category={String(neighbor.risk_category)} />
                </div>
              ) : null}
            </div>
            {onOpenNeighbor ? (
              <Button type="button" size="sm" onClick={() => onOpenNeighbor(key)}>
                Open
              </Button>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
