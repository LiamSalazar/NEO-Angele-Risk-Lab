import type { ApiRecord } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/formatters";

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
            <div>
              <p className="font-mono text-sm text-white">{key}</p>
              <p className="text-xs text-slate-500">
                similarity {formatNumber(neighbor.similarity, { maximumFractionDigits: 4 })}
              </p>
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
