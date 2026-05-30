import { Database, GitBranch, Orbit } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { MonteCarloHistogram } from "@/components/charts/MonteCarloHistogram";
import { RiskComponentsRadar } from "@/components/charts/RiskComponentsRadar";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { NeighborList } from "@/components/gnn/NeighborList";
import { PageHeader } from "@/components/layout/PageHeader";
import { ObjectSearch } from "@/components/objects/ObjectSearch";
import { ObjectSummaryCard } from "@/components/objects/ObjectSummaryCard";
import { OrbitalElementsPanel } from "@/components/objects/OrbitalElementsPanel";
import { PhysicalPropertiesPanel } from "@/components/objects/PhysicalPropertiesPanel";
import { SentrySignalPanel } from "@/components/objects/SentrySignalPanel";
import { RiskDriverList } from "@/components/risk/RiskDriverList";
import { RiskScoreGauge } from "@/components/risk/RiskScoreGauge";
import { SimulationSummary } from "@/components/simulation/SimulationSummary";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useObjectsQuery } from "@/hooks/useRiskRanking";
import {
  useDomainObjectQuery,
  useGNNNeighborsQuery,
  useLatestSimulationQuery,
  useObjectQuery,
  useRiskExplanationQuery
} from "@/hooks/useObjectProfile";
import { formatScore, objectDisplayName, objectKey } from "@/lib/formatters";

export function AsteroidProfilePage() {
  const params = useParams();
  const navigate = useNavigate();
  const selectedKey = params.objectKey;
  const objects = useObjectsQuery({ limit: 250 });
  const object = useObjectQuery(selectedKey);
  const domain = useDomainObjectQuery(selectedKey);
  const explanation = useRiskExplanationQuery(selectedKey);
  const simulation = useLatestSimulationQuery(selectedKey);
  const neighbors = useGNNNeighborsQuery(selectedKey);
  const currentObject = object.data?.object;
  const explanationData = explanation.data?.explanation;

  const openObject = (key: string) => navigate(`/objects/${encodeURIComponent(key)}`);

  if (!selectedKey) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Asteroid profile"
          title="Acquire Object Telemetry"
          description="Search a scored object to open its technical risk profile, domain aggregate and graph neighborhood."
        />
        <ObjectSearch objects={objects.data?.objects} onSelect={openObject} />
        <EmptyState
          title="No object selected"
          description="Select from the ranking stream or enter an object_key/designation."
        />
      </div>
    );
  }

  if (object.isLoading) {
    return <LoadingState label="Loading object profile" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Asteroid profile"
        title={objectDisplayName(currentObject)}
        description={`Mission dossier for ${selectedKey}: risk score, explanation, domain model, latest simulation and graph neighbors.`}
        actions={<ObjectSearch objects={objects.data?.objects} onSelect={openObject} />}
      />

      {object.isError ? <ErrorState error={object.error} endpoint={`/objects/${selectedKey}`} /> : null}

      {!currentObject ? (
        <EmptyState title="Object not found" description={object.data?.message || "No scored row matched this key."} />
      ) : (
        <>
          <section className="grid gap-6 xl:grid-cols-[390px_minmax(0,1fr)]">
            <RiskScoreGauge score={currentObject.risk_score_0_100} category={currentObject.risk_category} />
            <div className="console-panel rounded-lg p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="technical-label text-xs text-cyan-100">Mission object header</p>
                  <h1 className="mt-2 text-3xl font-semibold text-white">{objectDisplayName(currentObject)}</h1>
                  <p className="mt-2 font-mono text-sm text-slate-400">{objectKey(currentObject)}</p>
                </div>
                <div className="text-right">
                  <p className="technical-label text-[10px] text-slate-500">score</p>
                  <p className="font-mono text-5xl text-white">{formatScore(currentObject.risk_score_0_100)}</p>
                </div>
              </div>
              <p className="mt-6 max-w-3xl text-base leading-7 text-slate-300">
                {explanationData?.short_explanation || currentObject.risk_explanation_short || "Risk explanation is not available yet."}
              </p>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_430px]">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Component Breakdown</CardTitle>
                  <CardDescription>Physical, orbital, approach, sentry, uncertainty and quality signals.</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <RiskComponentsRadar object={currentObject} />
              </CardContent>
            </Card>
            <ObjectSummaryCard object={currentObject} />
          </section>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>Risk Explanation</CardTitle>
                <CardDescription>Drivers, protective factors and limitations returned by `/risk/explain`.</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <RiskDriverList
                drivers={explanationData?.main_drivers}
                protective={explanationData?.protective_factors}
                limitations={explanationData?.data_limitations}
              />
              <p className="rounded-lg border border-cyan-300/12 bg-slate-950/45 p-4 text-sm leading-6 text-slate-300">
                {explanationData?.technical_explanation || "Technical explanation unavailable for this object."}
              </p>
            </CardContent>
          </Card>

          <section className="grid gap-6 xl:grid-cols-3">
            <div className="space-y-6 xl:col-span-2">
              <div className="grid gap-6 lg:grid-cols-2">
                <OrbitalElementsPanel object={currentObject} />
                <PhysicalPropertiesPanel object={currentObject} />
              </div>
              <SentrySignalPanel object={currentObject} />
            </div>
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Domain Object</CardTitle>
                  <CardDescription>Nested aggregate from `/domain/objects/{selectedKey}`.</CardDescription>
                </div>
                <Database className="h-5 w-5 text-cyan-100" />
              </CardHeader>
              <CardContent>
                <pre className="max-h-[420px] overflow-auto rounded-md border border-cyan-300/12 bg-black/35 p-3 font-mono text-xs leading-5 text-slate-300">
                  {JSON.stringify(domain.data?.object ?? { status: domain.data?.status, message: domain.data?.message }, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Latest Monte Carlo</CardTitle>
                  <CardDescription>Saved score-stability simulation if available.</CardDescription>
                </div>
                <Orbit className="h-5 w-5 text-cyan-100" />
              </CardHeader>
              <CardContent className="space-y-4">
                <SimulationSummary result={simulation.data?.result} />
                <MonteCarloHistogram result={simulation.data?.result} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>GNN Neighbors</CardTitle>
                  <CardDescription>Orbital graph neighbors with similarity score.</CardDescription>
                </div>
                <GitBranch className="h-5 w-5 text-cyan-100" />
              </CardHeader>
              <CardContent>
                <NeighborList neighbors={neighbors.data?.result?.neighbors} onOpenNeighbor={openObject} />
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
