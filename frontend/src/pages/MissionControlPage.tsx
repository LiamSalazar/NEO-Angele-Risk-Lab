import { Activity, Database, GitBranch, Lightbulb, Orbit, Radar, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

import type { Finding, RankingSummary } from "@/api/types";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";
import { MissionCard } from "@/components/mission/MissionCard";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useFindingsSummaryQuery,
  useModelEvidenceSummaryQuery
} from "@/hooks/useFindings";
import { useApiHealth, useSystemStatus } from "@/hooks/useApiHealth";
import { useOrbitalSimulationStatusQuery } from "@/hooks/useOrbitalSimulation";
import {
  useGNNStatusQuery,
  useRankingSummaryQuery,
  useRankingTopQuery,
  useSimulationStatusQuery
} from "@/api/queries";
import { formatNumber, formatScore, objectDisplayName, objectKey } from "@/lib/formatters";

export function MissionControlPage() {
  const health = useApiHealth();
  const status = useSystemStatus();
  const rankingSummary = useRankingSummaryQuery();
  const topRanking = useRankingTopQuery(5);
  const findings = useFindingsSummaryQuery();
  const gnnStatus = useGNNStatusQuery();
  const simulationStatus = useSimulationStatusQuery();
  const orbitalStatus = useOrbitalSimulationStatusQuery();
  const modelEvidence = useModelEvidenceSummaryQuery();

  const summary = (rankingSummary.data?.details ?? {}) as RankingSummary;
  const readiness = gnnStatus.data?.result?.dataset_readiness;
  const phaCount = readiness?.pha_distribution?.true ?? 0;
  const nonPhaCount = readiness?.pha_distribution?.false ?? 0;
  const sentryCount = readiness?.sentry_coverage?.covered_rows ?? 0;
  const closeApproachCount = readiness?.cad_coverage?.covered_rows ?? 0;
  const findingRows = ((findings.data?.details?.findings ?? []) as Finding[]).slice(0, 5);
  const modelSummary = modelEvidence.data?.details ?? {};
  const bestModel = modelSummary.best_defensible_model as Record<string, unknown> | undefined;

  if (health.isLoading && status.isLoading) {
    return <LoadingState label="Opening control panel" />;
  }

  return (
    <div className="space-y-6">
      <section className="console-panel overflow-hidden rounded-lg p-6 md:p-8">
        <div className="relative z-10 max-w-5xl">
          <p className="technical-label text-sm text-cyan-100">Neo Angele Risk Lab</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-normal text-white md:text-6xl">
            Control Panel
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300">
            Analytical observatory for the active Near-Earth Object dataset: priority ranking,
            score stability, approximate orbital scenarios, graph neighborhoods and supporting
            model evidence.
          </p>
        </div>
      </section>

      {rankingSummary.isError ? (
        <ErrorState error={rankingSummary.error} endpoint="/rankings/summary" />
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MissionCard
          label="dataset analyzed"
          value={formatNumber(summary.n_objects, { maximumFractionDigits: 0 })}
          detail="active scored objects in this version"
          icon={Database}
        />
        <MissionCard
          label="PHA objects"
          value={formatNumber(phaCount, { maximumFractionDigits: 0 })}
          detail={`${formatNumber(nonPhaCount, { maximumFractionDigits: 0 })} non-PHA labels`}
          icon={ShieldAlert}
          tone="amber"
        />
        <MissionCard
          label="elevated priority"
          value={formatNumber(summary.category_counts?.elevated ?? 0, { maximumFractionDigits: 0 })}
          detail="objects above the moderate review band"
          icon={Radar}
          tone="cyan"
        />
        <MissionCard
          label="top score"
          value={formatScore(summary.score_max)}
          detail={summary.top_object ? objectDisplayName(summary.top_object) : "top object pending"}
          icon={Lightbulb}
          tone="green"
        />
        <MissionCard
          label="score simulation"
          value={formatNumber((simulationStatus.data as Record<string, unknown> | undefined)?.row_count, {
            maximumFractionDigits: 0
          })}
          detail="saved score-stability scenarios"
          icon={Activity}
          tone="green"
        />
        <MissionCard
          label="orbital simulation"
          value={formatNumber(orbitalStatus.data?.details?.row_count, { maximumFractionDigits: 0 })}
          detail="approximate orbital scenario rows"
          icon={Orbit}
          tone={orbitalStatus.data?.details?.orbital_simulation_available ? "green" : "amber"}
        />
        <MissionCard
          label="orbital graph"
          value={`${formatNumber(gnnStatus.data?.result?.node_count, { maximumFractionDigits: 0 })}/${formatNumber(
            gnnStatus.data?.result?.edge_count,
            { maximumFractionDigits: 0 }
          )}`}
          detail="nodes / similarity edges"
          icon={GitBranch}
          tone={gnnStatus.data?.result?.graph_exists ? "green" : "amber"}
        />
        <MissionCard
          label="model evidence"
          value={String(bestModel?.model_name ?? "pending")}
          detail={String(bestModel?.feature_set ?? "best defensible view")}
          icon={Lightbulb}
          tone={bestModel ? "green" : "amber"}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Risk Overview</CardTitle>
              <CardDescription>
                Score distribution for the active dataset, with mean, median and maximum.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart categoryCounts={summary.category_counts} />
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Stat label="mean score" value={formatScore(summary.score_mean)} />
              <Stat label="median score" value={formatScore(summary.score_median)} />
              <Stat label="max score" value={formatScore(summary.score_max)} />
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-400">
              Most important numbers are interpreted in the Findings page; this panel keeps the
              operational view compact.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Top Objects</CardTitle>
              <CardDescription>Highest experimental priority scores in the current table.</CardDescription>
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

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Main Dataset Conclusions</CardTitle>
              <CardDescription>Generated findings from the active dataset and reports.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {findingRows.length ? (
              findingRows.map((finding) => <FindingRow key={finding.title} finding={finding} />)
            ) : (
              <p className="text-sm text-slate-500">Findings are pending. Run the findings build command.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Data Readiness</CardTitle>
              <CardDescription>Synthesized availability for user-facing analysis.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <Readiness label="Sentry context" value={sentryCount} detail="objects with Sentry fields" />
            <Readiness
              label="Close-approach context"
              value={closeApproachCount}
              detail="objects with approach coverage"
            />
            <Readiness
              label="Graph readiness"
              value={gnnStatus.data?.result?.dataset_readiness?.readiness?.gnn}
              detail="orbital neighborhood evidence"
            />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-white">{finding.title}</h3>
        <span className="technical-label rounded-sm border border-cyan-300/20 px-2 py-1 text-[10px] text-cyan-100">
          {finding.importance ?? "medium"}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-300">{finding.short_text}</p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{finding.technical_basis}</p>
    </div>
  );
}

function Readiness({ label, value, detail }: { label: string; value: unknown; detail: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-lg text-white">
        {typeof value === "number" ? formatNumber(value, { maximumFractionDigits: 0 }) : String(value ?? "pending")}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
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
