import { Satellite } from "lucide-react";

import { cn } from "@/lib/utils";

type LoadingStateProps = {
  label?: string;
  className?: string;
};

export function LoadingState({ label = "Acquiring telemetry", className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        "console-panel scanline flex min-h-40 items-center justify-center rounded-lg p-6",
        className
      )}
      role="status"
    >
      <div className="flex items-center gap-4">
        <div className="relative grid h-12 w-12 place-items-center rounded-full border border-cyan-300/30">
          <div className="absolute inset-1 rounded-full border border-cyan-300/20" />
          <Satellite className="h-5 w-5 text-cyan-100" />
          <span className="absolute inset-0 rounded-full border border-cyan-300/20 animate-ping" />
        </div>
        <div>
          <p className="technical-label text-xs text-cyan-100">{label}</p>
          <p className="mt-1 text-sm text-slate-400">Synchronizing local FastAPI signal.</p>
        </div>
      </div>
    </div>
  );
}
