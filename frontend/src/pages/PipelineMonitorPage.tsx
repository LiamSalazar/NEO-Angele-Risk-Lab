import { CheckCircle2, CircleDashed, ServerCog } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { SystemStatusBeacon } from "@/components/mission/SystemStatusBeacon";
import { TelemetryStrip } from "@/components/mission/TelemetryStrip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useGNNStatusQuery } from "@/hooks/useGNN";
import { useSystemStatus } from "@/hooks/useApiHealth";
import { compactPath, formatNumber } from "@/lib/formatters";

export function PipelineMonitorPage() {
  const status = useSystemStatus();
  const gnnStatus = useGNNStatusQuery();
  const details = status.data?.details;
  const readiness = gnnStatus.data?.result?.dataset_readiness;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Pipeline monitor"
        title="Data Engineering Readiness"
        description="Bronze/Silver/Gold availability, coverage signals, module readiness, manifests and report paths."
      />

      <section className="grid gap-4 md:grid-cols-3">
        <Layer label="bronze" ok={details?.bronze_available} />
        <Layer label="silver" ok={details?.silver_available} />
        <Layer label="gold" ok={details?.gold_features_available} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_430px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Readiness Matrix</CardTitle>
              <CardDescription>ML, risk, simulation, GNN and frontend readiness from data-quality report.</CardDescription>
            </div>
            <ServerCog className="h-5 w-5 text-cyan-100" />
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {Object.entries(readiness?.readiness ?? {}).map(([name, value]) => (
              <div key={name} className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
                <p className="technical-label text-[10px] text-slate-500">{name.replace(/_/g, " ")}</p>
                <div className="mt-2"><SystemStatusBeacon state={value} label={value} /></div>
              </div>
            ))}
            {!readiness?.readiness ? (
              <EmptyState
                title="Readiness unavailable"
                description="Dataset readiness report has not been generated yet."
                command="python -m neo_ange.cli expand coverage"
              />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Coverage</CardTitle>
              <CardDescription>Dataset counts and recommended next command.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(readiness?.counts ?? {}).map(([name, value]) => (
              <div key={name} className="flex items-center justify-between rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
                <span className="technical-label text-[10px] text-slate-500">{name.replace(/_/g, " ")}</span>
                <span className="font-mono text-sm text-white">{formatNumber(value, { maximumFractionDigits: 0 })}</span>
              </div>
            ))}
            <code className="block rounded-md border border-cyan-300/15 bg-black/35 p-3 font-mono text-xs text-cyan-100">
              {readiness?.recommended_next_command || "python -m neo_ange.cli risk build"}
            </code>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Manifests and Reports</CardTitle>
            <CardDescription>Latest paths detected by `/status` and pipeline status helpers.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <TelemetryStrip
            items={[
              { label: "risk scores", value: details?.risk?.risk_scores_available, ok: details?.risk?.risk_scores_available },
              { label: "risk path", path: details?.risk?.risk_scores_path },
              { label: "simulation path", path: details?.simulation?.simulation_results_path },
              { label: "risk report", path: details?.risk?.latest_reports?.[0] },
              { label: "simulation report", path: details?.simulation?.latest_reports?.[0] },
              { label: "gnn report", path: gnnStatus.data?.result?.latest_reports?.[0] },
              { label: "ml manifest", path: details?.latest_manifest_paths?.ml?.at(-1) },
              { label: "readiness", value: readiness?.status ?? "unknown", ok: Boolean(readiness?.status) }
            ]}
          />
          <div className="mt-4 grid gap-2 md:grid-cols-2">
            {(details?.latest_manifest_paths ? Object.entries(details.latest_manifest_paths) : []).map(([name, paths]) => (
              <div key={name} className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
                <p className="technical-label text-[10px] text-slate-500">{name}</p>
                <p className="mt-1 truncate font-mono text-xs text-slate-300" title={paths.at(-1)}>
                  {compactPath(paths.at(-1))}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Layer({ label, ok }: { label: string; ok?: boolean }) {
  return (
    <div className="console-panel rounded-lg p-5">
      <div className="flex items-center justify-between">
        <p className="technical-label text-xs text-cyan-100">{label}</p>
        {ok ? <CheckCircle2 className="h-5 w-5 text-emerald-200" /> : <CircleDashed className="h-5 w-5 text-slate-500" />}
      </div>
      <p className="mt-4 font-mono text-2xl text-white">{ok ? "available" : "missing"}</p>
    </div>
  );
}
