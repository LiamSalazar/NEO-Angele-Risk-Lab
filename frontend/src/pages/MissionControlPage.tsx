import { Activity, BrainCircuit, Database, GitBranch, Radar, ShieldAlert, Sigma } from "lucide-react";
import { Link } from "react-router-dom";

import type { RankingSummary } from "@/api/types";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";
import { MissionCard } from "@/components/mission/MissionCard";
import { RiskRadar } from "@/components/mission/RiskRadar";
import { SystemStatusBeacon } from "@/components/mission/SystemStatusBeacon";
import { TelemetryStrip } from "@/components/mission/TelemetryStrip";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useGNNStatusQuery, useRankingSummaryQuery, useRankingTopQuery, useSimulationStatusQuery } from "@/api/queries";
import { useApiHealth, useSystemStatus } from "@/hooks/useApiHealth";
import { formatNumber, formatScore, objectDisplayName, objectKey } from "@/lib/formatters";

export function MissionControlPage() {
  const health = useApiHealth();
  const status = useSystemStatus();
  const rankingSummary = useRankingSummaryQuery();
  const topRanking = useRankingTopQuery(5);
  const gnnStatus = useGNNStatusQuery();
  const simulationStatus = useSimulationStatusQuery();

  const summary = (rankingSummary.data?.details ?? {}) as RankingSummary;
  const readiness = gnnStatus.data?.result?.dataset_readiness;
  const phaCount = readiness?.pha_distribution?.true ?? 0;
  const gnn = gnnStatus.data?.result;
  const statusDetails = status.data?.details;
  const mlManifestStatus = statusDetails?.latest_manifests?.ml?.status;
  const simulationDetails = (simulationStatus.data as Record<string, unknown> | undefined) ?? {};

  if (health.isLoading && status.isLoading) {
    return <LoadingState label="Opening mission control" />;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="console-panel overflow-hidden rounded-lg p-6 md:p-8">
          <div className="relative z-10 max-w-4xl">
            <div className="mb-5 flex flex-wrap items-center gap-3">
              <SystemStatusBeacon state={health.isError ? "unavailable" : health.data?.status} label="API" />
              <SystemStatusBeacon state={rankingSummary.data?.status || "missing_data"} label="Risk" />
              <SystemStatusBeacon state={gnnStatus.data?.status || "missing_data"} label="GNN" />
            </div>
            <p className="technical-label text-sm text-cyan-100">Neo Angele Risk Lab</p>
            <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-normal text-white md:text-6xl">
              Near-Earth Object risk intelligence, simulation and graph research observatory.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
              Mission-control interface for NASA/JPL-derived NEO data products, experimental risk
              priority scoring, Monte Carlo stability analysis and orbital graph research.
            </p>
          </div>
        </div>
        <RiskRadar topScore={summary.score_max} objectCount={summary.n_objects} />
      </section>

      {rankingSummary.isError ? (
        <ErrorState error={rankingSummary.error} endpoint="/rankings/summary" />
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MissionCard label="total objects" value={formatNumber(summary.n_objects, { maximumFractionDigits: 0 })} detail="scored/ranked population" icon={Database} />
        <MissionCard label="risk scores" value={formatNumber(statusDetails?.risk?.row_count ?? summary.n_objects, { maximumFractionDigits: 0 })} detail={statusDetails?.risk?.risk_scores_available ? "risk parquet available" : "risk build pending"} icon={Radar} tone={statusDetails?.risk?.risk_scores_available ? "green" : "amber"} />
        <MissionCard label="PHA count" value={formatNumber(phaCount, { maximumFractionDigits: 0 })} detail="from readiness report" icon={ShieldAlert} tone="amber" />
        <MissionCard label="GNN graph" value={`${formatNumber(gnn?.node_count, { maximumFractionDigits: 0 })}/${formatNumber(gnn?.edge_count, { maximumFractionDigits: 0 })}`} detail="nodes / edges" icon={GitBranch} tone={gnn?.graph_exists ? "green" : "neutral"} />
        <MissionCard label="latest simulation" value={String(simulationDetails.latest_manifest_status ?? simulationDetails.status ?? "unknown")} detail={`${formatNumber(simulationDetails.row_count, { maximumFractionDigits: 0 })} saved rows`} icon={Activity} />
        <MissionCard label="dataset readiness" value={readiness?.status ?? "unknown"} detail={readiness?.recommended_next_command ?? "readiness report"} icon={Sigma} tone={readiness?.status === "strong" ? "green" : "cyan"} />
        <MissionCard label="ML / leakage" value={String(mlManifestStatus ?? "unknown")} detail="reported via /status manifests" icon={BrainCircuit} tone={mlManifestStatus === "success" ? "green" : "amber"} />
        <MissionCard label="reports" value={formatNumber(statusDetails?.risk?.latest_reports?.length ?? 0, { maximumFractionDigits: 0 })} detail="risk reports available" icon={Database} tone="neutral" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Risk Overview</CardTitle>
              <CardDescription>Distribution and score statistics for the current ranking table.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart categoryCounts={summary.category_counts} />
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Stat label="mean" value={formatScore(summary.score_mean)} />
              <Stat label="median" value={formatScore(summary.score_median)} />
              <Stat label="max" value={formatScore(summary.score_max)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Top 5 Objects</CardTitle>
              <CardDescription>Highest experimental priority score.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {topRanking.data?.objects?.length ? (
              topRanking.data.objects.map((object) => (
                <Link
                  key={objectKey(object)}
                  to={`/objects/${encodeURIComponent(objectKey(object))}`}
                  className="block rounded-md border border-cyan-300/12 bg-slate-950/45 p-3 transition hover:border-cyan-300/35"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-mono text-sm text-white">{objectDisplayName(object)}</p>
                      <p className="text-xs text-slate-500">{objectKey(object)}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-lg text-white">{formatScore(object.risk_score_0_100)}</p>
                      <RiskCategoryBadge category={object.risk_category} />
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-sm text-slate-500">No ranked objects yet.</p>
            )}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>System Telemetry</CardTitle>
            <CardDescription>Bronze/Silver/Gold availability, manifests and reports.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <TelemetryStrip
            items={[
              { label: "bronze", value: statusDetails?.bronze_available, ok: statusDetails?.bronze_available },
              { label: "silver", value: statusDetails?.silver_available, ok: statusDetails?.silver_available },
              { label: "gold", value: statusDetails?.gold_features_available, ok: statusDetails?.gold_features_available },
              { label: "risk reports", value: statusDetails?.risk?.latest_reports?.length ?? 0, ok: Boolean(statusDetails?.risk?.latest_reports?.length) },
              { label: "simulation reports", value: statusDetails?.simulation_reports_available, ok: statusDetails?.simulation_reports_available },
              { label: "latest risk manifest", path: statusDetails?.risk?.latest_manifests?.at(-1) },
              { label: "latest simulation manifest", path: statusDetails?.simulation?.latest_manifests?.at(-1) },
              { label: "latest GNN report", path: gnn?.latest_reports?.[0] }
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-xl text-white">{value}</p>
    </div>
  );
}
