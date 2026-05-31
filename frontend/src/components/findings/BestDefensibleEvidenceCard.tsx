import { Activity, ChevronDown, ChevronUp, Database, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber, formatPercent } from "@/lib/formatters";

type EvidenceDetails = Record<string, unknown>;

const metricLabels = [
  ["accuracy", "Accuracy", "percent"],
  ["f1", "F1", "decimal"],
  ["pr_auc", "PR-AUC", "decimal"],
  ["precision", "Precision", "percent"],
  ["recall", "Recall", "percent"],
  ["false_negative_rate", "False Negative Rate", "percent"]
] as const;

export function BestDefensibleEvidenceCard({ details }: { details?: EvidenceDetails | null }) {
  const [expanded, setExpanded] = useState(false);
  const model = asRecord(details?.best_defensible_model);
  const metrics = asRecord(model.metrics);
  const family = text(model.model_family, "model");
  const featureSet = text(model.feature_set, "n/a");
  const leakageRisk = text(model.leakage_risk, "low");
  const interpretation = text(
    details?.best_defensible_model_interpretation ??
      details?.main_evidence_conclusion ??
      model.interpretation,
    "No defensible model evidence is available yet."
  );
  const coverageTotal =
    number(details?.total_risk_objects) || number(details?.total_gold_objects) || 0;
  const coverageUnique = number(details?.unique_full_object_keys) || 0;
  const recommendedUse = text(details?.recommended_use ?? model.recommended_use, "secondary evidence");
  const rankingSource = text(details?.ranking_source, "Risk Priority Score");

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Best Defensible Evidence</CardTitle>
          <CardDescription>
            Secondary model evidence selected for interpretability and lower leakage risk.
          </CardDescription>
        </div>
        <ShieldCheck className="h-5 w-5 text-cyan-100" />
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex flex-wrap gap-2">
          <EvidenceBadge label="Model" value={modelName(text(model.model_name, "n/a"))} />
          <EvidenceBadge label="Family" value={family} />
          <EvidenceBadge label="Feature set" value={featureSet} />
          <EvidenceBadge label="Target" value={text(model.target, "PHA").toUpperCase()} />
          <Badge variant={leakageVariant(leakageRisk)}>Leakage risk: {leakageRisk}</Badge>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {metricLabels.map(([key, label, format]) => (
            <MetricTile
              key={key}
              label={label}
              value={formatMetric(metrics[key], format)}
            />
          ))}
        </div>

        <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100">
            <Activity className="h-4 w-4" />
            Interpretation
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{interpretation}</p>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <EvidenceList title="Strengths" items={strengthsFor(family, featureSet, leakageRisk)} />
          <EvidenceList title="Limitations" items={limitationsFor(family)} muted />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <OperationalItem
            label="Coverage"
            value={`${formatNumber(coverageUnique, { maximumFractionDigits: 0 })} / ${formatNumber(
              coverageTotal,
              { maximumFractionDigits: 0 }
            )} objects`}
          />
          <OperationalItem label="Coverage ratio" value={formatPercent(details?.coverage_ratio)} />
          <OperationalItem
            label="Disagreements"
            value={formatNumber(details?.disagreement_count, { maximumFractionDigits: 0 })}
          />
          <OperationalItem label="Recommended use" value={recommendedUse} />
          <OperationalItem label="Ranking source" value={rankingSource} />
        </div>

        <div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            View technical details
          </Button>
          {expanded ? (
            <pre className="mt-3 max-h-[360px] overflow-auto rounded-md border border-cyan-300/12 bg-black/35 p-3 font-mono text-xs leading-5 text-slate-300">
              {JSON.stringify(details ?? {}, null, 2)}
            </pre>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function EvidenceBadge({ label, value }: { label: string; value: string }) {
  return (
    <Badge variant="cyan">
      <span className="text-slate-400">{label}:</span>
      <span>{value}</span>
    </Badge>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <p className="technical-label text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-lg text-white">{value}</p>
    </div>
  );
}

function EvidenceList({
  title,
  items,
  muted
}: {
  title: string;
  items: string[];
  muted?: boolean;
}) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-4">
      <p className="technical-label text-[10px] text-slate-500">{title}</p>
      <ul className="mt-3 space-y-2 text-sm leading-5 text-slate-300">
        {items.map((item) => (
          <li key={item} className={muted ? "text-slate-400" : undefined}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function OperationalItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <div className="flex items-center gap-2">
        <Database className="h-3.5 w-3.5 text-cyan-100" />
        <p className="technical-label text-[10px] text-slate-500">{label}</p>
      </div>
      <p className="mt-1 text-sm font-medium text-slate-100">{value}</p>
    </div>
  );
}

function strengthsFor(family: string, featureSet: string, leakageRisk: string) {
  if (["gnn", "graph"].includes(family.toLowerCase())) {
    return [
      "Captures relational/orbital neighborhood structure.",
      "Supports pattern consistency analysis.",
      "Useful as secondary validation."
    ];
  }
  const items = [
    "Focuses on interpretable feature groups.",
    "Supports pattern consistency analysis.",
    "Useful as secondary validation."
  ];
  if (leakageRisk === "low" || featureSet.includes("no_definition")) {
    items[0] = "Avoids direct PHA definition variables.";
  }
  return items;
}

function limitationsFor(family: string) {
  if (["gnn", "graph"].includes(family.toLowerCase())) {
    return [
      "Does not define the risk ranking.",
      "Depends on graph construction quality.",
      "Leakage-sensitive models must not be treated as primary evidence."
    ];
  }
  return [
    "Does not define the risk ranking.",
    "Depends on active dataset labels and feature quality.",
    "Leakage-sensitive models must not be treated as primary evidence."
  ];
}

function formatMetric(value: unknown, format: "percent" | "decimal") {
  if (format === "percent") {
    return formatPercent(value);
  }
  return formatNumber(value, { maximumFractionDigits: 3 });
}

function leakageVariant(value: string) {
  const normalized = value.toLowerCase();
  if (normalized === "high") return "red";
  if (normalized === "medium") return "amber";
  return "green";
}

function modelName(value: string) {
  const normalized = value.toLowerCase();
  if (normalized === "graphsage") return "GraphSAGE";
  if (normalized === "gcn") return "GCN";
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function asRecord(value: unknown): EvidenceDetails {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as EvidenceDetails)
    : {};
}

function text(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function number(value: unknown) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}
