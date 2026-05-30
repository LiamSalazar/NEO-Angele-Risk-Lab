import { SquareTerminal } from "lucide-react";

import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  command?: string;
  className?: string;
};

export function EmptyState({ title, description, command, className }: EmptyStateProps) {
  return (
    <div className={cn("rounded-lg border border-dashed border-cyan-300/20 bg-slate-950/35 p-5", className)}>
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-cyan-300/20 bg-cyan-300/8 text-cyan-100">
          <SquareTerminal className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-medium text-white">{title}</h3>
          {description ? <p className="mt-1 text-sm text-slate-400">{description}</p> : null}
          {command ? (
            <code className="mt-3 inline-block rounded-md border border-cyan-300/15 bg-black/35 px-2.5 py-1.5 font-mono text-xs text-cyan-100">
              {command}
            </code>
          ) : null}
        </div>
      </div>
    </div>
  );
}
