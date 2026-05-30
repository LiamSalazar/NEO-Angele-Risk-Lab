import { Cpu, GitBranch, PackageX } from "lucide-react";
import type { ReactNode } from "react";

import type { GNNStatusResult } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { formatNumber } from "@/lib/formatters";

type GNNStatusPanelProps = {
  status?: string;
  result?: GNNStatusResult | null;
};

export function GNNStatusPanel({ status, result }: GNNStatusPanelProps) {
  const torchAvailable = Boolean(result?.torch_geometric_available);
  const dependencyState = torchAvailable ? "torch-geometric available" : "skipped_missing_dependency";

  return (
    <div className="console-panel rounded-lg p-5" data-testid="gnn-status-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="technical-label text-xs text-cyan-100">GNN research status</p>
          <h2 className="mt-2 text-xl font-semibold text-white">{status || "unknown"}</h2>
        </div>
        <Badge variant={torchAvailable ? "green" : "amber"}>{dependencyState}</Badge>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <Metric icon={<GitBranch className="h-4 w-4" />} label="nodes" value={formatNumber(result?.node_count, { maximumFractionDigits: 0 })} />
        <Metric icon={<GitBranch className="h-4 w-4" />} label="edges" value={formatNumber(result?.edge_count, { maximumFractionDigits: 0 })} />
        <Metric icon={<Cpu className="h-4 w-4" />} label="risk rows" value={formatNumber(result?.risk_scores_count, { maximumFractionDigits: 0 })} />
      </div>
      {!torchAvailable ? (
        <div className="mt-4 flex items-start gap-3 rounded-md border border-amber-300/20 bg-amber-300/8 p-3 text-sm text-amber-100">
          <PackageX className="mt-0.5 h-4 w-4 shrink-0" />
          GraphSAGE/GCN experiments are reported as skipped, not failed, when torch-geometric is absent.
        </div>
      ) : null}
    </div>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-cyan-300/12 bg-slate-950/45 p-3">
      <div className="flex items-center gap-2 text-cyan-100">{icon}</div>
      <p className="technical-label mt-2 text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-xl text-white">{value}</p>
    </div>
  );
}
