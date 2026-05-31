import { Activity, AlertTriangle, Layers3 } from "lucide-react";
import { useMemo, useState } from "react";

import { MonteCarloHistogram } from "@/components/charts/MonteCarloHistogram";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/layout/PageHeader";
import { CategoryShiftIndicator } from "@/components/simulation/CategoryShiftIndicator";
import { SimulationControlPanel } from "@/components/simulation/SimulationControlPanel";
import { SimulationSummary } from "@/components/simulation/SimulationSummary";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  useLatestSimulationQuery,
  useSimulateBatchMutation,
  useSimulateObjectMutation,
  useSimulationStatusQuery
} from "@/hooks/useSimulation";
import { useObjectsQuery } from "@/hooks/useRiskRanking";
import { objectKey } from "@/lib/formatters";

export function MonteCarloLabPage() {
  const objects = useObjectsQuery({ limit: 250 });
  const [selectedObjectKey, setSelectedObjectKey] = useState("");
  const simulationStatus = useSimulationStatusQuery();
  const runSimulation = useSimulateObjectMutation();
  const firstKey = objects.data?.objects?.[0] ? objectKey(objects.data.objects[0]) : "";
  const activeKey = selectedObjectKey || firstKey;
  const latest = useLatestSimulationQuery(activeKey);
  const runBatch = useSimulateBatchMutation();
  const result = useMemo(
    () => runSimulation.data?.result || latest.data?.result || null,
    [latest.data?.result, runSimulation.data?.result]
  );

  if (objects.isLoading) {
    return <LoadingState label="Loading simulation candidates" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Score simulation"
        title="Score Stability Simulation"
        description="Perturb Risk Priority Score inputs to estimate stability bands, category-shift probability and threshold sensitivity."
        actions={
          <Button
            type="button"
            disabled={runBatch.isPending}
            onClick={() => runBatch.mutate({ limit: 50, n_simulations: 500, random_state: 42 })}
          >
            <Layers3 className="h-4 w-4" />
            {runBatch.isPending ? "Running batch" : "Run batch"}
          </Button>
        }
      />

      {runSimulation.isError ? <ErrorState error={runSimulation.error} endpoint="/simulations/object" /> : null}
      {runBatch.isError ? <ErrorState error={runBatch.error} endpoint="/simulations/batch" /> : null}
      {runBatch.data ? (
        <div className="rounded-lg border border-cyan-300/14 bg-cyan-300/8 p-4 text-sm text-cyan-100">
          Batch simulation finished with status <span className="font-mono">{runBatch.data.status}</span>.
        </div>
      ) : null}

      <SimulationControlPanel
        objects={objects.data?.objects}
        selectedObjectKey={activeKey}
        isRunning={runSimulation.isPending}
        onSelectObject={setSelectedObjectKey}
        onRun={(payload) => {
          setSelectedObjectKey(payload.object_key);
          runSimulation.mutate(payload);
        }}
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Scenario Cloud</CardTitle>
              <CardDescription>Summary quantiles with base-score reference.</CardDescription>
            </div>
            <Activity className="h-5 w-5 text-cyan-100" />
          </CardHeader>
          <CardContent className="space-y-4">
            <SimulationSummary result={result} />
            <MonteCarloHistogram result={result} />
          </CardContent>
        </Card>
        <div className="space-y-6">
          <CategoryShiftIndicator
            probability={result?.category_shift_probability}
            baseCategory={result?.base_category}
            p95Category={result?.p95_category}
          />
          <div className="rounded-lg border border-amber-300/20 bg-amber-300/8 p-4 text-sm leading-6 text-amber-100">
            <div className="mb-2 flex items-center gap-2 font-semibold">
              <AlertTriangle className="h-4 w-4" />
              Score scope
            </div>
            This simulation estimates Risk Priority Score stability. Orbital perturbation scenarios
            live in the Orbital Simulation page.
          </div>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Score Simulation Availability</CardTitle>
                <CardDescription>Saved rows and current status for score-stability results.</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                <StatusLine label="status" value={String((simulationStatus.data as Record<string, unknown> | undefined)?.status ?? "unknown")} />
                <StatusLine label="saved rows" value={String((simulationStatus.data as Record<string, unknown> | undefined)?.row_count ?? 0)} />
                <StatusLine
                  label="interpretation"
                  value="Stable categories support ranking confidence; high shift probabilities mark objects for review."
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 text-sm leading-6 text-slate-300">{value}</p>
    </div>
  );
}
