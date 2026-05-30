import { Radar } from "lucide-react";

import { formatScore } from "@/lib/formatters";

type RiskRadarProps = {
  topScore?: number | null;
  objectCount?: number | null;
};

export function RiskRadar({ topScore, objectCount }: RiskRadarProps) {
  return (
    <div className="relative min-h-[320px] overflow-hidden rounded-lg border border-cyan-300/14 bg-slate-950/45 p-6">
      <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/15" />
      <div className="absolute left-1/2 top-1/2 h-52 w-52 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/10" />
      <div className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-300/10" />
      <div className="absolute left-1/2 top-1/2 h-72 w-px -translate-x-1/2 -translate-y-1/2 bg-cyan-300/14" />
      <div className="absolute left-1/2 top-1/2 h-px w-72 -translate-x-1/2 -translate-y-1/2 bg-cyan-300/14" />
      <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full">
        <div className="h-1/2 w-1/2 origin-bottom-right border-r border-cyan-300/50 bg-gradient-to-tr from-cyan-300/0 via-cyan-300/10 to-cyan-300/22 animate-sweep" />
      </div>
      <div className="relative z-10 flex h-full min-h-[270px] flex-col justify-between">
        <div>
          <p className="technical-label text-xs text-cyan-100">Orbital priority radar</p>
          <p className="mt-2 max-w-xs text-sm text-slate-400">
            Top-scored NEOs and dataset readiness are projected into a lightweight mission-control
            view.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-cyan-300/14 bg-black/30 p-3">
            <p className="technical-label text-[10px] text-slate-500">Top score</p>
            <p className="mt-1 font-mono text-2xl text-white">{formatScore(topScore)}</p>
          </div>
          <div className="rounded-lg border border-cyan-300/14 bg-black/30 p-3">
            <p className="technical-label text-[10px] text-slate-500">Objects tracked</p>
            <p className="mt-1 font-mono text-2xl text-white">{objectCount ?? "n/a"}</p>
          </div>
        </div>
      </div>
      <Radar className="absolute right-5 top-5 h-5 w-5 text-cyan-100/70" />
    </div>
  );
}
