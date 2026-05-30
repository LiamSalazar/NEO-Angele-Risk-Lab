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
        title="Scope, Limits and Research Framing"
        description="Neo Angele Risk Lab is a technical/educational observatory. It does not replace NASA/JPL products or professional orbital risk assessment."
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <RiskMethodologyPanel content={content} />
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Official Context</CardTitle>
              <CardDescription>What this lab is and is not.</CardDescription>
            </div>
            <ShieldAlert className="h-5 w-5 text-amber-100" />
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-slate-300">
            <p>Sources are NASA/JPL-oriented data products consumed by the backend pipelines.</p>
            <p>Risk Priority Score is experimental and ranks follow-up priority inside this project.</p>
            <p>The frontend must never be read as an impact alert, official prediction or public safety tool.</p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MethodCard title="NASA/JPL Sources" body="The backend ingests and transforms NEO object, close-approach and Sentry-related records into Bronze/Silver/Gold layers." icon={<BookOpen className="h-5 w-5" />} />
        <MethodCard title="Monte Carlo" body="The simulation perturbs score inputs to estimate score stability. It is not orbital propagation and does not compute impact corridors." icon={<FlaskConical className="h-5 w-5" />} />
        <MethodCard title="Leakage Audit" body="Model results are interpreted with special care around H, MOID, diameter and target-definition-adjacent feature sets." icon={<ShieldAlert className="h-5 w-5" />} />
        <MethodCard title="GNN Experimental" body="Orbital graph and optional GNN experiments support research exploration. Missing torch-geometric is reported as skipped." icon={<FlaskConical className="h-5 w-5" />} />
        <MethodCard title="Educational Use" body="The application is built for technical portfolio review, data engineering demonstration and research literacy." icon={<BookOpen className="h-5 w-5" />} />
        <MethodCard title="Final Phase" body="Docker hardening, reproducibility, final README, demo and release polish remain intentionally out of this phase." icon={<ShieldAlert className="h-5 w-5" />} />
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
