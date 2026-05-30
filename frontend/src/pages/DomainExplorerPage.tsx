import { ArrowRight, Braces, DatabaseZap } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { ObjectSearch } from "@/components/objects/ObjectSearch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDomainObjectQuery } from "@/hooks/useObjectProfile";
import { useObjectsQuery } from "@/hooks/useRiskRanking";
import { ENTITY_NAMES } from "@/lib/constants";
import { objectKey } from "@/lib/formatters";

export function DomainExplorerPage() {
  const objects = useObjectsQuery({ limit: 250 });
  const [selectedObjectKey, setSelectedObjectKey] = useState("");
  const firstKey = objects.data?.objects?.[0] ? objectKey(objects.data.objects[0]) : "";
  const activeKey = selectedObjectKey || firstKey;
  const domain = useDomainObjectQuery(activeKey);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Domain explorer"
        title="Object-Oriented Domain Model"
        description="A technical interview view of aggregate entities and how Gold rows become domain-rich objects, scores, simulations and graph nodes."
      />

      <section className="grid gap-6 xl:grid-cols-[430px_minmax(0,1fr)]">
        <div className="space-y-6">
          <ObjectSearch objects={objects.data?.objects} onSelect={setSelectedObjectKey} />
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Domain Entities</CardTitle>
                <CardDescription>Core POO classes represented by the backend.</CardDescription>
              </div>
              <DatabaseZap className="h-5 w-5 text-cyan-100" />
            </CardHeader>
            <CardContent className="grid gap-2">
              {ENTITY_NAMES.map((entity) => (
                <div key={entity} className="rounded-md border border-cyan-300/12 bg-slate-950/45 px-3 py-2 font-mono text-sm text-slate-100">
                  {entity}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Domain Object JSON</CardTitle>
              <CardDescription>Clean aggregate representation from `/domain/objects/{activeKey || "object_key"}`.</CardDescription>
            </div>
            <Braces className="h-5 w-5 text-cyan-100" />
          </CardHeader>
          <CardContent>
            {activeKey ? (
              <pre className="max-h-[650px] overflow-auto rounded-md border border-cyan-300/12 bg-black/35 p-4 font-mono text-xs leading-5 text-slate-300">
                {JSON.stringify(domain.data?.object ?? { status: domain.data?.status, message: domain.data?.message }, null, 2)}
              </pre>
            ) : (
              <EmptyState title="No domain object selected" description="Select a scored object to inspect the aggregate." />
            )}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Data-to-Domain Flow</CardTitle>
            <CardDescription>How a processed Gold row becomes a richer technical artifact.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr_auto_1fr]">
            {["gold row", "Asteroid", "RiskScore", "Simulation", "GNN"].map((item, index, array) => (
              <FlowSegment key={item} label={item} showArrow={index < array.length - 1} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function FlowSegment({ label, showArrow }: { label: string; showArrow: boolean }) {
  return (
    <>
      <div className="rounded-lg border border-cyan-300/15 bg-slate-950/45 p-4 text-center">
        <p className="technical-label text-[10px] text-cyan-100">{label}</p>
      </div>
      {showArrow ? (
        <div className="hidden place-items-center text-cyan-100 md:grid">
          <ArrowRight className="h-5 w-5" />
        </div>
      ) : null}
    </>
  );
}
