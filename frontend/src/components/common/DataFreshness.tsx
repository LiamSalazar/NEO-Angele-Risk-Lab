import { Clock3 } from "lucide-react";

import { formatTimestamp } from "@/lib/formatters";

type DataFreshnessProps = {
  timestamp?: string | null;
  label?: string;
};

export function DataFreshness({ timestamp, label = "Last signal" }: DataFreshnessProps) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/15 bg-slate-950/50 px-3 py-1 text-xs text-slate-300">
      <Clock3 className="h-3.5 w-3.5 text-cyan-100" />
      {label}: <span className="font-mono text-slate-100">{formatTimestamp(timestamp)}</span>
    </span>
  );
}
