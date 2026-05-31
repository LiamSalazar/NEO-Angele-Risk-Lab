import { BookOpen, FlaskConical, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { RiskMethodologyPanel } from "@/components/risk/RiskMethodologyPanel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRiskMethodologyQuery } from "@/api/queries";

export function MethodologyPage() {
  const methodology = useRiskMethodologyQuery();
  const content = String(methodology.data?.details?.content ?? "");

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Methodology"
        title="Analytical Methodology"
        description="How the observatory turns persisted NASA/JPL-derived NEO data into rankings, findings, simulations, graph neighborhoods and supporting model evidence."
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <RiskMethodologyPanel content={content} />
        <Card>
          <CardHeader>
            <div>
            <CardTitle>Scope</CardTitle>
            <CardDescription>A concise boundary for interpretation.</CardDescription>
            </div>
            <ShieldAlert className="h-5 w-5 text-amber-100" />
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-slate-300">
            <p>Sources are NASA/JPL-oriented data products persisted by the backend pipelines.</p>
            <p>Risk Priority Score ranks analytical follow-up priority inside this project.</p>
            <p>Findings are dataset interpretations, not official impact alerts.</p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MethodCard title="NASA/JPL Sources" body="The backend ingests NEO object, close-approach and Sentry-related records, then analyzes persisted Bronze/Silver/Gold data products." icon={<BookOpen className="h-5 w-5" />} />
        <MethodCard title="Risk Priority Score" body="The score combines physical, orbital, approach, Sentry, uncertainty and data-quality signals into a review-priority ranking." icon={<ShieldAlert className="h-5 w-5" />} />
        <MethodCard title="Score Simulation" body="Score simulation perturbs score inputs to estimate score stability, category-shift probability and p95 score behavior." icon={<FlaskConical className="h-5 w-5" />} />
        <MethodCard title="Orbital Simulation" body="Orbital simulation perturbs available orbital elements and uses approximate two-body propagation to estimate distance bands." icon={<FlaskConical className="h-5 w-5" />} />
        <MethodCard title="Orbital Graph" body="The graph links orbitally similar objects so the app can inspect neighborhoods and compare graph evidence against tabular patterns." icon={<BookOpen className="h-5 w-5" />} />
        <MethodCard title="ML/GNN Evidence" body="Models are secondary evidence for pattern consistency. Definition-heavy feature sets are treated as leakage-sensitive diagnostics." icon={<ShieldAlert className="h-5 w-5" />} />
      </section>
    </div>
  );
}

function MethodCard({ title, body, icon }: { title: string; body: string; icon: ReactNode }) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-5">
      <div className="mb-3 flex items-center gap-2 text-cyan-100">{icon}</div>
      <h3 className="font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">{body}</p>
    </div>
  );
}
