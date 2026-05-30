import { Play, Radar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

import { GNNGraphPreview } from "@/components/charts/GNNGraphPreview";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { GNNMetricsTable } from "@/components/gnn/GNNMetricsTable";
import { GNNStatusPanel } from "@/components/gnn/GNNStatusPanel";
import { GraphStatsPanel } from "@/components/gnn/GraphStatsPanel";
import { NeighborList } from "@/components/gnn/NeighborList";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useBuildGNNGraphMutation,
  useGNNGraphQuery,
  useGNNMetricsQuery,
  useGNNNeighborsQuery,
  useGNNSummaryQuery,
  useGNNStatusQuery,
  useRunGNNMutation
} from "@/hooks/useGNN";
import { useObjectsQuery } from "@/hooks/useRiskRanking";
import { objectKey } from "@/lib/formatters";

export function GNNResearchLabPage() {
  const navigate = useNavigate();
  const [selectedObjectKey, setSelectedObjectKey] = useState("");
  const objects = useObjectsQuery({ limit: 250 });
  const status = useGNNStatusQuery();
  const graph = useGNNGraphQuery(220);
  const metrics = useGNNMetricsQuery();
  const summary = useGNNSummaryQuery();
  const neighbors = useGNNNeighborsQuery(selectedObjectKey);
  const buildGraph = useBuildGNNGraphMutation();
  const runGNN = useRunGNNMutation();

  if (status.isLoading && graph.isLoading) {
    return <LoadingState label="Loading graph observatory" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="GNN research lab"
        title="Orbital Similarity Graph"
        description="Experimental graph view for orbital-neighborhood analysis. GraphSAGE/GCN runs are skipped cleanly when torch-geometric is not installed."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="primary" disabled={buildGraph.isPending} onClick={() => buildGraph.mutate({ k: 10, min_nodes: 100 })}>
              <Radar className="h-4 w-4" />
              Build graph
            </Button>
            <Button type="button" disabled={runGNN.isPending} onClick={() => runGNN.mutate({ target: "pha", k: 10, min_nodes: 100 })}>
              <Play className="h-4 w-4" />
              Run lab
            </Button>
          </div>
        }
      />

      {buildGraph.isError ? <ErrorState error={buildGraph.error} endpoint="/gnn/build-graph" /> : null}
      {runGNN.isError ? <ErrorState error={runGNN.error} endpoint="/gnn/run" /> : null}

      <section className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <GNNStatusPanel status={status.data?.status} result={status.data?.result} />
        <GraphStatsPanel status={status.data?.result} graph={graph.data?.result} />
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Graph Preview</CardTitle>
            <CardDescription>Limited node preview for browser performance, colored by risk category.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <GNNGraphPreview nodes={graph.data?.result?.nodes} edges={graph.data?.result?.edges} />
        </CardContent>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Experiment Results</CardTitle>
              <CardDescription>Baselines and optional real GNN metrics.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <GNNMetricsTable metrics={metrics.data?.result?.metrics} />
            {summary.data?.message ? <p className="mt-3 text-sm text-slate-500">{summary.data.message}</p> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Neighbor Explorer</CardTitle>
              <CardDescription>Select an object and inspect graph-adjacent neighbors.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              list="gnn-objects"
              value={selectedObjectKey}
              onChange={(event) => setSelectedObjectKey(event.target.value)}
              placeholder="object_key"
            />
            <datalist id="gnn-objects">
              {objects.data?.objects?.map((object) => (
                <option key={objectKey(object)} value={objectKey(object)} />
              ))}
            </datalist>
            <NeighborList
              neighbors={neighbors.data?.result?.neighbors}
              onOpenNeighbor={(key) => navigate(`/objects/${encodeURIComponent(key)}`)}
            />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
