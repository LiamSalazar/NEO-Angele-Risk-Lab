import { ExternalLink, Filter } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/layout/PageHeader";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useBuildRiskMutation, useObjectsQuery, useRankingSummaryQuery } from "@/hooks/useRiskRanking";
import { RISK_CATEGORIES } from "@/lib/constants";
import { formatBoolean, formatScore, objectDisplayName, objectKey } from "@/lib/formatters";
import { normalizeCategory } from "@/lib/risk";

export function RiskRankingPage() {
  const [category, setCategory] = useState<string>("all");
  const [sentryOnly, setSentryOnly] = useState(false);
  const [search, setSearch] = useState("");
  const objects = useObjectsQuery({ limit: 500 });
  const summary = useRankingSummaryQuery();
  const buildRisk = useBuildRiskMutation();

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (objects.data?.objects ?? [])
      .filter((object) => category === "all" || normalizeCategory(object.risk_category) === category)
      .filter((object) => !sentryOnly || formatBoolean(object.sentry_flag) === "yes")
      .filter((object) =>
        !needle
          ? true
          : [objectKey(object), objectDisplayName(object), object.des, object.name, object.full_name]
              .filter(Boolean)
              .some((value) => String(value).toLowerCase().includes(needle))
      )
      .sort((a, b) => Number(b.risk_score_0_100 ?? 0) - Number(a.risk_score_0_100 ?? 0));
  }, [category, objects.data?.objects, search, sentryOnly]);

  if (objects.isLoading) {
    return <LoadingState label="Loading ranking telemetry" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Risk ranking"
        title="Experimental Priority Table"
        description="Interactive ranking of scored NEO objects with category, Sentry and object-key filters."
        actions={
          <Button type="button" variant="primary" disabled={buildRisk.isPending} onClick={() => buildRisk.mutate()}>
            {buildRisk.isPending ? "Building" : "Build risk scores"}
          </Button>
        }
      />

      {objects.isError ? <ErrorState error={objects.error} endpoint="/objects" /> : null}
      {buildRisk.isError ? <ErrorState error={buildRisk.error} endpoint="/risk/build" /> : null}
      {buildRisk.data ? (
        <div className="rounded-lg border border-cyan-300/14 bg-cyan-300/8 p-4 text-sm text-cyan-100">
          Risk build finished with status <span className="font-mono">{buildRisk.data.status}</span>.
        </div>
      ) : null}

      <div className="console-panel rounded-lg p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-cyan-100" />
            <Button size="sm" variant={category === "all" ? "primary" : "secondary"} onClick={() => setCategory("all")}>
              All
            </Button>
            {RISK_CATEGORIES.map((item) => (
              <Button key={item} size="sm" variant={category === item ? "primary" : "secondary"} onClick={() => setCategory(item)}>
                {item}
              </Button>
            ))}
            <Button size="sm" variant={sentryOnly ? "primary" : "secondary"} onClick={() => setSentryOnly((value) => !value)}>
              Sentry flag
            </Button>
          </div>
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search object_key, designation or name"
            className="max-w-xl"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Summary label="objects" value={summary.data?.details?.n_objects} />
        <Summary label="mean score" value={summary.data?.details?.score_mean} score />
        <Summary label="median score" value={summary.data?.details?.score_median} score />
        <Summary label="max score" value={summary.data?.details?.score_max} score />
      </div>

      {!filtered.length ? (
        <EmptyState
          title="Risk scores are not available yet"
          description={objects.data?.message || "Build risk scores before exploring ranking rows."}
          command="python -m neo_ange.cli risk build"
        />
      ) : (
        <div className="console-panel overflow-hidden rounded-lg p-3">
          <div className="overflow-x-auto">
            <table className="data-table w-full min-w-[1120px] text-left">
              <thead>
                <tr className="text-slate-500">
                  {[
                    "object_key",
                    "des/name",
                    "score",
                    "category",
                    "physical",
                    "orbital",
                    "approach",
                    "sentry",
                    "uncertainty",
                    "sentry flag",
                    "profile"
                  ].map((column) => (
                    <th key={column} className="px-3 py-2 technical-label text-[10px]">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((object) => {
                  const key = objectKey(object);
                  return (
                    <tr key={key} className="rounded-md bg-slate-950/42 text-sm text-slate-200 transition hover:bg-cyan-300/8">
                      <td className="rounded-l-md px-3 py-3 font-mono text-cyan-100">{key}</td>
                      <td className="px-3 py-3">{objectDisplayName(object)}</td>
                      <td className="px-3 py-3 font-mono text-white">{formatScore(object.risk_score_0_100)}</td>
                      <td className="px-3 py-3"><RiskCategoryBadge category={object.risk_category} /></td>
                      <td className="px-3 py-3 font-mono">{formatScore(Number(object.physical_risk_component ?? 0) * 100)}</td>
                      <td className="px-3 py-3 font-mono">{formatScore(Number(object.orbital_risk_component ?? 0) * 100)}</td>
                      <td className="px-3 py-3 font-mono">{formatScore(Number(object.approach_risk_component ?? 0) * 100)}</td>
                      <td className="px-3 py-3 font-mono">{formatScore(Number(object.sentry_risk_component ?? 0) * 100)}</td>
                      <td className="px-3 py-3 font-mono">{formatScore(Number(object.uncertainty_risk_component ?? 0) * 100)}</td>
                      <td className="px-3 py-3 font-mono">{formatBoolean(object.sentry_flag)}</td>
                      <td className="rounded-r-md px-3 py-3">
                        <Button asChild size="sm">
                          <Link to={`/objects/${encodeURIComponent(key)}`}>
                            Open <ExternalLink className="h-3.5 w-3.5" />
                          </Link>
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Summary({ label, value, score }: { label: string; value: unknown; score?: boolean }) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-2xl text-white">
        {score ? formatScore(value as number) : String(value ?? "n/a")}
      </p>
    </div>
  );
}
