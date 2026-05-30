import { AlertTriangle, BrainCircuit, ShieldQuestion } from "lucide-react";

import { LeakageComparisonChart } from "@/components/charts/LeakageComparisonChart";
import { ModelComparisonChart } from "@/components/charts/ModelComparisonChart";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useGNNStatusQuery } from "@/hooks/useGNN";
import { useSystemStatus } from "@/hooks/useApiHealth";
import { formatNumber } from "@/lib/formatters";

type ExperimentRow = Record<string, unknown>;

export function ModelAndLeakageLabPage() {
  const status = useSystemStatus();
  const readiness = useGNNStatusQuery();
  const mlManifest = (status.data?.details?.latest_manifests?.ml ?? {}) as Record<string, unknown>;
  const metricsSummary = (mlManifest.metrics_summary ?? {}) as Record<string, unknown>;
  const experiments = extractExperiments(metricsSummary);
  const phaDistribution = readiness.data?.result?.dataset_readiness?.pha_distribution;
  const latestMlPaths = status.data?.details?.latest_manifest_paths?.ml ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="ML & leakage lab"
        title="Baseline Models and Leakage Audit"
        description="Model telemetry is displayed honestly from available manifests and readiness reports. Missing metrics remain visible as insufficient data."
      />

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="ML status" value={String(mlManifest.status ?? "unknown")} />
        <Metric label="PHA true" value={formatNumber(phaDistribution?.true, { maximumFractionDigits: 0 })} />
        <Metric label="PHA false" value={formatNumber(phaDistribution?.false, { maximumFractionDigits: 0 })} />
        <Metric label="manifests" value={latestMlPaths.length} />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Baseline Metrics</CardTitle>
              <CardDescription>Precision, recall, F1, PR-AUC and ROC-AUC when available.</CardDescription>
            </div>
            <BrainCircuit className="h-5 w-5 text-cyan-100" />
          </CardHeader>
          <CardContent>
            <ModelComparisonChart metrics={experiments} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Feature Set Leakage Comparison</CardTitle>
              <CardDescription>Feature-set comparisons should reveal trivial learning risk.</CardDescription>
            </div>
            <ShieldQuestion className="h-5 w-5 text-amber-100" />
          </CardHeader>
          <CardContent>
            <LeakageComparisonChart rows={experiments} />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Leakage Interpretation</CardTitle>
              <CardDescription>Technical caveats for target-definition-adjacent features.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            {[
              ["H / diameter", "Physical definition signals can dominate PHA-like targets when not audited."],
              ["MOID", "Orbital proximity is scientifically meaningful and can also become a target shortcut."],
              ["Sentry fields", "Sentry-related variables should be isolated to prevent circular conclusions."]
            ].map(([title, body]) => (
              <div key={title} className="rounded-lg border border-amber-300/18 bg-amber-300/8 p-4">
                <div className="mb-2 flex items-center gap-2 text-amber-100">
                  <AlertTriangle className="h-4 w-4" />
                  <h3 className="font-semibold">{title}</h3>
                </div>
                <p className="text-sm leading-6 text-amber-50/80">{body}</p>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Available ML Reports</CardTitle>
              <CardDescription>Latest manifest paths exposed by `/status`.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {latestMlPaths.length ? (
              <div className="space-y-2">
                {latestMlPaths.map((path) => (
                  <p key={path} className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3 font-mono text-xs text-slate-300">
                    {path}
                  </p>
                ))}
              </div>
            ) : (
              <EmptyState
                title="ML reports unavailable"
                description="No ML manifest was found through /status."
                command="python -m neo_ange.cli ml run-all"
              />
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function extractExperiments(metricsSummary: Record<string, unknown>): ExperimentRow[] {
  const candidates = [
    metricsSummary.experiments,
    metricsSummary.results,
    metricsSummary.comparison,
    metricsSummary.feature_set_results
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate.map((item) => flattenExperiment(item as Record<string, unknown>));
    }
  }

  return [];
}

function flattenExperiment(row: Record<string, unknown>): ExperimentRow {
  const metrics = (row.metrics ?? {}) as Record<string, unknown>;
  return { ...row, ...metrics };
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-2xl text-white">{String(value ?? "n/a")}</p>
    </div>
  );
}
