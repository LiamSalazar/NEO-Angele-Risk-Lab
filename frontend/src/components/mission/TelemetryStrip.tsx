import { CheckCircle2, CircleDashed, FileText } from "lucide-react";

import { compactPath } from "@/lib/formatters";
import { cn } from "@/lib/utils";

type TelemetryItem = {
  label: string;
  value?: string | number | boolean | null;
  ok?: boolean;
  path?: string;
};

type TelemetryStripProps = {
  items: TelemetryItem[];
};

export function TelemetryStrip({ items }: TelemetryStripProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const positive = item.ok ?? Boolean(item.value);
        return (
          <div
            key={item.label}
            className="rounded-lg border border-cyan-300/12 bg-slate-950/45 p-3"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="technical-label text-[11px] text-slate-500">{item.label}</p>
              {item.path ? (
                <FileText className="h-4 w-4 text-cyan-100" />
              ) : positive ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-200" />
              ) : (
                <CircleDashed className="h-4 w-4 text-slate-500" />
              )}
            </div>
            <p
              className={cn(
                "mt-2 truncate font-mono text-sm",
                positive ? "text-slate-100" : "text-slate-500"
              )}
              title={item.path || String(item.value ?? "unavailable")}
            >
              {item.path ? compactPath(item.path) : String(item.value ?? "unavailable")}
            </p>
          </div>
        );
      })}
    </div>
  );
}
