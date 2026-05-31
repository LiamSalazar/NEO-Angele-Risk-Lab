import ReactECharts from "echarts-for-react";
import { Layers3, Orbit, Play } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { Finding, OrbitalSimulationResult } from "@/api/types";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/layout/PageHeader";
import { ObjectSearch } from "@/components/objects/ObjectSearch";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useFindingsGroupQuery } from "@/hooks/useFindings";
import {
  useLatestOrbitalSimulationQuery,
  useRunOrbitalBatchMutation,
  useRunOrbitalSimulationMutation
} from "@/hooks/useOrbitalSimulation";
import { useObjectsQuery } from "@/hooks/useRiskRanking";
import { baseChartOptions } from "@/lib/charts";
import { formatNumber, objectKey } from "@/lib/formatters";

export function OrbitalSimulationPage() {
  const objects = useObjectsQuery({ limit: 250 });
  const [selectedObjectKey, setSelectedObjectKey] = useState("");
  const [nClones, setNClones] = useState(300);
  const [horizonDays, setHorizonDays] = useState(3650);
  const [timeStepDays, setTimeStepDays] = useState(10);
  const firstKey = objects.data?.objects?.[0] ? objectKey(objects.data.objects[0]) : "";
  const activeKey = selectedObjectKey || firstKey;
  const latest = useLatestOrbitalSimulationQuery(activeKey);
  const runObject = useRunOrbitalSimulationMutation();
  const runBatch = useRunOrbitalBatchMutation();
  const findings = useFindingsGroupQuery("orbitalSimulation");

  const result = (runObject.data?.result || latest.data?.result || null) as
    | OrbitalSimulationResult
    | null;
  const findingRows = ((findings.data?.details?.findings ?? []) as Finding[]).slice(0, 3);

  if (objects.isLoading) {
    return <LoadingState label="Loading orbital simulation candidates" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Orbital simulation"
        title="Approximate Orbital Scenario Analysis"
        description="Perturb available orbital elements and estimate Earth-object distance bands across a simplified two-body horizon."
        actions={
          <Button
            type="button"
            disabled={runBatch.isPending}
            onClick={() =>
              runBatch.mutate({
                limit: 50,
                n_clones: nClones,
                horizon_days: horizonDays,
                time_step_days: timeStepDays,
                random_state: 42
              })
            }
          >
            <Layers3 className="h-4 w-4" />
            {runBatch.isPending ? "Running batch" : "Run batch"}
          </Button>
        }
      />

      {runObject.isError ? <ErrorState error={runObject.error} endpoint="/orbital-simulation/object" /> : null}
      {runBatch.isError ? <ErrorState error={runBatch.error} endpoint="/orbital-simulation/batch" /> : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Scenario Controls</CardTitle>
            <CardDescription>Approximate orbital scenario analysis based on available orbital elements.</CardDescription>
          </div>
          <Orbit className="h-5 w-5 text-cyan-100" />
        </CardHeader>
        <CardContent className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_140px_160px_160px_160px]">
          <ObjectSearch objects={objects.data?.objects} onSelect={setSelectedObjectKey} />
          <NumberField label="clones" value={nClones} min={20} onChange={setNClones} />
          <NumberField label="horizon days" value={horizonDays} min={30} onChange={setHorizonDays} />
          <NumberField label="step days" value={timeStepDays} min={1} onChange={setTimeStepDays} />
          <Button
            type="button"
            variant="primary"
            disabled={!activeKey || runObject.isPending}
            onClick={() =>
              runObject.mutate({
                object_key: activeKey,
                n_clones: nClones,
                horizon_days: horizonDays,
                time_step_days: timeStepDays,
                random_state: 42
              })
            }
          >
            <Play className="h-4 w-4" />
            {runObject.isPending ? "Running" : "Run"}
          </Button>
        </CardContent>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Distance Band</CardTitle>
              <CardDescription>p05 / p50 / p95 distance envelope across clone scenarios.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <OrbitalDistanceChart result={result} />
          </CardContent>
        </Card>
        <div className="space-y-6">
          <ScenarioCards result={result} />
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Interpretation</CardTitle>
                <CardDescription>Concise scenario reading for the selected object.</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-6 text-slate-300">
                {result?.interpretation ??
                  "Run an orbital simulation or select an object with saved orbital results."}
              </p>
              {result?.object_key ? (
                <Button asChild className="mt-4" size="sm">
                  <Link to={`/objects/${encodeURIComponent(result.object_key)}`}>Open profile</Link>
                </Button>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Orbital Simulation Findings</CardTitle>
            <CardDescription>Objects with high dispersion or low lower-tail distance.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          {findingRows.length ? (
            findingRows.map((finding) => <FindingCard key={finding.title} finding={finding} />)
          ) : (
            <p className="text-sm text-slate-500">Orbital findings are pending.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  onChange
}: {
  label: string;
  value: number;
  min: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="technical-label mb-1 block text-[10px] text-slate-500">{label}</span>
      <Input
        type="number"
        min={min}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function ScenarioCards({ result }: { result: OrbitalSimulationResult | null }) {
  const cards = [
    ["min distance p05", result?.simulated_min_distance_p05_au, "AU"],
    ["min distance p50", result?.simulated_min_distance_p50_au, "AU"],
    ["min distance p95", result?.simulated_min_distance_p95_au, "AU"],
    ["dispersion index", result?.dispersion_index, ""],
    ["closest day mean", result?.closest_approach_day_mean, "days"],
    ["scenario", result?.scenario_category, ""]
  ];
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Scenario Summary</CardTitle>
          <CardDescription>{result?.object_key ?? "No object selected"}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2">
        {cards.map(([label, value, unit]) => (
          <div key={label} className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
            <p className="technical-label text-[10px] text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-lg text-white">
              {typeof value === "number"
                ? `${formatNumber(value, { maximumFractionDigits: 4 })}${unit ? ` ${unit}` : ""}`
                : String(value ?? "pending")}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function OrbitalDistanceChart({ result }: { result: OrbitalSimulationResult | null }) {
  const trace = result?.distance_trace;
  const option = useMemo(
    () => ({
      ...baseChartOptions,
      xAxis: { type: "category", data: trace?.day ?? [] },
      yAxis: { type: "value", name: "AU" },
      legend: { textStyle: { color: "#94a3b8" } },
      series: [
        { name: "p05", type: "line", smooth: true, data: trace?.p05 ?? [] },
        { name: "p50", type: "line", smooth: true, data: trace?.p50 ?? [] },
        { name: "p95", type: "line", smooth: true, data: trace?.p95 ?? [] }
      ]
    }),
    [trace]
  );
  if (!trace?.day?.length) {
    return (
      <div className="grid h-[360px] place-items-center rounded-md border border-cyan-300/12 bg-slate-950/35 text-sm text-slate-500">
        Run a simulation to render the distance band.
      </div>
    );
  }
  return <ReactECharts option={option} style={{ height: 420, width: "100%" }} />;
}

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-4">
      <h3 className="text-sm font-semibold text-white">{finding.title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-300">{finding.short_text}</p>
      {finding.related_objects?.length ? (
        <p className="mt-2 text-xs text-slate-500">
          Objects: {finding.related_objects.slice(0, 5).join(", ")}
        </p>
      ) : null}
    </div>
  );
}
