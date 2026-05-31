import { ExternalLink, Lightbulb } from "lucide-react";
import { Link } from "react-router-dom";

import type { Finding } from "@/api/types";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useFindingsGroupQuery,
  useFindingsSummaryQuery,
  useModelEvidenceSummaryQuery
} from "@/hooks/useFindings";

const groups = [
  { key: "risk", title: "Risk Findings" },
  { key: "scoreSimulation", title: "Score Simulation Findings" },
  { key: "orbitalSimulation", title: "Orbital Simulation Findings" },
  { key: "orbitalGraph", title: "Orbital Graph Findings" },
  { key: "modelEvidence", title: "Model Evidence Findings" }
] as const;

export function FindingsPage() {
  const summary = useFindingsSummaryQuery();
  const modelEvidence = useModelEvidenceSummaryQuery();

  if (summary.isLoading) {
    return <LoadingState label="Loading analytical findings" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Findings"
        title="Analytical Findings"
        description="User-facing conclusions generated from the active NEO dataset, scores, simulations, orbital graph and model evidence."
      />

      {summary.isError ? <ErrorState error={summary.error} endpoint="/findings/summary" /> : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Main Conclusions</CardTitle>
            <CardDescription>Highest-signal observations from the current artifacts.</CardDescription>
          </div>
          <Lightbulb className="h-5 w-5 text-cyan-100" />
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {(((summary.data?.details?.findings ?? []) as Finding[]).slice(0, 6)).map((finding) => (
            <FindingCard key={finding.title} finding={finding} />
          ))}
        </CardContent>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_390px]">
        <div className="space-y-6">
          {groups.map((group) => (
            <FindingGroup key={group.key} groupKey={group.key} title={group.title} />
          ))}
        </div>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Best Defensible Evidence</CardTitle>
              <CardDescription>ML/GNN evidence is secondary support, not the product center.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[360px] overflow-auto rounded-md border border-cyan-300/12 bg-black/35 p-3 font-mono text-xs leading-5 text-slate-300">
              {JSON.stringify(modelEvidence.data?.details?.best_defensible_model ?? {}, null, 2)}
            </pre>
            <p className="mt-4 text-sm leading-6 text-slate-400">
              {String(
                modelEvidence.data?.details?.main_evidence_conclusion ??
                  "Model evidence is pending."
              )}
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function FindingGroup({
  groupKey,
  title
}: {
  groupKey: (typeof groups)[number]["key"];
  title: string;
}) {
  const query = useFindingsGroupQuery(groupKey);
  const findings = (query.data?.details?.findings ?? []) as Finding[];
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>Conclusion, support data and related objects.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {findings.length ? (
          findings.map((finding) => <FindingCard key={finding.title} finding={finding} />)
        ) : (
          <p className="text-sm text-slate-500">No findings available for this group yet.</p>
        )}
      </CardContent>
    </Card>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-white">{finding.title}</h3>
        <ImportanceBadge importance={finding.importance} />
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-300">{finding.short_text}</p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{finding.technical_basis}</p>
      {finding.related_objects?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {finding.related_objects.slice(0, 6).map((key) => (
            <Link
              key={key}
              to={`/objects/${encodeURIComponent(key)}`}
              className="inline-flex items-center gap-1 rounded-sm border border-cyan-300/15 px-2 py-1 font-mono text-xs text-cyan-100 hover:border-cyan-300/40"
            >
              {key}
              <ExternalLink className="h-3 w-3" />
            </Link>
          ))}
        </div>
      ) : null}
      {finding.caveat ? <p className="mt-3 text-xs leading-5 text-amber-100">{finding.caveat}</p> : null}
    </div>
  );
}

function ImportanceBadge({ importance }: { importance?: string | null }) {
  const normalized = (importance ?? "medium").toLowerCase();
  const variant = normalized === "high" ? "red" : normalized === "low" ? "green" : "amber";
  return <Badge variant={variant}>{normalized}</Badge>;
}
